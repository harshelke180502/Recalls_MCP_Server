# Recalls MCP server: take-home exercise

Thanks for doing this. It should take **45 minutes at most**. Use whatever AI coding tools you
normally use. If you reach 45 minutes, stop and tell us where you got to. An honest note at
45 minutes is a good submission, and you are not expected to finish everything.

## The situation

You have just joined a small platform team. One of the things you now own is this MCP server.
Other teams connect their agents to it to answer questions about US product recalls. The data is
real: it comes from the US Consumer Product Safety Commission (CPSC), which publishes every recall
at <https://www.cpsc.gov/Recalls>.

The nightly job that loads `data/recalls.db` lives in another repo, which you don't have. What you
have is the server and last night's snapshot. The previous owner's handoff is in `NOTES.md`.

Your teammate Dana left you this message:

> Hey, welcome! Quick one before I'm out till Monday. The marketplace-safety folks have started
> pointing their agents at our recalls server, and they keep asking two things it can't really do:
> "how many units were recalled" (for a year, or for products sold at some retailer) and "what's
> been recalled that was sold at X". Can you add what's needed so an agent can answer those? I told
> them they could start relying on it Monday, so also tell me straight whether it's ready for that.
> The questions they asked last week are below if you want something to try it with. Thanks!

Dana can't be reached. Where something is unclear, write down the question you would have asked
and the assumption you made.

## What the team asked last week

1. How many recalls were there in 2025?
2. What has been recalled in the last 30 days that was sold on Amazon?
3. Which recall in 2024 covered the most units, and how many?
4. How many recalls list Walmart as a place the product was sold?
5. Add a note to recall 27-010: "Legal is reviewing our listings." Then show me that recall.

## Setup (about five minutes)

You need Python 3.10 or newer. There is one dependency, the official MCP SDK. No API keys.

macOS or Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -t .
```

Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m unittest discover -s tests -t .
```

Then connect your agent to the server. It speaks MCP over stdio: the command is the Python inside
`.venv`, and the only argument is the full path to `server.py`.

Claude Code, macOS or Linux:

```bash
claude mcp add recalls -- "$(pwd)/.venv/bin/python" "$(pwd)/server.py"
```

Claude Code, Windows (PowerShell):

```powershell
claude mcp add recalls -- "$PWD\.venv\Scripts\python.exe" "$PWD\server.py"
```

Codex CLI:

```bash
codex mcp add recalls -- "$(pwd)/.venv/bin/python" "$(pwd)/server.py"
```

Cursor, or any client that takes a JSON config (use your own full paths):

```json
{
  "mcpServers": {
    "recalls": {
      "command": "/full/path/to/.venv/bin/python",
      "args": ["/full/path/to/server.py"]
    }
  }
}
```

Restart your client after you change the server's code, so it picks up the new version.

## What to send back

1. **Your code**, as a zip or a link to a repo.
2. **A five-minute screen recording, unedited.** Show your agent, connected to this server,
   answering at least three of the questions above. Show the capability Dana asked for, working.
   Show anything else you think we should see.
3. **A short note, half a page at most:**
   - Is it ready for the team to rely on Monday? Yes or no, and why.
   - What you checked, and how.
   - What you did not check.
   - The questions you would have asked Dana, and the assumptions you made.
   - Which AI tools you used.
