"""
tools/audit_tools.py
SQLite-based audit trail for RecoverIQ.
Every agent decision and action is persisted here.
"""

import sqlite3
import uuid
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from config import AUDIT_DB_PATH
except ImportError:
    AUDIT_DB_PATH = "recoveriq_audit.db"


# ---------------------------------------------------------------------------
# Database path
# ---------------------------------------------------------------------------

DB_PATH = Path(AUDIT_DB_PATH)

# Create parent directory if one is specified
if DB_PATH.parent != Path("."):
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

def _conn():
    """Create a SQLite database connection."""
    con = sqlite3.connect(str(DB_PATH))
    return con


# ---------------------------------------------------------------------------
# Initialize database
# ---------------------------------------------------------------------------

def init_db():
    """Create all audit tables if they do not already exist."""

    with _conn() as con:

        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS recovery_runs (
                id TEXT PRIMARY KEY,
                payment_id TEXT,
                customer_name TEXT,
                amount REAL,
                failure_reason TEXT,
                started_at TEXT,
                completed_at TEXT,
                outcome TEXT DEFAULT 'PENDING',
                amount_recovered REAL DEFAULT 0.0
            );

            CREATE TABLE IF NOT EXISTS agent_decisions (
                id TEXT PRIMARY KEY,
                run_id TEXT,
                agent_name TEXT,
                input_summary TEXT,
                decision TEXT,
                reasoning TEXT,
                timestamp TEXT
            );

            CREATE TABLE IF NOT EXISTS actions_taken (
                id TEXT PRIMARY KEY,
                run_id TEXT,
                action_type TEXT,
                details TEXT,
                result TEXT,
                timestamp TEXT
            );
            """
        )

        con.commit()

    logger.info("Audit DB initialized at %s", DB_PATH)


# ---------------------------------------------------------------------------
# Recovery run
# ---------------------------------------------------------------------------

def log_run_start(
    payment_id,
    customer_name,
    amount,
    failure_reason
):
    """Insert a new recovery run and return its run ID."""

    # Make sure tables exist
    init_db()

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
                started_at,
                outcome,
                amount_recovered
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                payment_id,
                customer_name,
                amount,
                failure_reason,
                datetime.now().isoformat(),
                "PENDING",
                0.0,
            ),
        )

        con.commit()

    return run_id


# ---------------------------------------------------------------------------
# Agent decisions
# ---------------------------------------------------------------------------

def log_decision(
    run_id,
    agent_name,
    input_summary,
    decision,
    reasoning
):
    """Log an agent decision."""

    init_db()

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

        con.commit()


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------

def log_action(
    run_id,
    action_type,
    details,
    result
):
    """Log an executed action."""

    init_db()

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

        con.commit()


# ---------------------------------------------------------------------------
# Complete recovery run
# ---------------------------------------------------------------------------

def log_run_complete(
    run_id,
    outcome,
    amount_recovered=0.0
):
    """Mark a recovery run as complete."""

    init_db()

    with _conn() as con:

        con.execute(
            """
            UPDATE recovery_runs
            SET
                outcome = ?,
                amount_recovered = ?,
                completed_at = ?
            WHERE id = ?
            """,
            (
                outcome,
                amount_recovered,
                datetime.now().isoformat(),
                run_id,
            ),
        )

        con.commit()


# ---------------------------------------------------------------------------
# Get all runs
# ---------------------------------------------------------------------------

def get_all_runs():
    """Return all recovery runs as a list of dictionaries."""

    init_db()

    with _conn() as con:

        con.row_factory = sqlite3.Row

        rows = con.execute(
            """
            SELECT *
            FROM recovery_runs
            ORDER BY started_at DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# Summary statistics
# ---------------------------------------------------------------------------

def get_summary_stats():
    """Return high-level recovery statistics."""

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
        if run.get("outcome") == "RECOVERED"
    )

    amount = sum(
        float(run.get("amount_recovered") or 0)
        for run in runs
    )

    return {
        "total_failed": total,
        "total_recovered": recovered,
        "recovery_rate": round(
            recovered / total * 100,
            1
        ),
        "total_amount_recovered": round(
            amount,
            2
        ),
    }


# ---------------------------------------------------------------------------
# Automatically initialize database
# ---------------------------------------------------------------------------

try:
    init_db()
except Exception as exc:
    logger.error(
        "Failed to initialize audit database: %s",
        exc
    )