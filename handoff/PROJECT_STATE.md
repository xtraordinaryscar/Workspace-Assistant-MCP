# PROJECT_STATE

> **Read this file first at the start of every session.** It is the single source of truth for where the project stands. The rules for this file and the other three handoff files are in "Handoff protocol" at the end.

**Project:** workspace-assistant, an MCP file-server connector (Python, `mcp` SDK, streamable HTTP)
**Root:** `mcp-server/` (the sandbox; the tools cannot reach anything outside it)
**Last updated:** 2026-10-17 by Claude (session 1)
**Branch and commit at last update:** `handoff-protocol` @ 6c14a42 ("added handoff files"), one commit ahead of `main` @ 8562201. Handoff files are committed; the protocol's append method was corrected after the commit (see CP-004, not yet committed).

## Current status

**Working (per code and README read in session 1)**
- 12 tools in `server.py`, all paths resolved through `safe_path()`
- Tests in `test_tools.py` (last recorded run result: none; see Known issues)
- Server on `127.0.0.1:8000`, public HTTPS through an ngrok fixed domain (set at the top of `run-tunnel.bat`)
- Process management: `run-server.bat` and `run-tunnel.bat` restart on crash, `start-all.bat` launches both, `check-status.bat` checks both (HTTP 406 from each address means it is up)
- Connected to Claude Desktop through the public address; `notes/test-note.md` shows a successful write from a real client
- Handoff append method tested and working with the filesystem `edit_file` tool (CP-004)

**Done**
- Handoff protocol created in `handoff/` and committed (CP-003)
- Append method verified (CP-004)

**Not done (requirements for the midterm brief)**
- Multi-step demo task across 2 or more sessions with a real MCP client (PLAN-002)
- Tool-call transcript of the demo task
- Handoff protocol verified in use: the files exist, but no session has resumed from them yet
- Short report on stack, tool design choices, and security tradeoffs (PLAN-003)
- 5-minute live demo
- README section describing the handoff protocol
- Stretch goals (optional): `if_version` locking, `search_code`, repo map, token auth

## Tools

| Group | Tools |
|---|---|
| Read | `list_project_files`, `read_file`, `search_in_files`, `analyze_text_file`, `find_todos`, `find_broken_links`, `generate_markdown_toc`, `git_lite` |
| Generate | `generate_project_report` (saves a file only if `save_as` is given) |
| Write | `write_note` (creates new files in `notes/` only), `str_replace` (edits existing files), `delete_file` (moves to `.trash/`) |

## Constraints every agent must respect

- `server.py` cannot be edited or deleted through the tools.
- `write_note` only creates new `.md` or `.txt` files in `notes/` and never overwrites. Update existing files with `str_replace`.
- `notes/`, `logs/`, and `.trash/` are git-ignored. `handoff/` is tracked.
- Only UTF-8 text files up to about 1 MB can be read. Search is plain text, not regex.
- The server has no login. Treat the public address as private (see D-006).
- Never write secrets (the ngrok authtoken, tokens, passwords) into any file in this project.
- Only one agent works at a time. There is no `if_version` locking, so concurrent edits can overwrite each other.

## Build history (from the git reflog, in order)

1. Initial commit: "Add workspace assistant MCP server". The branch was renamed from `master` to `main`.
2. Commit "added find_todos and find_broken_links".
3. Commit "added read_file, str_replace, delete_file, git_lite".
4. Commit "added Process Manager" on branch `process-manager`.
5. Branch `process-manager` was merged into `main` (the reflog shows `main` fast-forwarded to 8562201).
6. `handoff-protocol` branch created from `main`, then fast-forwarded to 8562201 with `pull origin main`.
7. Commit "added handoff files" on `handoff-protocol` (6c14a42), made by the user.

## Next steps (in order)

1. Delete the scratch file `handoff/_append_test.md` (created by the append test in CP-004; it could not be moved to `.trash/`, which does not exist yet).
2. Run the demo task in PLAN-002 across two separate sessions, using these handoff files to resume. Start with session A (first half).
3. Save the tool-call transcript of the demo in `handoff/transcripts/`.
4. Run `python test_tools.py` and record the result in CHECKPOINTS.md.
5. Write the report and README handoff section (PLAN-003).
6. Decide whether to merge `handoff-protocol` into `main` once the demo is done.

## Known issues

- No authentication on the public address (see D-006).
- Test results have not been recorded since the process manager was added (see next step 4).
- Claude Desktop's filesystem server timed out once (2 minutes, see CP-002). If it happens again, the tools may be unavailable for that session.
- The built-in `str_replace` tool cannot use Windows paths in this environment. Use the filesystem `edit_file` tool for handoff log appends.
- `.trash/` does not exist yet, so `delete_file` may fail until it is created.

## Last session

- **Agent:** Claude, session 1
- **Did:** created the handoff protocol and seeded it from the README, code, and git reflog; corrected earlier wrong claims; user committed the files (CP-003); tested the append method and corrected the protocol (CP-004).
- **Resume from:** CP-004 in CHECKPOINTS.md, then PLAN-002 step 2.

---

# Handoff protocol

Four files in `handoff/` keep work continuous between sessions and agents:

| File | Purpose | How it changes |
|---|---|---|
| `PROJECT_STATE.md` | Current status, constraints, next steps | Rewrite the sections you changed |
| `PLAN_LOG.md` | What was planned and what happened | Append only |
| `CHECKPOINTS.md` | Snapshots to resume from | Append only |
| `DECISIONS.md` | Why choices were made | Append only (change status, never delete) |

## At the start of a session

1. Read this file.
2. Read the latest entries of `CHECKPOINTS.md` and `PLAN_LOG.md`. Use `read_file` with `tail` or `head` to skip old entries.
3. Check `DECISIONS.md` before changing anything that has a recorded decision.
4. Run `git status` (or ask the user to) to see uncommitted changes.

## During a session

- Write a plan entry in `PLAN_LOG.md` before starting multi-step work.
- Record a decision in `DECISIONS.md` whenever you choose between real options.
- Add a checkpoint after each milestone and before any risky change.

## At the end of a session

1. Update **Current status**, **Next steps**, **Known issues**, and **Last session** in this file, and **Last updated** at the top.
2. Update the plan status in `PLAN_LOG.md`.
3. Add a final checkpoint with a clear **Resume from** note.

## How to append to a log file

Each log file ends with the line `<!-- APPEND NEW ENTRIES ABOVE THIS LINE -->`. Append with the filesystem tool `edit_file` (not the built-in `str_replace`, which does not accept Windows paths in this environment):

- `path`: the full Windows path of the log file
- `edits`: one edit with `oldText` set to the exact marker line, and `newText` set to your new entry, a blank line, then the same marker line again
- Set `dryRun` to `true` first if you want to preview the diff

The marker appears once per file, so the match is unique. Check the diff output shows the entry above the marker. If `edit_file` is not available, stop and tell the user rather than rewriting the whole log.

## Rules

- Never delete or rewrite earlier log entries. Correct a mistake by adding a new entry that refers to the old one by ID.
- IDs increase by one and are never reused: `PLAN-001`, `CP-001`, `D-001`.
- Put the date (YYYY-MM-DD) and the agent name in every entry.
- Keep entries short and factual. State what was verified and how, not what was expected.
