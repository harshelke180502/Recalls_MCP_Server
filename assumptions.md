# Assumptions

## Q3 — most units in 2024

**Assumption:** I return the **single 2024 recall row with the max `units`** (one `recall_number`). I do **not** group duplicate products or sum their units.

That is `search_recalls(year=2024, sort="units", limit=1)`. “How many” is **`units` on that row**, not a year-wide total and not a sum across duplicates.

Each CPSC announcement is already one row. A reannounce is usually a **new** recall number, so it competes on its own `units` rather than being merged.

---

## If Dana instead wanted “duplicates → sum, then take the highest sum”

I would keep the same MCP tool (`search_recalls` + `sort=units`) but change the SQL when `sort=units`: **GROUP BY product**, **SUM(units)**, order by that sum, `limit=1`. The answer would be the **product name** and the **summed** units, not one recall number’s raw `units`.

Commented sketch (not wired up):

```python
# Alternate Q3 if Dana wants product-level duplicates summed, then the highest sum.
# if (sort or "").strip().lower() == "units":
#     rows = con.execute(
#         f"""
#         SELECT
#             product_name,
#             SUM(units) AS units,
#             MIN(recall_number) AS recall_number,
#             MAX(recall_date) AS recall_date,
#             MIN(title) AS title
#         FROM recalls
#         {where}
#         GROUP BY product_name
#         ORDER BY units DESC
#         LIMIT ? OFFSET ?
#         """,
#         params + [limit, offset],
#     ).fetchall()
# # Then results[0] is the product with the largest SUM(units) in that year.
```

Until she answers, the live path stays **max on one recall_number** (see `_order` in `recalls_server/db.py`).

---

## Q5 — how the recall number is shown

**Assumption:** It is fine to **show** the number the way the user typed it (`27-010`). The important part is that **save and load use the same digit key** (`27010`) so the note appears. I did **not** change the chat/UI to print only the normalized form.

`add_note` and `get_recall` both strip to digits in the DB. If Dana wanted the tool payload and the agent reply to always show `27010`, that would be a small display change on the returned `recall_number` (already normalized on save) and on `get_recall` echoing CPSC’s dashed style vs digits. Not built; called out as unchecked.
