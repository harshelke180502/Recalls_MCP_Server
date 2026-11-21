# Questions I would have asked Dana

Dana was out until Monday, so these are the questions I would have asked before locking Q3.

## Q3 — “Which recall in 2024 covered the most units, and how many?”

1. By “which recall,” do you mean **one CPSC recall number** (one row in `recalls`), i.e. the announcement with the **largest `units` value** (a **max**)?

2. Or, if the **same product** shows up more than once in 2024 (reannounce, extra SKU, two recall numbers with similar titles), should we **group those rows**, **sum `units`**, and return the **product whose summed units are highest** (name + that sum)?

3. If two different recall numbers truly tie on `units`, which one should we return (newer date, either, both)?

4. Should “how many” be the parsed **`units`** integer, or the original **`units_text`** (“About 1,200”)?
