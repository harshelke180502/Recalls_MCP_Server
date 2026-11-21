"""Tool implementations. Kept free of MCP imports so they can be unit tested directly."""
from __future__ import annotations

import datetime as dt

from . import db
from .limits import clamp_limit, fit

SOURCE = "US Consumer Product Safety Commission recalls feed, loaded nightly"


def search_recalls(
    query: str = "",
    year: int | None = None,
    limit: int = 20,
    cursor: int = 0,
    sold_at: str = "",
) -> dict:
    limit = clamp_limit(limit)
    cursor = max(cursor or 0, 0)
    total, rows = db.search(query, year, limit, cursor, sold_at)
    payload = {"total": total, "results": rows}
    if sold_at.strip():
        payload["sold_at"] = sold_at.strip()
    if cursor + len(rows) < total:
        payload["next_cursor"] = cursor + limit
    return fit(payload)


def count_recalls(query: str = "", year: int | None = None, sold_at: str = "") -> dict:
    payload = {"count": db.count(query, year, sold_at)}
    if (sold_at or "").strip():
        payload["sold_at"] = sold_at.strip()
    return payload


def get_recall(recall_number: str) -> dict:
    record = db.get(recall_number)
    if record is None:
        return {"found": False, "recall_number": recall_number}
    record["found"] = True
    return record


def recent_recalls(days: int = 30, today: dt.date | None = None, sold_at: str = "") -> dict:
    # Keep a 1–365 day cap: this tool is a short window, and results are already limited to 50 rows.
    days = max(1, min(days or 30, 365))
    rows = db.recent(days, today=today, sold_at=sold_at)
    payload = {"days": days, "count": len(rows), "results": rows}
    if (sold_at or "").strip():
        payload["sold_at"] = sold_at.strip()
    return fit(payload)


def add_note(recall_number: str, note: str, author: str = "agent") -> dict:
    if not (note or "").strip():
        return {"saved": False, "error": "note is empty"}
    saved = db.add_note(recall_number, note, author or "agent")
    return {"saved": True, **saved}


def server_status() -> dict:
    return {**db.status(), "source": SOURCE}
