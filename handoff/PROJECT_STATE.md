# PROJECT_STATE

> **Read this file first at the start of every session.** It is the single source of truth for where the project stands. The rules for this file and the other three handoff files are in "Handoff protocol" at the end.

**Project:** workspace-assistant, an MCP file-server connector (Python, `mcp` SDK, streamable HTTP)
**Root:** `mcp-server/` (the sandbox; the tools cannot reach anything outside it)
**Last updated:** 2026-10-17 by Claude (session 4)
**Branch and commit at last update:** `handoff-protocol` @ 6c14a42 ("added handoff files"), plus later uncommitted handoff edits (CP-004 to CP-009, PLAN_LOG updates, `notes/audit-session-a.md`, `handoff/transcripts/`). Check `git status`.

## Current status

**Working (per code and README read in session 1)**
- 12 tools in `server.py`, all paths resolved through `safe_path()`
- Tests in `test_tools.py` (last recorded run result: none; see Known issues)
- Server on `127.0.0.1:8000`, public HTTPS through an ngrok fixed domain (set at the top of `run-tunnel.bat`)
- Process management: `run-server.bat` and `run-tunnel.bat` restart on crash, `start-all.bat` launches both, `check-status.bat` checks both (HTTP 406 from each address means it is up; HTTP 000 locally means the server is down, HTTP 502 publicly means the tunnel is up but the server is not)
- Connected to Claude Desktop, and to claude.ai as the custom connector "Lazaro's MCP" (the user's own server; the name is the user's choice)
- `notes/test-note.md` shows a successful write from a real client

**Done**
- Handoff protocol created in `handoff/` and committed (CP-003)
- Append method verified (CP-004, corrected in CP-005)
- PLAN-002 complete (CP-006 to CP-009): session A audit (`handoff/audit-session-a.md`, moved from `notes/` so git tracks it), session B re-check and transcript (`handoff/transcripts/plan-002-session-b-tool-calls.md`). Session B resumed from the handoff files with no questions to the user.
- Protocol fixes for the findings in CP-009
- PLAN-003 complete: documentation PDF (report, design choices, handoff section; submitted separately, not in the repo) and README handoff section (CP-013)
- Ngrok domain moved to the ignored local file `ngrok-domain.txt` (D-007)

**Not done**
- 5-minute live demo: not planned (the user decided not to run it; see CP-015)
- Stretch goals (optional, not planned): `if_version` locking, `search_code`, repo map, token auth
- Session A transcript (not saved; accepted by the user, see CP-012)
- Raw session B transcript is not saved in raw form (the file in `handoff/transcripts/` is a summary); see CP-015

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
8. Later handoff commits by the user (protocol fix, PLAN_LOG block note).

## Next steps (in order)

1. Commit any uncommitted handoff changes (check `git status` first).
2. Optional: if the user wants the raw session B transcript, copy it from claude.ai into `handoff/transcripts/`.
3. Otherwise the project is complete; the live demo is not planned (CP-015).

## Known issues

- No authentication on the public address (see D-006).
- Test results have not been recorded since the process manager was added (next step 4).
- Claude Desktop's filesystem server timed out once (2 minutes, see CP-002). If it happens again, the tools may be unavailable for that session.
- The built-in `str_replace` tool cannot use Windows paths. In the filesystem environment, use `edit_file` for appends. In the claude.ai connector environment, use the connector's `str_replace`. See the protocol.
- `delete_file` may fail until `.trash/` is created. The filesystem tools cannot create it; create it manually or accept that deletes fail.

## Last session

- **Agent:** Claude, session 4
- **Did:** confirmed the final state; moved the audit note into `handoff/`; updated the documentation PDF (title, name, handoff section, domain text); closed PLAN-003 (CP-013); recorded that the live demo will not happen (CP-015); saved the session C raw transcript; aligned the next steps with CP-015.
- **Resume from:** CP-015 in CHECKPOINTS.md. The project is otherwise complete.

---

# Handoff protocol

Four files in `handoff/` keep work continuous between sessions and agents:

| File | Purpose | How it changes |
|---|---|---|
| `PROJECT_STATE.md` | Current status, constraints, next steps | Rewrite the sections you changed |
| `PLAN_LOG.md` | What was planned and what happened | Append only |
| `CHECKPOINTS.md` | Snapshots to resume from | Append only |
| `DECISIONS.md` | Why choices were made | Append only (change status, never delete) |

Supporting folders: `handoff/transcripts/` holds saved tool-call transcripts.

## At the start of a session

1. Read this file.
2. Read the latest entries of `CHECKPOINTS.md` and `PLAN_LOG.md`. Use `read_file` with `tail` or `head` to skip old entries.
3. Check `DECISIONS.md` before changing anything that has a recorded decision.
4. Check `git status` (or ask the user to) to see uncommitted changes.
5. Check which write tools you have (see "Write tools by environment" below). If the one you need is missing, stop and tell the user before using any other tool.

## During a session

- Write a plan entry in `PLAN_LOG.md` before starting multi-step work.
- Record a decision in `DECISIONS.md` whenever you choose between real options.
- Add a checkpoint after each milestone and before any risky change.

## At the end of a session

1. Update **Current status**, **Next steps**, **Known issues**, and **Last session** in this file, and **Last updated** at the top.
2. Update the plan status in `PLAN_LOG.md`.
3. Add a final checkpoint with a clear **Resume from** note.

## Write tools by environment

| Environment | Append to logs | Edit existing file | Create folder |
|---|---|---|---|
| Filesystem server (Claude Desktop) | `edit_file`, `path` = full Windows path | `edit_file` | `create_directory` |
| claude.ai connector "Lazaro's MCP" | connector `str_replace` on the marker line | connector `str_replace` | none; ask the user |

If the write tool you need is not in your tool list, do not substitute a different tool silently. Tell the user which tool is missing and wait for a decision.

## How to append to a log file

Each log file ends with the line `<!-- APPEND NEW ENTRIES ABOVE THIS LINE -->`. Use the append tool for your environment (see the table above). Set the edit so that `oldText` is the exact marker line, and `newText` is your new entry, a blank line, then the same marker line again. The marker appears once per file, so the match is unique. Check the result shows the entry above the marker. Never rewrite a whole log file to add an entry.

## Missing folders

If a folder the protocol names (for example `handoff/transcripts/`) does not exist and your tools cannot create it, stop and ask the user to create it. Do not save the file somewhere else without asking. If the user prefers, the transcript can go in `notes/`, and the checkpoint should say where it was saved.

## Rules

- Never delete or rewrite earlier log entries. Correct a mistake by adding a new entry that refers to the old one by ID.
- IDs increase by one and are never reused: `PLAN-001`, `CP-001`, `D-001`.
- Put the date (YYYY-MM-DD) and the agent name in every entry.
- Keep entries short and factual. State what was verified and how, not what was expected.
