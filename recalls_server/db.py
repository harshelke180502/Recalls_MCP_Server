"""Read and write access to the recalls snapshot (SQLite)."""
from __future__ import annotations

import contextlib
import datetime as dt
import os
import re
import sqlite3
from typing import Any, Iterator

DEFAULT_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "recalls.db")

SUMMARY_COLUMNS = (
    "recall_number, title, recall_date, product_name, hazard, units, sold_at, url"
)


def db_path() -> str:
    return os.environ.get("RECALLS_DB", DEFAULT_DB)


@contextlib.contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    con = sqlite3.connect(db_path())
    con.row_factory = sqlite3.Row
    try:
        yield con
    finally:
        con.close()


def normalize_recall_number(value: str) -> str:
    """Accept '26-123', '26123' or 'Recall 26-123' and return the stored form."""
    return re.sub(r"\D", "", value or "")


def _where(query: str, year: int | None) -> tuple[str, list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    query = (query or "").strip()
    if query:
        like = f"%{query}%"
        clauses.append("(title LIKE ? OR product_name LIKE ? OR hazard LIKE ? OR sold_at LIKE ?)")
        params += [like, like, like, like]
    if year:
        # Recall numbers start with the two-digit year and the column is indexed.
        clauses.append("recall_number LIKE ?")
        params.append(f"{int(year) % 100:02d}%")
    return (" WHERE " + " AND ".join(clauses)) if clauses else "", params


def search(query: str = "", year: int | None = None, limit: int = 20, offset: int = 0) -> tuple[int, list[dict]]:
    where, params = _where(query, year)
    with connect() as con:
        total = con.execute(f"SELECT COUNT(*) FROM recalls{where}", params).fetchone()[0]
        rows = con.execute(
            f"SELECT {SUMMARY_COLUMNS} FROM recalls{where} ORDER BY recall_date DESC, recall_number DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()
    return total, [dict(r) for r in rows]


def count(query: str = "", year: int | None = None) -> int:
    where, params = _where(query, year)
    with connect() as con:
        return con.execute(f"SELECT COUNT(*) FROM recalls{where}", params).fetchone()[0]


def get(recall_number: str) -> dict | None:
    number = normalize_recall_number(recall_number)
    with connect() as con:
        row = con.execute("SELECT * FROM recalls WHERE recall_number = ?", [number]).fetchone()
        if row is None:
            return None
        record = dict(row)
        notes = con.execute(
            "SELECT author, body, created_at FROM notes WHERE recall_number = ? ORDER BY created_at",
            [number],
        ).fetchall()
    record["notes"] = [dict(n) for n in notes]
    return record


def recent(days: int, today: dt.date | None = None, limit: int = 50) -> list[dict]:
    today = today or dt.date.today()
    since = (today - dt.timedelta(days=days)).isoformat()
    with connect() as con:
        rows = con.execute(
            f"SELECT {SUMMARY_COLUMNS} FROM recalls WHERE recall_date >= ? ORDER BY recall_date DESC, recall_number DESC LIMIT ?",
            [since, limit],
        ).fetchall()
    return [dict(r) for r in rows]


def add_note(recall_number: str, body: str, author: str) -> dict:
    created = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with connect() as con:
        cur = con.execute(
            "INSERT INTO notes (recall_number, author, body, created_at) VALUES (?, ?, ?, ?)",
            [recall_number.strip(), author, body.strip(), created],
        )
        con.commit()
        note_id = cur.lastrowid
    return {"id": note_id, "recall_number": recall_number.strip(), "author": author, "created_at": created}


def status() -> dict:
    with connect() as con:
        rows = con.execute("SELECT COUNT(*) FROM recalls").fetchone()[0]
        last = con.execute("SELECT run_at, status FROM load_log ORDER BY run_at DESC LIMIT 1").fetchone()
    return {
        "recalls_loaded": rows,
        "last_load_at": last["run_at"] if last else None,
        "last_load_status": last["status"] if last else "never",
    }
