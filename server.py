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

# Cold agents never saw our Q2 plan. These lines are how they pick tools: sold_at, not query.
mcp = FastMCP(
    "recalls",
    instructions=(
        "Product recall lookups for the marketplace-safety team. Data comes from the US Consumer "
        "Product Safety Commission and is refreshed nightly. "
        "Any 'sold at/on/listed at' retailer question (Amazon, Walmart, Target, …) — including "
        "last 7/30/60/90/N days — is sold_at_recalls only. sold_at is required; days is the "
        "lookback (30 if they say last month / last 30 days). One call. Do not use "
        "recent_recalls (that tool has no retailer filter) and do not use search_recalls query. "
        "Use count_recalls for 'how many recalls' (announcements), not paging search_recalls."
    ),
)


@mcp.tool()
def sold_at_recalls(
    sold_at: Annotated[
        str,
        Field(
            description="Retailer, required. Amazon, Walmart, Target, … — 'sold at', 'sold on', or 'listed at'.",
        ),
    ],
    days: Annotated[
        int | None,
        Field(
            description="Lookback in days, 1–365. 7=last week, 30=last 30 days, 60, 90, or any N they name. Omit for all time.",
        ),
    ] = None,
    year: int | None = None,
) -> dict:
    """The Q2 tool: recalls sold at a retailer, optionally in the last N days.

    Examples: last 30 days on Amazon → sold_at=Amazon, days=30. Last 90 days at Walmart →
    sold_at=Walmart, days=90. Do not call recent_recalls or search_recalls for these.
    """
    return tools.sold_at_recalls(sold_at, days=days, year=year)


@mcp.tool()
def search_recalls(
    query: Annotated[
        str,
        Field(description="Keywords in title, product, or hazard. Never Amazon/Walmart — use sold_at."),
    ] = "",
    year: int | None = None,
    limit: int = 20,
    cursor: int = 0,
    sold_at: Annotated[
        str,
        Field(description="Retailer, sold_at column only. For last N days sold at X use sold_at_recalls, not this tool."),
    ] = "",
) -> dict:
    """Search product recalls, newest first. Not for 'last N days sold at X' — use sold_at_recalls.

    `query`: keywords in title, product name, and hazard. Do not put a retailer here.
    `year` limits to that year. Returns `total`, up to `limit` results (max 50), and
    `next_cursor` when there are more: pass it back as `cursor`.
    """
    return tools.search_recalls(query, year, limit, cursor, sold_at)


@mcp.tool()
def count_recalls(
    query: Annotated[
        str,
        Field(description="Keywords in title/product/hazard. Not a retailer — use sold_at for Amazon/Walmart."),
    ] = "",
    year: int | None = None,
    sold_at: Annotated[
        str,
        Field(description="Retailer filter. For a list of last-N-days sold at X, use sold_at_recalls instead."),
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
    days: Annotated[int, Field(description="Lookback window, 1–365. Default 30. No retailer filter.")] = 30,
) -> dict:
    """Recalls announced in the last `days` days. Date window only — no Amazon/Walmart filter.

    If the user names a store, do not use this tool; use sold_at_recalls(sold_at, days).
    """
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
