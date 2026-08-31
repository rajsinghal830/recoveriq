"""
tools/audit_tools.py

SQLite-based audit trail for RecoverIQ.

Stores:
- Recovery runs
- Agent decisions
- Actions taken
- Priority scores
- Policy decisions

The database is designed to survive repeated application runs.
"""

import logging
import sqlite3
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


# ============================================================================
# DATABASE PATH
# ============================================================================

try:
    from config import AUDIT_DB_PATH
except ImportError:
    AUDIT_DB_PATH = "recoveriq_audit.db"


# ============================================================================
# CONNECTION
# ============================================================================

def _conn():
    """
    Create a SQLite connection.

    check_same_thread=False helps when Streamlit and other
    components access the database during the same application.
    """

    return sqlite3.connect(
        AUDIT_DB_PATH,
        check_same_thread=False,
    )


# ============================================================================
# INITIALIZE DATABASE
# ============================================================================

def init_db():
    """
    Create all RecoverIQ audit tables if they don't exist.

    Also upgrades an older database by adding the new
    priority/policy columns when necessary.
    """

    with _conn() as con:

        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS recovery_runs (
                id                  TEXT PRIMARY KEY,
                payment_id          TEXT,
                customer_name       TEXT,
                amount              REAL,
                failure_reason      TEXT,
                started_at          TEXT,
                completed_at        TEXT,
                outcome             TEXT DEFAULT 'PENDING',
                amount_recovered    REAL DEFAULT 0.0,

                priority_score      REAL DEFAULT 0.0,
                priority            TEXT DEFAULT 'LOW',
                policy_allowed      INTEGER DEFAULT 1,
                policy_action       TEXT DEFAULT '',
                policy_reason       TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS agent_decisions (
                id              TEXT PRIMARY KEY,
                run_id          TEXT,
                agent_name      TEXT,
                input_summary   TEXT,
                decision        TEXT,
                reasoning       TEXT,
                timestamp       TEXT
            );

            CREATE TABLE IF NOT EXISTS actions_taken (
                id              TEXT PRIMARY KEY,
                run_id          TEXT,
                action_type     TEXT,
                details         TEXT,
                result          TEXT,
                timestamp       TEXT
            );
            """
        )

        # --------------------------------------------------------------------
        # Upgrade existing databases
        # --------------------------------------------------------------------

        existing_columns = {
            row[1]
            for row in con.execute(
                "PRAGMA table_info(recovery_runs)"
            ).fetchall()
        }

        new_columns = {
            "priority_score": (
                "REAL DEFAULT 0.0"
            ),
            "priority": (
                "TEXT DEFAULT 'LOW'"
            ),
            "policy_allowed": (
                "INTEGER DEFAULT 1"
            ),
            "policy_action": (
                "TEXT DEFAULT ''"
            ),
            "policy_reason": (
                "TEXT DEFAULT ''"
            ),
        }

        for column, definition in new_columns.items():

            if column not in existing_columns:

                con.execute(
                    f"""
                    ALTER TABLE recovery_runs
                    ADD COLUMN {column} {definition}
                    """
                )

    logger.info(
        "Audit database initialized at %s",
        AUDIT_DB_PATH,
    )


# ============================================================================
# LOG RUN START
# ============================================================================

def log_run_start(
    payment_id,
    customer_name,
    amount,
    failure_reason,
):
    """
    Create a new recovery run and return its run ID.
    """

    run_id = str(uuid.uuid4())

    with _conn() as con:

        con.execute(
            """
            INSERT INTO recovery_runs
            (
                id,
                payment_id,
                customer_name,
                amount,
                failure_reason,
                started_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                payment_id,
                customer_name,
                amount,
                failure_reason,
                datetime.now().isoformat(),
            ),
        )

    return run_id


# ============================================================================
# LOG PRIORITY + POLICY
# ============================================================================

def log_policy_decision(
    run_id,
    priority_score,
    priority,
    policy_allowed,
    policy_action,
    policy_reason,
):
    """
    Store the policy engine's decision for a recovery run.
    """

    with _conn() as con:

        con.execute(
            """
            UPDATE recovery_runs
            SET
                priority_score=?,
                priority=?,
                policy_allowed=?,
                policy_action=?,
                policy_reason=?
            WHERE id=?
            """,
            (
                float(priority_score),
                str(priority),
                1 if policy_allowed else 0,
                str(policy_action),
                str(policy_reason),
                run_id,
            ),
        )


# ============================================================================
# LOG AGENT DECISION
# ============================================================================

def log_decision(
    run_id,
    agent_name,
    input_summary,
    decision,
    reasoning,
):
    """
    Log an individual agent decision.
    """

    with _conn() as con:

        con.execute(
            """
            INSERT INTO agent_decisions
            (
                id,
                run_id,
                agent_name,
                input_summary,
                decision,
                reasoning,
                timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                run_id,
                agent_name,
                str(input_summary),
                str(decision),
                str(reasoning),
                datetime.now().isoformat(),
            ),
        )


# ============================================================================
# LOG ACTION
# ============================================================================

def log_action(
    run_id,
    action_type,
    details,
    result,
):
    """
    Log an executed recovery action.
    """

    with _conn() as con:

        con.execute(
            """
            INSERT INTO actions_taken
            (
                id,
                run_id,
                action_type,
                details,
                result,
                timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                run_id,
                action_type,
                str(details),
                str(result),
                datetime.now().isoformat(),
            ),
        )


# ============================================================================
# COMPLETE RUN
# ============================================================================

def log_run_complete(
    run_id,
    outcome,
    amount_recovered=0.0,
):
    """
    Mark a recovery run as complete.
    """

    with _conn() as con:

        con.execute(
            """
            UPDATE recovery_runs
            SET
                outcome=?,
                amount_recovered=?,
                completed_at=?
            WHERE id=?
            """,
            (
                str(outcome),
                float(amount_recovered or 0.0),
                datetime.now().isoformat(),
                run_id,
            ),
        )


# ============================================================================
# GET ALL RUNS
# ============================================================================

def get_all_runs():
    """
    Return all recovery runs as dictionaries.
    """

    with _conn() as con:

        con.row_factory = sqlite3.Row

        rows = con.execute(
            """
            SELECT *
            FROM recovery_runs
            ORDER BY started_at DESC
            """
        ).fetchall()

    return [
        dict(row)
        for row in rows
    ]


# ============================================================================
# GET SUMMARY
# ============================================================================

def get_summary_stats():
    """
    Return high-level recovery statistics.
    """

    runs = get_all_runs()

    if not runs:

        return {
            "total_failed": 0,
            "total_recovered": 0,
            "recovery_rate": 0.0,
            "total_amount_recovered": 0.0,
        }

    total = len(runs)

    recovered = sum(
        1
        for run in runs
        if str(
            run.get("outcome", "")
        ).upper() == "RECOVERED"
    )

    amount = sum(
        float(
            run.get(
                "amount_recovered",
                0,
            )
            or 0
        )
        for run in runs
    )

    return {
        "total_failed": total,
        "total_recovered": recovered,
        "recovery_rate": round(
            recovered / total * 100,
            1,
        ),
        "total_amount_recovered": round(
            amount,
            2,
        ),
    }