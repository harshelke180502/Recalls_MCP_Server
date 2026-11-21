"""Recalls MCP server (stdio).

Run:  python server.py
Agents connect to it as an MCP server named "recalls". See README.md for client setup.
"""
from __future__ import annotations

import os
import sys
from typing import Annotated

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP  # noqa: E402
from pydantic import Field  # noqa: E402

from recalls_server import tools  # noqa: E402

# One tool for both Q2 and "last N days": recent_recalls. Omit sold_at when no store is named.
mcp = FastMCP(
    "recalls",
    instructions=(
        "Product recall lookups for the marketplace-safety team. Data comes from the US Consumer "
        "Product Safety Commission and is refreshed nightly. "
        "Use recent_recalls for last-N-days lists. If they name a retailer (Amazon, Walmart, "
        "sold at/on/listed at), pass sold_at in that same call — e.g. days=30, sold_at=Amazon. "
        "If they do not name a store, call recent_recalls with only days. Do not also call "
        "search_recalls. Never put Amazon/Walmart in query. "
        "Which recall had the most units (e.g. in 2024): one search_recalls with year, "
        "sort=units, limit=1. Do not use count_recalls for that (count is announcements). "
        "Use count_recalls for 'how many recalls' (announcements), not paging search_recalls."
    ),
)


@mcp.tool()
def search_recalls(
    query: Annotated[
        str,
        Field(description="Keywords in title, product, or hazard. Never Amazon/Walmart — use recent_recalls sold_at for last N days."),
    ] = "",
    year: int | None = None,
    limit: int = 20,
    cursor: int = 0,
    sold_at: Annotated[
        str,
        Field(description="Retailer, sold_at column only. For last N days sold at X use recent_recalls(days, sold_at), not query."),
    ] = "",
    sort: Annotated[
        str,
        Field(
            description=(
                "'date' (default, newest first) or 'units' (largest first). "
                "Most units in a year: year=2024, sort=units, limit=1. One call, not count_recalls."
            ),
        ),
    ] = "date",
) -> dict:
    """Search product recalls. Default newest first. For most units, pass sort=units.

    `query`: keywords in title, product name, and hazard. Do not put a retailer here.
    `year` limits to that year. `sort=units` ranks by the units column (Q3). Returns `total`,
    up to `limit` results (max 50), and `next_cursor` when there are more.
    """
    return tools.search_recalls(query, year, limit, cursor, sold_at, sort)


@mcp.tool()
def count_recalls(
    query: Annotated[
        str,
        Field(description="Keywords in title/product/hazard. Not a retailer — use sold_at for Amazon/Walmart."),
    ] = "",
    year: int | None = None,
    sold_at: Annotated[
        str,
        Field(description="Retailer filter. For a last-N-days list sold at X, use recent_recalls(days, sold_at)."),
    ] = "",
) -> dict:
    """Count recall announcements. Same filters as search_recalls: retailer goes in `sold_at`, not `query`."""
    return tools.count_recalls(query, year, sold_at)


@mcp.tool()
def get_recall(recall_number: str) -> dict:
    """Get one recall with all its details and any notes the team has added.

    Accepts the number with or without the dash (for example 26-123 or 26123).
    """
    return tools.get_recall(recall_number)


@mcp.tool()
def recent_recalls(
    days: Annotated[int, Field(description="Lookback, 1–365. Default 30. Use 60, 90, or any N they name.")] = 30,
    sold_at: Annotated[
        str,
        Field(
            description=(
                "Retailer on the sold_at column (Amazon, Walmart, …). Pass this in the SAME call "
                "when they say sold at/on X. Omit it when they only ask for the last N days."
            ),
        ),
    ] = "",
) -> dict:
    """Last `days` days of recalls. One tool for two questions.

    Last 30 days sold on Amazon: days=30 AND sold_at=Amazon (do not call search_recalls).
    Last 30 days with no store: days=30 only, omit sold_at.
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
