"""Recalls MCP server (stdio).

Run:  python server.py
Agents connect to it as an MCP server named "recalls". See README.md for client setup.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP  # noqa: E402

from recalls_server import tools  # noqa: E402

mcp = FastMCP(
    "recalls",
    instructions=(
        "Product recall lookups for the marketplace-safety team. Data comes from the US Consumer "
        "Product Safety Commission and is refreshed nightly. Use count_recalls for 'how many' "
        "questions instead of paging search_recalls. For 'sold at Amazon/Walmart' use the sold_at "
        "argument (not query). For 'last N days sold at X' call recent_recalls with days and sold_at."
    ),
)


@mcp.tool()
def search_recalls(
    query: str = "",
    year: int | None = None,
    limit: int = 20,
    cursor: int = 0,
    sold_at: str = "",
) -> dict:
    """Search product recalls, newest first.

    `query` matches the recall title, product name, hazard and where the product was sold.
    `sold_at` is the retailer filter: it matches only the sold_at column (e.g. Amazon, Walmart).
    Use sold_at for 'sold at X' questions — query also hits titles, so it over-counts retailers.
    `year` limits results to recalls from that year. Returns `total` (all matches), up to
    `limit` results (max 50), and `next_cursor` when there are more: pass it back as `cursor`.
    """
    return tools.search_recalls(query, year, limit, cursor, sold_at)


@mcp.tool()
def count_recalls(query: str = "", year: int | None = None, sold_at: str = "") -> dict:
    """Count recalls matching `query`, `year`, and/or `sold_at`. Same matching rules as search_recalls."""
    return tools.count_recalls(query, year, sold_at)


@mcp.tool()
def get_recall(recall_number: str) -> dict:
    """Get one recall with all its details and any notes the team has added.

    Accepts the number with or without the dash (for example 26-123 or 26123).
    """
    return tools.get_recall(recall_number)


@mcp.tool()
def recent_recalls(days: int = 30, sold_at: str = "") -> dict:
    """List recalls announced in the last `days` days (default 30), newest first.

    `days` is any window from 1 to 365 (not only 30). Pass `sold_at` (Amazon, Walmart, …)
    to answer 'what was recalled in the last X days that was sold at X' in one call.
    """
    return tools.recent_recalls(days, sold_at=sold_at)


@mcp.tool()
def add_note(recall_number: str, note: str, author: str = "agent") -> dict:
    """Attach a short note to a recall so teammates and their agents can see it on get_recall."""
    return tools.add_note(recall_number, note, author)


@mcp.tool()
def server_status() -> dict:
    """Report how many recalls are loaded and when the nightly load last ran."""
    return tools.server_status()


if __name__ == "__main__":
    mcp.run()
