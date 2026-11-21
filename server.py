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
        "For anything 'sold at Amazon/Walmart/…' call sold_at_recalls. sold_at is required. "
        "Last 30 days sold on Amazon: sold_at_recalls(sold_at='Amazon', days=30) — one call, "
        "not recent_recalls then search_recalls. "
        "Never put Amazon/Walmart in query. "
        "Use count_recalls for 'how many recalls' (announcements), not paging search_recalls."
    ),
)


@mcp.tool()
def sold_at_recalls(
    sold_at: Annotated[
        str,
        Field(description="Retailer, required. Examples: Amazon, Walmart. Matches the sold_at column only."),
    ],
    days: Annotated[
        int | None,
        Field(description="Last N days (1–365). Pass 30 for 'last 30 days'. Omit for all time."),
    ] = None,
    year: int | None = None,
) -> dict:
    """List recalls sold at a retailer. Use this for every 'sold at X' question, including last N days.

    Last 30 days on Amazon: sold_at='Amazon', days=30. Do not also call recent_recalls or search_recalls.
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
        Field(description="Retailer on the sold_at column only, e.g. Amazon or Walmart. Not for last-N-days; use recent_recalls."),
    ] = "",
) -> dict:
    """Search product recalls, newest first. Not for 'last N days sold at X' — use recent_recalls.

    `sold_at`: retailer only (Amazon, Walmart). Use this for 'sold at X', never `query`.
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
        Field(description="Retailer filter on sold_at only, e.g. Walmart. Use this for 'how many sold at X'."),
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
    days: Annotated[int, Field(description="Lookback window, 1–365. Default 30.")] = 30,
    # Field() is what Cursor puts in the JSON schema. Docstrings alone were ignored; agents skipped sold_at.
    sold_at: Annotated[
        str,
        Field(
            description=(
                "REQUIRED when the user names a retailer. Last 30 days sold on Amazon: "
                'days=30 and sold_at="Amazon" in this same call. Do not call search_recalls.'
            ),
        ),
    ] = "",
) -> dict:
    """Recalls in the last `days` days, optionally only those sold at `sold_at` (Amazon, Walmart).

    For 'last 30 days sold on Amazon' pass both: days=30, sold_at="Amazon". One call.
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
