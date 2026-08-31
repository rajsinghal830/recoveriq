"""
RecoverIQ main orchestration pipeline.

Flow:

Payment Failure
      ↓
Detector
      ↓
Priority Score + Policy
      ↓
Strategist
      ↓
Executor
      ↓
Audit

The policy engine provides a deterministic safety boundary
before the recovery strategy is executed.
"""

import argparse
import json
import logging
import sqlite3
import sys
from pathlib import Path

# ============================================================================
# RICH
# ============================================================================

try:
    from rich.console import Console
    from rich.progress import (
        Progress,
        SpinnerColumn,
        BarColumn,
        TextColumn,
        TimeElapsedColumn,
    )
    from rich.table import Table

    HAS_RICH = True

except ImportError:
    HAS_RICH = False


console = Console() if HAS_RICH else None


# ============================================================================
# LOGGING
# ============================================================================

logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger("orchestrator")


# ============================================================================
# PROJECT PATH
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================================
# LOCAL IMPORTS
# ============================================================================

from tools.audit_tools import (
    init_db,
    log_run_start,
    log_run_complete,
    log_policy_decision,
    get_summary_stats,
)

from agents.detector import DetectorAgent
from agents.strategist import StrategistAgent
from agents.executor import ExecutorAgent

from agents.policy import evaluate_policy


# ============================================================================
# OUTCOME COLORS
# ============================================================================

OUTCOME_COLORS = {
    "RECOVERED": "green",
    "FAILED": "red",
    "PENDING": "yellow",
    "ESCALATED": "magenta",
}


# ============================================================================
# LOAD EVENTS
# ============================================================================

def load_events(
    path="data/mock_failures.json",
    count=None,
    failure_type=None,
):
    """Load payment failure events from JSON."""

    file_path = PROJECT_ROOT / path

    with open(file_path, encoding="utf-8") as file:
        events = json.load(file)

    if failure_type:
        failure_type = failure_type.upper()

        events = [
            event
            for event in events
            if str(
                event.get("failure_reason", "")
            ).upper() == failure_type
        ]

    if count is not None:
        events = events[:count]

    return events


# ============================================================================
# EXISTING PAYMENT IDS
# ============================================================================

def get_existing_payment_ids():
    """
    Return payment IDs already processed.

    This prevents the same demo payment from being
    inserted into the audit database multiple times.
    """

    try:

        from config import AUDIT_DB_PATH

        db_path = PROJECT_ROOT / AUDIT_DB_PATH

        if not db_path.exists():
            return set()

        with sqlite3.connect(db_path) as con:

            cursor = con.execute(
                """
                SELECT DISTINCT payment_id
                FROM recovery_runs
                WHERE payment_id IS NOT NULL
                """
            )

            return {
                row[0]
                for row in cursor.fetchall()
                if row[0]
            }

    except Exception as exc:

        logger.warning(
            "Could not read existing payment IDs: %s",
            exc,
        )

        return set()


# ============================================================================
# RUN PIPELINE
# ============================================================================

def run_pipeline(events):

    init_db()

    detector = DetectorAgent()
    strategist = StrategistAgent()
    executor = ExecutorAgent()

    results = []

    existing_payment_ids = get_existing_payment_ids()

    # ------------------------------------------------------------------------
    # Avoid duplicate demo processing
    # ------------------------------------------------------------------------

    new_events = [
        event
        for event in events
        if event.get("id") not in existing_payment_ids
    ]

    skipped_count = (
        len(events) - len(new_events)
    )

    if skipped_count:

        print(
            f"Skipped {skipped_count} already "
            f"processed payment(s).\n"
        )

    if not new_events:

        print(
            "All selected payment events have "
            "already been processed.\n"
        )

        return results

    # =========================================================================
    # RICH PROGRESS
    # =========================================================================

    if HAS_RICH:

        with Progress(
            SpinnerColumn(),
            TextColumn(
                "[progress.description]{task.description}"
            ),
            BarColumn(),
            TextColumn(
                "{task.completed}/{task.total}"
            ),
            TimeElapsedColumn(),
            console=console,
        ) as progress:

            task = progress.add_task(
                "[cyan]Processing payments...",
                total=len(new_events),
            )

            for event in new_events:

                result = _process_one(
                    event,
                    detector,
                    strategist,
                    executor,
                )

                results.append(result)

                outcome = result.get(
                    "outcome",
                    "PENDING",
                )

                color = OUTCOME_COLORS.get(
                    outcome,
                    "white",
                )

                amount = (
                    float(
                        event.get("amount", 0)
                    )
                    / 100.0
                )

                progress.console.print(
                    f"  [{color}]"
                    f"{outcome:10}"
                    f"[/{color}] "
                    f"{event.get('id', 'N/A'):10} "
                    f"{event.get('failure_reason', 'UNKNOWN'):22} "
                    f"₹{amount:>8.2f}"
                )

                progress.advance(task)

    # =========================================================================
    # STANDARD CONSOLE
    # =========================================================================

    else:

        for index, event in enumerate(
            new_events,
            1,
        ):

            result = _process_one(
                event,
                detector,
                strategist,
                executor,
            )

            results.append(result)

            print(
                f"[{index:3}/{len(new_events)}] "
                f"{result.get('outcome', 'PENDING'):10} | "
                f"{event.get('id', 'N/A')} | "
                f"{event.get('failure_reason', 'UNKNOWN')}"
            )

    return results


