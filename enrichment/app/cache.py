import hashlib
import json
import sqlite3
import time
from typing import Any, Optional

from .config import CACHE_DB, CACHE_TTL_SECONDS

_SCHEMA = """
CREATE TABLE IF NOT EXISTS cache (
    key         TEXT PRIMARY KEY,
    kind        TEXT NOT NULL,
    params      TEXT NOT NULL,
    payload     TEXT NOT NULL,
    fetched_at  REAL NOT NULL,
    ttl         INTEGER NOT NULL,
    pinned      INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_cache_kind ON cache(kind);
"""


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(CACHE_DB, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init() -> None:
    with _conn() as conn:
        conn.executescript(_SCHEMA)


def make_key(kind: str, params: dict) -> str:
    blob = json.dumps({"kind": kind, "params": params}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()


def get(kind: str, params: dict) -> Optional[dict]:
    """Return cached payload if present and unexpired. Pinned rows never expire."""
    key = make_key(kind, params)
    with _conn() as conn:
        row = conn.execute("SELECT * FROM cache WHERE key = ?", (key,)).fetchone()
    if row is None:
        return None
    age = time.time() - row["fetched_at"]
    if not row["pinned"] and age > row["ttl"]:
        return None
    return {
        "payload": json.loads(row["payload"]),
        "fetched_at": row["fetched_at"],
        "cached": True,
        "pinned": bool(row["pinned"]),
    }


def put(kind: str, params: dict, payload: Any, pinned: bool = False) -> float:
    key = make_key(kind, params)
    now = time.time()
    with _conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO cache (key, kind, params, payload, fetched_at, ttl, pinned)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                key,
                kind,
                json.dumps(params, sort_keys=True),
                json.dumps(payload),
                now,
                CACHE_TTL_SECONDS,
                1 if pinned else 0,
            ),
        )
    return now


def pin(kind: str, params: dict) -> bool:
    """Mark an entry as demo-critical so it never expires mid-demo."""
    key = make_key(kind, params)
    with _conn() as conn:
        cur = conn.execute("UPDATE cache SET pinned = 1 WHERE key = ?", (key,))
    return cur.rowcount > 0


def stats() -> dict:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT kind, COUNT(*) n, SUM(pinned) pinned FROM cache GROUP BY kind"
        ).fetchall()
        total = conn.execute("SELECT COUNT(*) n FROM cache").fetchone()["n"]
    return {
        "total_entries": total,
        "by_kind": [
            {"kind": r["kind"], "entries": r["n"], "pinned": r["pinned"] or 0} for r in rows
        ],
    }


def entries(kind: Optional[str] = None) -> list:
    q = "SELECT kind, params, fetched_at, pinned FROM cache"
    args: tuple = ()
    if kind:
        q += " WHERE kind = ?"
        args = (kind,)
    with _conn() as conn:
        rows = conn.execute(q + " ORDER BY fetched_at DESC", args).fetchall()
    return [
        {
            "kind": r["kind"],
            "params": json.loads(r["params"]),
            "fetched_at": r["fetched_at"],
            "pinned": bool(r["pinned"]),
        }
        for r in rows
    ]
