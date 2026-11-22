# Submission note

**Ready for Monday? No** — not for everything Dana promised. Agents can answer **“what was recalled that was sold at X”** (including last N days). They **cannot** answer **“how many units were recalled”** for a year or a retailer: we never added a **sum of `units`**. I would not tell marketplace-safety to rely on unit totals.

**What it can do:** last-N-days sold at Amazon/Walmart (`recent_recalls` with `sold_at`); count/list sold at a retailer (`count_recalls` / `search_recalls` with `sold_at`); most units on **one** recall in a year (`search_recalls` `sort=units`, `limit=1` — I assumed **max**, not a product-level sum); count announcements by year (Q1); add a note and load the recall (Q5), with dashed numbers stored as digits.

**What it can’t (Dana + assumptions):** year/retailer **unit totals**; Q3 **duplicate-product sums**; showing Q5 numbers only as `27010` in the chat.

**How I checked:** connected Cursor to this MCP, read the tool JSON (name, args, result), and compared order **before vs after**. Prompts were the five from last week, plus Q2/Q3 variants (Walmart 90 days; most units in 2023–2026).

| | Before | After |
|--|--------|--------|
| Q1 2025 count | `count_recalls(year=2025)` → 341 | same |
| Q2 Amazon last 30d | `recent_recalls(days=30)` then `search_recalls(query=Amazon)` | **one** `recent_recalls(days=30, sold_at=Amazon)` |
| Q3 most units 2024 | count → search by date → get / sqlite | **one** `search_recalls(year, sort=units, limit=1)` |
| Q4 Walmart count | fuzzy `query=Walmart` | `count_recalls(sold_at=Walmart)` → 161 |
| Q5 note 27-010 | add then get, **empty notes** (dash vs digits) | same two tools; note shows. Chat still says 27-010 |

**Did not check:** sum of units for a year or retailer; Q3 grouped duplicates; whether Q5 must **display** the normalized number. Due to time constraints and the ambiguity in q3 in test cases with respect to max/sum - so due to ambiguity of the test case I choose to go forward with max of the recall units(as it said most) instead of calculating the sum.

**AI:** Cursor for the code and for all live MCP chats.
