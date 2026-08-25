"""
orchestrator.py â€” RecoverIQ main pipeline.
Loads 100 mock failed payments, runs all 3 agents per event, writes audit trail.

Usage:
    python orchestrator.py
    python orchestrator.py --count 10
    python orchestrator.py --failure-type CARD_EXPIRED
"""
import json, logging, argparse, sys, os
from pathlib import Path

# â”€â”€ Rich for pretty console output â”€â”€
try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
    from rich.table import Table
    from rich import print as rprint
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

console = Console() if HAS_RICH else None

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("orchestrator")

# â”€â”€ Local imports â”€â”€
sys.path.insert(0, str(Path(__file__).parent))
from tools.audit_tools import init_db, log_run_start, log_run_complete, get_summary_stats
from agents.detector import DetectorAgent
from agents.strategist import StrategistAgent
from agents.executor import ExecutorAgent


_OUTCOME_COLORS = {
    "RECOVERED": "green",
    "FAILED":    "red",
    "PENDING":   "yellow",
    "ESCALATED": "magenta",
}


def load_events(path="data/mock_failures.json", count=None, failure_type=None):
    with open(path, encoding="utf-8") as f:
        events = json.load(f)
    if failure_type:
        events = [e for e in events if e["failure_reason"] == failure_type.upper()]
    if count:
        events = events[:count]
    return events


def run_pipeline(events):
    init_db()
    detector   = DetectorAgent()
    strategist = StrategistAgent()
    executor   = ExecutorAgent()

    results = []

    if HAS_RICH:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Processing paymentsâ€¦", total=len(events))
            for event in events:
                result = _process_one(event, detector, strategist, executor)
                results.append(result)
                color = _OUTCOME_COLORS.get(result["outcome"], "white")
                progress.console.print(
                    f"  [{color}]{result['outcome']:10}[/{color}] "
                    f"{event['id']:10} {event['failure_reason']:22} "
                    f"â‚¹{event['amount']/100:>8.2f}"
                )
                progress.advance(task)
    else:
        for i, event in enumerate(events, 1):
            result = _process_one(event, detector, strategist, executor)
            results.append(result)
            print(f"[{i:3}/{len(events)}] {result['outcome']:10} | {event['id']} | {event['failure_reason']}")

    return results


def _process_one(event, detector, strategist, executor):
    run_id = log_run_start(
        event["id"],
        event["customer_name"],
        event["amount"] / 100.0,
        event["failure_reason"],
    )
    diagnosis = detector.run(event)
    plan      = strategist.run(diagnosis, event)
    result    = executor.run(plan, event, run_id)
    log_run_complete(run_id, result["outcome"], result["amount_recovered"])
    return result


def print_summary(results):
    stats = get_summary_stats()
    if HAS_RICH:
        table = Table(title="RecoverIQ â€” Recovery Summary", show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="bold")
        table.add_column("Value", justify="right")
        table.add_row("Total Processed",     str(stats["total_failed"]))
        table.add_row("[green]Recovered",     f"[green]{stats['total_recovered']}")
        table.add_row("Recovery Rate",        f"{stats['recovery_rate']}%")
        table.add_row("[cyan]Amount Recovered", f"[cyan]â‚¹{stats['total_amount_recovered']:,.2f}")
        console.print(table)
        console.print("[bold green]\nâœ… Run  [dim]streamlit run dashboard/app.py[/dim]  to view the dashboard[/bold green]")
    else:
        print("\n" + "="*50)
        print(f"Total Processed : {stats['total_failed']}")
        print(f"Recovered       : {stats['total_recovered']}")
        print(f"Recovery Rate   : {stats['recovery_rate']}%")
        print(f"Amount Recovered: Rs.{stats['total_amount_recovered']:,.2f}")
        print("="*50)
        print("Run: streamlit run dashboard/app.py")


def main():
    parser = argparse.ArgumentParser(description="RecoverIQ â€” AI Revenue Recovery Agent")
    parser.add_argument("--count",        type=int,  default=None, help="Process first N events")
    parser.add_argument("--failure-type", type=str,  default=None, help="Filter by failure reason")
    args = parser.parse_args()

    if HAS_RICH:
        console.print("\n[bold yellow]ðŸ’° RecoverIQ[/bold yellow] â€” AI Revenue Recovery Agent\n")

    events = load_events(count=args.count, failure_type=args.failure_type)
    print(f"Loaded {len(events)} failure events\n")

    results = run_pipeline(events)
    print_summary(results)


if __name__ == "__main__":
    main()
