"""Logger: records every tool call (allowed or blocked) in a SQLite database."""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "agentguard_log.db"


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            tool TEXT,
            input TEXT,
            status TEXT,
            reason TEXT,
            duration_ms REAL
        )"""
    )
    return conn


def log_action(tool: str, args: dict, result: dict, duration_ms: float) -> None:
    conn = _connect()
    try:
        conn.execute(
            "INSERT INTO actions (timestamp, tool, input, status, reason, duration_ms) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                datetime.now(timezone.utc).isoformat(),
                tool,
                json.dumps(args)[:500],
                result["status"],
                result.get("reason", ""),
                round(duration_ms, 1),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def last_action_id() -> int:
    conn = _connect()
    try:
        row = conn.execute("SELECT MAX(id) FROM actions").fetchone()
        return row[0] or 0
    finally:
        conn.close()


def actions_since(action_id: int) -> list:
    conn = _connect()
    try:
        return conn.execute(
            "SELECT tool, input, status, reason FROM actions WHERE id > ? ORDER BY id",
            (action_id,),
        ).fetchall()
    finally:
        conn.close()
