# workspace-assistant (MCP server)

A small [Model Context Protocol](https://modelcontextprotocol.io) server, written in Python, that gives Claude twelve tools for working with a project folder: listing, searching and analyzing files, generating Markdown output, and saving notes.

Built for a university course project using the official `mcp` Python SDK (version 1.x, FastMCP style). It serves MCP over **streamable HTTP** on `127.0.0.1` and is reached by claude.ai through a temporary tunnel.

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
├── .gitignore         # keeps notes/, caches and test files out of git
└── README.md
```

`notes/` is created the first time `write_note` (or a saved report) writes a file. The tests use a temporary folder and delete it afterwards, so they leave nothing in the project.

## Setup (Windows)

### 1. Install Python

1. Download Python 3.10 or newer from https://www.python.org/downloads/
2. In the installer, tick **"Add python.exe to PATH"** before clicking Install.
3. Open a new Command Prompt and check:
   ```
   python --version
   ```

### 2. Install the dependency

```
cd "C:\Users\Carl Stephen\Desktop\claude-test\mcp-server"
pip install -r requirements.txt
```

`requirements.txt` pins `mcp>=1.8.0,<2`. Streamable HTTP needs 1.8 or newer, and version 2.x renamed `FastMCP`.

### 3. Test the tools

```
python test_tools.py
```

You should see a list of PASS lines and `Result: N passed, 0 failed`. No network or setup is needed for this.

## Running it for claude.ai

claude.ai connects from Anthropic's cloud, so it can't reach `127.0.0.1` on your PC. You need two running programs: the server, and a tunnel that makes it reachable on the internet.

### 1. Start the server (window 1)

```
cd "C:\Users\Carl Stephen\Desktop\claude-test\mcp-server"
python server.py
```

Leave it open. It listens on `http://127.0.0.1:8000` by default. To use a different port, set `PORT` first with `set PORT=8001`.

### 2. Start a tunnel (window 2)

Install cloudflared once:

```
winget install --id Cloudflare.cloudflared
```

Then start the tunnel:

```
cloudflared tunnel --url http://127.0.0.1:8000
```

It prints an address such as `https://random-words.trycloudflare.com`. Quick Tunnel addresses change every time you restart the tunnel.

### 3. Add the connector in claude.ai (once per tunnel address)

1. Go to **Settings → Connectors**.
2. Delete any old connector for this server.
3. Click **Add custom connector**.
4. Enter the tunnel address with `/mcp` added at the end, for example `https://random-words.trycloudflare.com/mcp`.
5. Leave the OAuth Client ID and Client Secret fields **empty**, then save and connect.

Menu names and supported options change. Check Anthropic's current documentation on custom connectors if the steps differ.

Keep both windows open while you use the connector. Stop the tunnel when you are finished.

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
- **There is no login.** The server has no password or token. Anyone who has the tunnel address can call its tools while the tunnel is running. Keep the address private, and stop the tunnel when you are not demonstrating.
- **`write_note` writes files** (and `generate_project_report` does when `save_as` is given). They can only be created in `notes/`, but anyone who can call the server can make them.
- The server listens only on `127.0.0.1`, and a tunnel is what makes it reachable from outside.
- The server rewrites the incoming `Host` header to `127.0.0.1` so that the MCP SDK accepts requests coming through the tunnel. This is why the connector works.
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
