"""
webhook_simulator.py â€” Simulates Razorpay webhook failure events.
Usage:
    python webhook_simulator.py                   # all 100 events
    python webhook_simulator.py --single          # 1 random event
    python webhook_simulator.py --count 10        # first 10 events
    python webhook_simulator.py --failure-type CARD_EXPIRED
"""
import json, random, argparse, sys, os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    from rich.console import Console
    from rich.json import JSON as RichJSON
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

import orchestrator


def load_events(path="data/mock_failures.json"):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def simulate_webhook(event):
    webhook_payload = {
        "entity": "event",
        "event": "payment.failed",
        "payload": {"payment": {"entity": event}},
    }
    if HAS_RICH:
        console.rule(f"[yellow]Webhook: {event['id']}[/yellow]")
        console.print(RichJSON(json.dumps(event, indent=2, ensure_ascii=False)))
    else:
        print(f"\n--- Webhook: {event['id']} ---")
        print(json.dumps(event, indent=2, ensure_ascii=False))
    return webhook_payload


def main():
    parser = argparse.ArgumentParser(description="RecoverIQ Webhook Simulator")
    parser.add_argument("--single",       action="store_true", help="Process one random event")
    parser.add_argument("--count",        type=int, default=None)
    parser.add_argument("--failure-type", type=str, default=None)
    args = parser.parse_args()

    events = load_events()

    if args.failure_type:
        events = [e for e in events if e["failure_reason"] == args.failure_type.upper()]
    if args.single:
        events = [random.choice(events)]
    elif args.count:
        events = events[:args.count]

    for event in events:
        simulate_webhook(event)

    print(f"\nFiring RecoverIQ pipeline for {len(events)} event(s)...\n")
    orchestrator.init_db = __import__("tools.audit_tools", fromlist=["init_db"]).init_db
    results = orchestrator.run_pipeline(events)
    orchestrator.print_summary(results)


if __name__ == "__main__":
    main()