# ============================================================================
# PROCESS ONE PAYMENT
# ============================================================================

def _process_one(
    event,
    detector,
    strategist,
    executor,
):

    payment_id = event.get(
        "id",
        "unknown",
    )

    customer_name = event.get(
        "customer_name",
        "Unknown",
    )

    amount = (
        float(
            event.get("amount", 0)
        )
        / 100.0
    )

    failure_reason = event.get(
        "failure_reason",
        "UNKNOWN",
    )

    # =========================================================================
    # CREATE AUDIT RUN
    # =========================================================================

    run_id = log_run_start(
        payment_id,
        customer_name,
        amount,
        failure_reason,
    )

    try:

        # =====================================================================
        # 1. DETECT + DIAGNOSE
        # =====================================================================

        diagnosis = detector.run(event)

        # =====================================================================
        # 2. PRIORITY + POLICY
        # =====================================================================

        policy = evaluate_policy(
            event,
            diagnosis,
        )
        log_policy_decision(
            run_id,
            policy.priority_score,
            policy.priority,
            policy.allowed,
            policy.action,
            policy.reason,
        )

        # Add policy information to diagnosis
        # so the strategist and executor can see it.

        diagnosis["priority_score"] = (
            policy.priority_score
        )

        diagnosis["priority"] = (
            policy.priority
        )

        diagnosis["recoverability"] = (
            policy.recoverability
        )

        diagnosis["policy_allowed"] = (
            policy.allowed
        )

        diagnosis["policy_action"] = (
            policy.action
        )

        diagnosis["policy_reason"] = (
            policy.reason
        )

        # =====================================================================
        # 3. POLICY BLOCK
        # =====================================================================

        if not policy.allowed:

            logger.warning(
                "Policy blocked payment %s: %s",
                payment_id,
                policy.reason,
            )

            result = {
                "outcome": (
                    "ESCALATED"
                    if policy.action == "ESCALATE"
                    else "FAILED"
                ),
                "actions_executed": [],
                "amount_recovered": 0.0,
                "recovery_method": "policy_block",
                "priority_score": policy.priority_score,
                "priority": policy.priority,
                "policy_allowed": False,
                "policy_action": policy.action,
                "policy_reason": policy.reason,
            }

            log_run_complete(
                run_id,
                result["outcome"],
                0.0,
            )

            return result

        # =====================================================================
        # 4. STRATEGIST
        # =====================================================================

        plan = strategist.run(
            diagnosis,
            event,
        )

        # Attach policy metadata to the plan

        plan["priority_score"] = (
            policy.priority_score
        )

        plan["priority"] = (
            policy.priority
        )

        plan["policy_allowed"] = (
            policy.allowed
        )

        plan["policy_reason"] = (
            policy.reason
        )

        # =====================================================================
        # 5. EXECUTOR
        # =====================================================================

        result = executor.run(
            plan,
            event,
            run_id,
        )

        # Add policy information to result

        result["priority_score"] = (
            policy.priority_score
        )

        result["priority"] = (
            policy.priority
        )

        result["policy_allowed"] = (
            policy.allowed
        )

        result["policy_action"] = (
            policy.action
        )

        result["policy_reason"] = (
            policy.reason
        )

        # =====================================================================
        # 6. COMPLETE AUDIT
        # =====================================================================

        log_run_complete(
            run_id,
            result.get(
                "outcome",
                "PENDING",
            ),
            float(
                result.get(
                    "amount_recovered",
                    0.0,
                )
                or 0.0
            ),
        )

        return result

    except Exception as exc:

        logger.exception(
            "Payment processing failed for %s",
            payment_id,
        )

        log_run_complete(
            run_id,
            "FAILED",
            0.0,
        )

        return {
            "outcome": "FAILED",
            "actions_executed": [],
            "amount_recovered": 0.0,
            "recovery_method": "error",
            "error": str(exc),
        }


