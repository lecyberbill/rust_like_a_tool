import json
import sqlite3
import threading
from pathlib import Path

_CHECKPOINT_DB = str(Path(__file__).parent / ".run_checkpoint.db")
_LOCK = threading.Lock()

_INIT_SQL = """
CREATE TABLE IF NOT EXISTS checkpoints (
    plan_id TEXT NOT NULL,
    completed_steps TEXT NOT NULL DEFAULT '[]',
    step_performance TEXT NOT NULL DEFAULT '{}',
    execution_context TEXT NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (plan_id)
);
"""

def _get_conn():
    conn = sqlite3.connect(_CHECKPOINT_DB, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(_INIT_SQL)
    conn.commit()
    return conn

def save_checkpoint(plan_id: str, completed_steps: list, step_performance: dict, execution_context: dict):
    with _LOCK:
        conn = _get_conn()
        try:
            conn.execute(
                """INSERT OR REPLACE INTO checkpoints
                   (plan_id, completed_steps, step_performance, execution_context, updated_at)
                   VALUES (?, ?, ?, ?, datetime('now'))""",
                (
                    plan_id,
                    json.dumps(list(completed_steps), ensure_ascii=False),
                    json.dumps(step_performance, ensure_ascii=False),
                    json.dumps(execution_context, ensure_ascii=False),
                )
            )
            conn.commit()
        finally:
            conn.close()

def load_checkpoint(plan_id: str) -> dict | None:
    with _LOCK:
        conn = _get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM checkpoints WHERE plan_id = ?", (plan_id,)
            ).fetchone()
            if row:
                return {
                    "plan_id": row["plan_id"],
                    "completed_steps": set(json.loads(row["completed_steps"])),
                    "step_performance": json.loads(row["step_performance"]),
                    "execution_context": json.loads(row["execution_context"]),
                }
            return None
        finally:
            conn.close()

def delete_checkpoint(plan_id: str):
    with _LOCK:
        conn = _get_conn()
        try:
            conn.execute("DELETE FROM checkpoints WHERE plan_id = ?", (plan_id,))
            conn.commit()
        finally:
            conn.close()
