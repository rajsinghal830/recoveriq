"""
tools/audit_tools.py — SQLite-based audit trail for RecoverIQ.
Every agent decision and action is persisted here.
"""
import sqlite3, uuid, logging
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from config import AUDIT_DB_PATH
except ImportError:
    AUDIT_DB_PATH = "recoveriq_audit.db"


def _conn():
    return sqlite3.connect(AUDIT_DB_PATH)


def init_db():
    """Create audit tables if they do not exist."""
    with _conn() as con:
        con.executescript("""
            CREATE TABLE IF NOT EXISTS recovery_runs (
                id              TEXT PRIMARY KEY,
                payment_id      TEXT,
                customer_name   TEXT,
                amount          REAL,
                failure_reason  TEXT,
                started_at      TEXT,
                completed_at    TEXT,
                outcome         TEXT DEFAULT 'PENDING',
                amount_recovered REAL DEFAULT 0.0
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
        """)
    logger.debug("Audit DB initialised at %s", AUDIT_DB_PATH)


def log_run_start(payment_id, customer_name, amount, failure_reason):
    """Insert a new recovery run record and return its run_id."""
    run_id = str(uuid.uuid4())
    with _conn() as con:
        con.execute(
            "INSERT INTO recovery_runs (id, payment_id, customer_name, amount, failure_reason, started_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (run_id, payment_id, customer_name, amount, failure_reason, datetime.now().isoformat()),
        )
    return run_id


def log_decision(run_id, agent_name, input_summary, decision, reasoning):
    """Log an agent decision."""
    with _conn() as con:
        con.execute(
            "INSERT INTO agent_decisions (id, run_id, agent_name, input_summary, decision, reasoning, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), run_id, agent_name, input_summary, decision, reasoning, datetime.now().isoformat()),
        )


def log_action(run_id, action_type, details, result):
    """Log an executed action."""
    with _conn() as con:
        con.execute(
            "INSERT INTO actions_taken (id, run_id, action_type, details, result, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), run_id, action_type, str(details), str(result), datetime.now().isoformat()),
        )


def log_run_complete(run_id, outcome, amount_recovered=0.0):
    """Mark a recovery run as complete."""
    with _conn() as con:
        con.execute(
            "UPDATE recovery_runs SET outcome=?, amount_recovered=?, completed_at=? WHERE id=?",
            (outcome, amount_recovered, datetime.now().isoformat(), run_id),
        )


def get_all_runs():
    """Return all recovery runs as a list of dicts."""
    with _conn() as con:
        con.row_factory = sqlite3.Row
        rows = con.execute("SELECT * FROM recovery_runs ORDER BY started_at DESC").fetchall()
    return [dict(r) for r in rows]


def get_summary_stats():
    """Return high-level stats dict."""
    runs = get_all_runs()
    if not runs:
        return {"total_failed": 0, "total_recovered": 0, "recovery_rate": 0.0, "total_amount_recovered": 0.0}
    total = len(runs)
    recovered = sum(1 for r in runs if r["outcome"] == "RECOVERED")
    amount = sum(r["amount_recovered"] or 0 for r in runs)
    return {
        "total_failed": total,
        "total_recovered": recovered,
        "recovery_rate": round(recovered / total * 100, 1),
        "total_amount_recovered": round(amount, 2),
    }