# ============================================================================
# SUMMARY
# ============================================================================

def print_summary(results):

    stats = get_summary_stats()

    if HAS_RICH:

        table = Table(
            title="RecoverIQ — Recovery Summary",
            show_header=True,
            header_style="bold cyan",
        )

        table.add_column(
            "Metric",
            style="bold",
        )

        table.add_column(
            "Value",
            justify="right",
        )

        table.add_row(
            "Total Processed",
            str(
                stats["total_failed"]
            ),
        )

        table.add_row(
            "Recovered",
            (
                f"[green]"
                f"{stats['total_recovered']}"
                f"[/green]"
            ),
        )

        table.add_row(
            "Recovery Rate",
            f"{stats['recovery_rate']}%",
        )

        table.add_row(
            "Amount Recovered",
            (
                f"₹"
                f"{stats['total_amount_recovered']:,.2f}"
            ),
        )

        console.print(table)

        console.print(
            "\n[bold green]"
            "Run [dim]"
            "python -m streamlit run dashboard/app.py"
            "[/dim] to view the dashboard"
            "[/bold green]"
        )

    else:

        print("\n" + "=" * 55)

        print(
            f"Total Processed  : "
            f"{stats['total_failed']}"
        )

        print(
            f"Recovered        : "
            f"{stats['total_recovered']}"
        )

        print(
            f"Recovery Rate    : "
            f"{stats['recovery_rate']}%"
        )

        print(
            f"Amount Recovered : "
            f"₹{stats['total_amount_recovered']:,.2f}"
        )

        print("=" * 55)

        print(
            "\nRun:"
        )

        print(
            "python -m streamlit run dashboard/app.py"
        )


# ============================================================================
# RESET DATABASE
# ============================================================================

def reset_database():

    from config import AUDIT_DB_PATH

    db_path = PROJECT_ROOT / AUDIT_DB_PATH

    if not db_path.exists():

        print(
            "Database does not exist. "
            "Nothing to reset."
        )

        return

    with sqlite3.connect(db_path) as con:

        con.execute(
            "DELETE FROM actions_taken"
        )

        con.execute(
            "DELETE FROM agent_decisions"
        )

        con.execute(
            "DELETE FROM recovery_runs"
        )

    print(
        "✅ Audit database reset successfully."
    )


# ============================================================================
# MAIN
# ============================================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "RecoverIQ — AI Revenue Recovery Agent"
        )
    )

    parser.add_argument(
        "--count",
        type=int,
        default=None,
        help="Process first N events",
    )

    parser.add_argument(
        "--failure-type",
        type=str,
        default=None,
        help=(
            "Filter by failure reason, "
            "e.g. CARD_EXPIRED"
        ),
    )

    parser.add_argument(
        "--reset",
        action="store_true",
        help="Clear audit database before running",
    )

    args = parser.parse_args()

    # =========================================================================
    # RESET
    # =========================================================================

    if args.reset:
        reset_database()

    # =========================================================================
    # HEADER
    # =========================================================================

    if HAS_RICH:

        console.print(
            "\n[bold yellow]"
            "💰 RecoverIQ"
            "[/bold yellow] "
            "— AI Revenue Recovery Agent\n"
        )

    else:

        print(
            "\n💰 RecoverIQ — "
            "AI Revenue Recovery Agent\n"
        )

    # =========================================================================
    # LOAD EVENTS
    # =========================================================================

    events = load_events(
        count=args.count,
        failure_type=args.failure_type,
    )

    print(
        f"Loaded {len(events)} failure events\n"
    )

    # =========================================================================
    # PIPELINE
    # =========================================================================

    results = run_pipeline(events)

    # =========================================================================
    # SUMMARY
    # =========================================================================

    print_summary(results)


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()