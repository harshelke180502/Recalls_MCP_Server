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


def _where(query: str, year: int | None, sold_at: str = "") -> tuple[str, list[Any]]:
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
    # Retailer questions (Dana / Q2 / Q4) must not reuse `query` — that also hits title and hazard.
    sold_at = (sold_at or "").strip()
    if sold_at:
        clauses.append("sold_at LIKE ?")
        params.append(f"%{sold_at}%")
    return (" WHERE " + " AND ".join(clauses)) if clauses else "", params


def _order(sort: str) -> str:
    # Q3: "most units" = the one recall_number with the largest units (max), not a sum
    # of duplicate products. See assumptions.md if Dana wanted GROUP BY product + SUM.
    # Only "units" is extra; anything else stays newest-first so old search still works.
    if (sort or "").strip().lower() == "units":
        return "ORDER BY units DESC, recall_date DESC, recall_number DESC"
    return "ORDER BY recall_date DESC, recall_number DESC"


def search(
    query: str = "",
    year: int | None = None,
    limit: int = 20,
    offset: int = 0,
    sold_at: str = "",
    sort: str = "date",
) -> tuple[int, list[dict]]:
    where, params = _where(query, year, sold_at)
    order = _order(sort)
    with connect() as con:
        total = con.execute(f"SELECT COUNT(*) FROM recalls{where}", params).fetchone()[0]
        rows = con.execute(
            f"SELECT {SUMMARY_COLUMNS} FROM recalls{where} {order} LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()
    return total, [dict(r) for r in rows]


def count(query: str = "", year: int | None = None, sold_at: str = "") -> int:
    where, params = _where(query, year, sold_at)
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


def recent(days: int, today: dt.date | None = None, limit: int = 50, sold_at: str = "") -> list[dict]:
    today = today or dt.date.today()
    since = (today - dt.timedelta(days=days)).isoformat()
    # Date window is not part of _where (that helper is query/year/sold_at). Combine here for Q2.
    clauses = ["recall_date >= ?"]
    params: list[Any] = [since]
    sold_at = (sold_at or "").strip()
    if sold_at:
        clauses.append("sold_at LIKE ?")
        params.append(f"%{sold_at}%")
    where = " WHERE " + " AND ".join(clauses)
    with connect() as con:
        rows = con.execute(
            f"SELECT {SUMMARY_COLUMNS} FROM recalls{where} ORDER BY recall_date DESC, recall_number DESC LIMIT ?",
            params + [limit],
        ).fetchall()
    return [dict(r) for r in rows]


def add_note(recall_number: str, body: str, author: str) -> dict:
    # Same digit-only key as get_recall, so Q5 "27-010" then get still finds the note.
    number = normalize_recall_number(recall_number)
    created = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with connect() as con:
        cur = con.execute(
            "INSERT INTO notes (recall_number, author, body, created_at) VALUES (?, ?, ?, ?)",
            [number, author, body.strip(), created],
        )
        con.commit()
        note_id = cur.lastrowid
    return {"id": note_id, "recall_number": number, "author": author, "created_at": created}


def status() -> dict:
    with connect() as con:
        rows = con.execute("SELECT COUNT(*) FROM recalls").fetchone()[0]
        last = con.execute("SELECT run_at, status FROM load_log ORDER BY run_at DESC LIMIT 1").fetchone()
    return {
        "recalls_loaded": rows,
        "last_load_at": last["run_at"] if last else None,
        "last_load_status": last["status"] if last else "never",
    }
