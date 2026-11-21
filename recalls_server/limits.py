"""Keep tool responses small enough for every client we support."""
from __future__ import annotations

import json

# Some clients cut off or refuse large tool results. Stay well under the smallest limit we have seen.
MAX_RESPONSE_CHARS = 15_000
DEFAULT_LIMIT = 20
MAX_LIMIT = 50


def clamp_limit(limit: int | None) -> int:
    if not limit or limit < 1:
        return DEFAULT_LIMIT
    return min(limit, MAX_LIMIT)


def fit(payload: dict, key: str = "results") -> dict:
    """Trim the list under `key` until the serialized payload fits the size budget."""
    items = payload.get(key) or []
    while items and len(json.dumps(payload, ensure_ascii=False)) > MAX_RESPONSE_CHARS:
        items.pop()
    return payload
