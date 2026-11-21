# Handoff notes: recalls server

Written on my last day on the team. Sorry it's brief.

## What it is

An MCP server that lets other teams' agents look up product recalls. Six tools:

- `search_recalls`: search with optional year, paged
- `count_recalls`: same filters, returns a count
- `get_recall`: one recall with its notes
- `recent_recalls`: the last N days
- `add_note`: attach a note to a recall
- `server_status`: row count and last load

Code is in `recalls_server/`. `server.py` wires the tools to MCP. Tests are in `tests/`.

## Data

`data/recalls.db` is SQLite. The loader is a nightly job in the data-platform repo. It pulls the
public CPSC recall feed and upserts into the `recalls` table. Each run writes a row to `load_log`.
I copied last night's snapshot into this repo so you have something to run against.

The loader keeps the original units wording in `units_text` and a parsed number in `units`. It
also tidies the "sold at" text.

## What I verified

- All tests pass.
- Connected it to Claude Code and tried searches for Amazon and Walmart. Results looked right.
- Checked the year filter against the CPSC site for 2025. Counts matched.
- Paged through a large search to make sure the cursor works.
- The load has been green every night since I set it up.

## Known gaps

- No way to total units, and no direct "sold at" lookup. That is what Dana is asking for.
- Notes can't be edited or deleted.
- Responses are capped in `limits.py` because one client was choking on large results.
