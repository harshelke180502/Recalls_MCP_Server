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
        "questions instead of paging search_recalls."
    ),
)


@mcp.tool()
def search_recalls(query: str = "", year: int | None = None, limit: int = 20, cursor: int = 0) -> dict:
    """Search product recalls, newest first.

    `query` matches the recall title, product name, hazard and where the product was sold.
    `year` limits results to recalls from that year. Returns `total` (all matches), up to
    `limit` results (max 50), and `next_cursor` when there are more: pass it back as `cursor`.
    """
    return tools.search_recalls(query, year, limit, cursor)


@mcp.tool()
def count_recalls(query: str = "", year: int | None = None) -> dict:
    """Count recalls matching `query` and/or `year`. Same matching rules as search_recalls."""
    return tools.count_recalls(query, year)


@mcp.tool()
def get_recall(recall_number: str) -> dict:
    """Get one recall with all its details and any notes the team has added.

    Accepts the number with or without the dash (for example 26-123 or 26123).
    """
    return tools.get_recall(recall_number)


@mcp.tool()
def recent_recalls(days: int = 30) -> dict:
    """List recalls announced in the last `days` days (default 30), newest first."""
    return tools.recent_recalls(days)


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
