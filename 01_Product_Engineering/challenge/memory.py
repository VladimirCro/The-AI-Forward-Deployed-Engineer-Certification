"""Week 7: episodic memory. What the assessment and the consultant did, so it can be explained later.

An episode holds what the code saw, not what the model says about it: the documents found, their
labels, the quotes the check dropped, the proposed levels, the consultant's decision.

Staleness: supersede on write. One live episode per client, control, kind and dimension. A new one
marks the old one replaced; the old one is kept for the audit. The unique index on live episodes
means the database refuses a second one.
"""

import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS episodes (
    id          INTEGER PRIMARY KEY,
    client_id   TEXT NOT NULL,
    control_id  TEXT NOT NULL,
    kind        TEXT NOT NULL CHECK (kind IN ('assessment', 'decision')),
    dimension   TEXT NOT NULL DEFAULT '',
    inputs_hash TEXT NOT NULL DEFAULT '',
    data        TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    replaced_at TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS one_live
    ON episodes (client_id, control_id, kind, dimension) WHERE replaced_at IS NULL;
"""

SUBJECT = "client_id = ? AND control_id = ? AND kind = ? AND dimension = ?"


def _connect() -> sqlite3.Connection:
    # Read on every call, so a test can point MEMORY_FILE at its own empty file.
    # Two endpoints can write at once: the second one waits for the first instead of failing.
    conn = sqlite3.connect(os.getenv("MEMORY_FILE") or "/tmp/memory.sqlite", timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def _episode(row: sqlite3.Row) -> dict:
    return {**dict(row), "data": json.loads(row["data"])}


def record(client_id: str, control_id: str, kind: str, data: dict, dimension: str = "", inputs_hash: str = "") -> int:
    """Store a new live episode for this subject and mark the one it replaces. Returns the new id."""
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    subject = (client_id, control_id, kind, dimension)
    # One transaction: the old episode is replaced first, or the index would refuse the new one.
    # IMMEDIATE takes the write lock at the start, so two writers queue instead of deadlocking.
    with closing(_connect()) as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            conn.execute(f"UPDATE episodes SET replaced_at = ? WHERE {SUBJECT} AND replaced_at IS NULL", (now, *subject))
            cursor = conn.execute(
                "INSERT INTO episodes (client_id, control_id, kind, dimension, inputs_hash, data, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (*subject, inputs_hash, json.dumps(data, ensure_ascii=False), now))
            conn.execute("COMMIT")
        except BaseException:
            conn.execute("ROLLBACK")
            raise
        return cursor.lastrowid


def live(client_id: str, control_id: str, kind: str, dimension: str = "") -> dict | None:
    """The current episode for this subject, or None when there is none."""
    with closing(_connect()) as conn:
        row = conn.execute(f"SELECT * FROM episodes WHERE {SUBJECT} AND replaced_at IS NULL",
                           (client_id, control_id, kind, dimension)).fetchone()
    return _episode(row) if row else None


def history(client_id: str, control_id: str, kind: str, dimension: str = "") -> list[dict]:
    """Every episode for this subject, oldest first, the replaced ones included."""
    with closing(_connect()) as conn:
        rows = conn.execute(f"SELECT * FROM episodes WHERE {SUBJECT} ORDER BY id",
                            (client_id, control_id, kind, dimension)).fetchall()
    return [_episode(row) for row in rows]
