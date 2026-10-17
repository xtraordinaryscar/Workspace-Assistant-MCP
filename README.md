# workspace-assistant (MCP server)

A small [Model Context Protocol](https://modelcontextprotocol.io) server, written in Python, that gives Claude twelve tools for working with a project folder: listing, searching, reading, editing and analyzing files, generating Markdown output, saving notes, and read-only git information.

Built for a university course project using the official `mcp` Python SDK (version 1.x, FastMCP style). It serves MCP over **streamable HTTP** on `127.0.0.1`. claude.ai reaches it through a fixed **ngrok** address, and small watchdog scripts keep the server and tunnel running.

## What it does

| Tool | What it does | Writes files? |
|---|---|---|
| `list_project_files` | Lists files with size and last-modified date, with an optional extension filter | No |
| `analyze_text_file` | Word count, line count, reading time and top 10 keywords | No |
| `search_in_files` | Case-insensitive keyword search across text files, with file and line numbers | No |
| `generate_markdown_toc` | Builds a Markdown table of contents from a `.md` file's headings | No |
| `generate_project_report` | Markdown summary: counts by file type, total size, largest and newest files | Only if `save_as` is given |
| `write_note` | Creates a new `.md` or `.txt` file in `notes/` | Yes (new files only) |
| `find_todos` | Lists `TODO`, `FIXME` and `NOTE` comments with file and line number | No |
| `find_broken_links` | Reports relative links in a `.md` file that point to files that don't exist | No |
| `read_file` | Returns a file's lines with line numbers, in parts for long files | No |
| `str_replace` | Replaces one exact piece of text in an existing file (must match exactly once; never edits `server.py`) | Yes (existing files only) |
| `delete_file` | Moves a file into `.trash/` so it can be recovered; never erases it; never touches `server.py` | Yes (moves to `.trash/`) |
| `git_lite` | Runs only `git status`, `git log` or `git diff` and returns the output | No |

## Project structure

```
mcp-server/
├── server.py          # the MCP server and all tools
├── requirements.txt   # Python dependency (mcp 1.x)
├── test_tools.py      # tests that call the tools directly (no Claude needed)
├── run-server.bat     # keeps the server running (restarts it if it stops)
├── run-tunnel.bat     # keeps the ngrok tunnel running (restarts it if it stops)
├── start-all.bat      # starts both watchdogs
├── check-status.bat   # checks that both addresses respond
├── handoff/           # session handoff files (see "Handoff protocol" below)
├── .gitignore         # keeps notes/, .trash/, logs/, caches and test files out of git
└── README.md
```

`notes/` is created the first time `write_note` (or a saved report) writes a file. `.trash/` holds files removed by `delete_file`. `logs/` holds the watchdog output. The tests use a temporary folder and delete it afterwards.

## Setup (Windows), one time

### 1. Install Python

1. Download Python 3.10 or newer from https://www.python.org/downloads/
2. In the installer, tick **"Add python.exe to PATH"** before clicking Install.
3. Open a new Command Prompt and check: `python --version`

### 2. Install the Python dependency

```
cd "C:\Users\Carl Stephen\Desktop\claude-test\mcp-server"
pip install -r requirements.txt
```

`requirements.txt` pins `mcp>=1.8.0,<2`. Streamable HTTP needs 1.8 or newer, and version 2.x renamed `FastMCP`.

### 3. Test the tools

```
python test_tools.py
```

You should see `Result: N passed, 0 failed`. No network or ngrok is needed for this.

### 4. Install ngrok and add your authtoken

1. Install ngrok:
   ```
   winget install ngrok.ngrok
   ```
   Close and reopen Command Prompt afterwards.
2. Copy your authtoken from the ngrok dashboard (**Your Authtoken** page), then run:
   ```
   ngrok config add-authtoken <your-authtoken>
   ```

The authtoken is stored in ngrok's own configuration. It is **not** stored in any file in this project.

### 5. Your fixed address

The domain is stored in a local file named `ngrok-domain.txt`, which git ignores, so it is not committed. Create it in the `mcp-server` folder with your domain on one line:

```
your-name.ngrok-free.dev
```

The scripts `run-tunnel.bat` and `check-status.bat` read the domain from that file. If it is missing, they stop and say so.

Your claude.ai connector URL is that domain with `/mcp` added:

```
https://<your-ngrok-domain>/mcp
```

## Running it

### Start everything

Double-click **`start-all.bat`**, or run it from Command Prompt. Two minimized windows open: one for the server and one for the tunnel. Their output goes to `logs\server.log` and `logs\tunnel.log`.

Then run **`check-status.bat`**. Both lines should show `HTTP 406`. A `406` means the server answered; plain `curl` doesn't send the `Accept` header that MCP requires, so `406` is the expected reply. `000`, `502` or `503` means that part is down.

### Stop everything

Open Task Manager and end the two `cmd.exe` windows titled **workspace-assistant server** and **ngrok tunnel**, and end any `python.exe` and `ngrok.exe` processes that remain. Closing a watchdog window alone is not enough, because the watchdog keeps restarting the program.

### Do not run start-all twice

A second copy of the server fails with "port in use". Stop everything first, then start again.

### Start automatically at login (Task Scheduler)

1. Press **Win + R**, type `taskschd.msc`, and press Enter.
2. In the right panel, click **Create Task...** (not "Create Basic Task").
3. **General tab:** name it `workspace-assistant`. Choose **Run only when user is logged on**.
4. **Triggers tab:** click **New...**, set **Begin the task** to **At log on**, and choose your user. Click OK.
5. **Actions tab:** click **New...**, set **Program/script** to:
   ```
   C:\Users\Carl Stephen\Desktop\claude-test\mcp-server\start-all.bat
   ```
   Set **Start in** to `C:\Users\Carl Stephen\Desktop\claude-test\mcp-server`. Click OK.
6. **Conditions tab:** if it's a laptop, uncheck **Start the task only if the computer is on AC power**.
7. Click OK. Enter your Windows password if asked.

The services now start each time you log in. They stop when you shut down, sleep or log out, so run `check-status.bat` after logging in.

## Connecting claude.ai (once only)

1. In claude.ai, open **Settings → Connectors**.
2. Click **Add custom connector**.
3. Enter the URL `https://<your-ngrok-domain>/mcp`.
4. Leave the OAuth Client ID and Client Secret fields **empty**, then save and connect.

Because the address is fixed, you don't need to change the connector again. Menu names change, so check Anthropic's current documentation if the steps differ.

## Example prompts to try

- "List all the files in the project."
- "List only the `.md` files."
- "Analyze `README.md`. What are the top keywords and how long does it take to read?"
- "Search the project for the word 'safe'."
- "Generate a table of contents for `README.md`."
- "Make a project report for the project folder."
- "Create a note called `ideas.md` with three ideas for this project."
- "Find all the TODO, FIXME and NOTE comments in the project."
- "Check README.md for broken links."
- Live demo: "Create a note called `demo.md` containing the line `TODO: write the tests` and a link `[missing](nope.md)`. Then find the TODOs, and check `notes/demo.md` for broken links."
- "Read the first 40 lines of `server.py`."
- "In `notes/demo.md`, replace `TODO: write the tests` with `DONE: tests written`."
- "Show the last 10 git commits."
- "Delete `notes/demo.md`." (It goes to `.trash/`, not permanently erased.)
- Safety check: "Analyze `..\hello.txt`." (This should be refused.)

## Limitations and safety

**Safety**
- Every path goes through `safe_path()`, which resolves it and rejects anything outside the `mcp-server` folder. This blocks `..`, absolute paths such as `C:\Windows\...`, and symlinks that point outside.
- Writing is limited to these tools: `write_note` and `generate_project_report` (with `save_as`) create new files in `notes/`; `str_replace` edits existing text files; `delete_file` moves a file into `.trash/`. Nothing is permanently erased by the server, and `server.py` cannot be edited or deleted through these tools.
- `git_lite` runs `git` with three fixed commands (`status`, `log`, `diff`). It does not use a shell and cannot run any other command.
- Problems are returned to Claude as `Error: ...` messages instead of crashing the server.

**Limitations**
- **There is no login.** The server has no password or token. Anyone who knows the ngrok address can call its tools while the tunnel is running, and `write_note`, `str_replace` and `delete_file` can change files in the project. Keep the address private, and stop the services when you are not using them.
- The server listens only on `127.0.0.1`. ngrok is what makes it reachable from outside.
- The server rewrites the incoming `Host` header to `127.0.0.1` so that the MCP SDK accepts requests coming through the tunnel.
- The watchdogs only run while you are logged in, and they stop when the computer sleeps or shuts down.
- The watchdogs restart a crashed program, but they don't fix a bug that crashes it every time. Check `logs\server.log` if the restarts keep happening.
- Works only with UTF-8 text files up to about 1 MB (`.txt`, `.md`, `.py`, `.json`, `.csv`, `.log`, `.html`, `.css`, `.js`, `.yaml`, `.yml`, `.toml`, `.ini`). It cannot read Word, PDF or image files.
- Keyword analysis is simple word counting with a basic English stop-word list; it does not understand meaning.
- Reading time assumes 200 words per minute.
- Search is plain text matching (no regular expressions) and shows at most 50 matches.
- `find_todos` matches only the uppercase words TODO, FIXME and NOTE, scans code files too (so it also lists those words inside `server.py`), and shows at most 50 results.
- `find_broken_links` only checks that a link's target file or folder exists. It does not check `#anchors` inside other files, and it skips external links (`http`, `mailto`).
- `str_replace` writes files with UTF-8 encoding, so a file that started with a byte-order mark may lose it.
- `git_lite` needs `git` installed, and it only works inside a folder that is a Git repository. Run `git init` in `mcp-server` first.
- The `.trash/` folder grows over time. Empty it by hand when you no longer need the files.
- The boundary is only the `mcp-server` folder, so files elsewhere in `claude-test` are not reachable through this server.

## Handoff protocol

Long projects often span several chat sessions, and sometimes several AI agents. The `handoff/` folder keeps the work continuous, so a new session can resume without the user re-explaining anything.

| File | Purpose | How it changes |
|---|---|---|
| `PROJECT_STATE.md` | Current status, constraints, next steps | Rewritten in place |
| `PLAN_LOG.md` | What was planned and what happened | Append only |
| `CHECKPOINTS.md` | Snapshots to resume from | Append only |
| `DECISIONS.md` | Why choices were made | Append only (status changes, never deleted) |
| `transcripts/` | Saved tool-call transcripts of demo sessions | Added as needed |

### Starting a session

1. Read `handoff/PROJECT_STATE.md`.
2. Read the latest entries of `CHECKPOINTS.md` and `PLAN_LOG.md`.
3. Check `DECISIONS.md` before changing anything that has a recorded decision.
4. Check `git status` to see uncommitted changes.

### Ending a session

1. Update the status, next steps and known issues in `PROJECT_STATE.md`.
2. Update the plan status in `PLAN_LOG.md`.
3. Add a checkpoint in `CHECKPOINTS.md` with a clear **Resume from** note.

### Rules

- Never delete or rewrite earlier log entries. Correct a mistake with a new entry that refers to the old one by ID.
- IDs increase by one and are never reused (`PLAN-001`, `CP-001`, `D-001`).
- Every entry has a date (YYYY-MM-DD) and the name of the agent that wrote it.
- Record what was verified and how. Do not record what was expected.
- Keep secrets (authtokens, passwords) out of every handoff file.

### Tool note

Appends are made with the tool available in that environment. In Claude Desktop this is the filesystem server's `edit_file`. In claude.ai the custom connector's `str_replace` is used on the marker line `<!-- APPEND NEW ENTRIES ABOVE THIS LINE -->`. If the required tool is missing, the agent must tell the user before using a different tool.

### Why this works

The handoff files are the only memory that carries from one session to the next. A session that needs something the files don't contain should record it as a gap, not guess. The project's midterm test was a two-session audit: the second session resumed from the files and finished the work without asking the user any questions.
