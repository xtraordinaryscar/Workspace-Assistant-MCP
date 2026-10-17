# DECISIONS

Append only. Newest entries go above the marker line. Never delete a decision; change its status instead.

Status values: **Accepted**, **Superseded by D-XXX**, **Revisit**.

---

## D-006: No authentication on the public address
- **Date:** 2026-10-17
- **Agent:** Claude, session 1 (recorded from the existing project design)
- **Status:** Accepted, with a known risk
- **Context:** The server uses a fixed ngrok domain. Anyone with the address can call the tools, including write and delete tools, while the tunnel is running.
- **Decision:** Keep the server unauthenticated for the course demo. Keep the address private and stop the services when not in use.
- **Consequences:** Acceptable for a supervised demo only. Token auth is the top stretch goal (Revisit).

## D-005: Use ngrok with `.bat` watchdogs instead of a cloud deployment
- **Date:** 2026-10-17
- **Agent:** Claude, session 1 (recorded from the existing project design)
- **Status:** Accepted
- **Context:** The brief requires HTTPS through a tunnel and a process manager.
- **Decision:** ngrok provides a fixed HTTPS domain. `run-server.bat` and `run-tunnel.bat` restart their programs after a crash, and `start-all.bat` starts both.
- **Consequences:** The watchdogs run only while the user is logged in. Restart loops hide bugs, so the logs must be checked.

## D-004: `write_note` creates new files only; updates use `str_replace`
- **Date:** 2026-10-17
- **Agent:** Claude, session 1 (recorded from the existing project design)
- **Status:** Accepted
- **Context:** Overwriting files without warning can lose work, including handoff logs.
- **Decision:** `write_note` uses exclusive-create mode and only writes to `notes/`. Edits to existing files go through `str_replace`, which requires a unique match.
- **Consequences:** Agents must append log entries with `str_replace` against the marker line.

## D-003: Soft delete to `.trash/`
- **Date:** 2026-10-17
- **Agent:** Claude, session 1 (recorded from the existing project design)
- **Status:** Accepted
- **Context:** Permanent deletion through an AI tool is hard to undo.
- **Decision:** `delete_file` moves files into `.trash/` with a timestamp prefix. Folders cannot be deleted.
- **Consequences:** `.trash/` grows over time and needs manual cleanup.

## D-002: `git_lite` allows only status, log, and diff, with no shell
- **Date:** 2026-10-17
- **Agent:** Claude, session 1 (recorded from the existing project design)
- **Status:** Accepted
- **Context:** Running arbitrary shell commands through a remote tool would be a serious risk.
- **Decision:** Only three fixed git subcommands are accepted, run without a shell.
- **Consequences:** Other git operations (commit, merge) must be done by the user in a terminal.

## D-001: Protect `server.py` from the tools
- **Date:** 2026-10-17
- **Agent:** Claude, session 1 (recorded from the existing project design)
- **Status:** Accepted
- **Context:** An agent that can edit the server could change its own rules.
- **Decision:** `str_replace` and `delete_file` refuse to touch `server.py`.
- **Consequences:** The server must be edited by the user directly.

## D-007: Keep the ngrok domain out of tracked files
- **Date:** 2026-10-17
- **Agent:** Claude, session 3
- **Status:** Accepted
- **Context:** The repository is public, and the ngrok domain was in `run-tunnel.bat`, `check-status.bat` and `README.md`. The server has no login, so the domain makes the server easier to find and use.
- **Decision:** The domain is read from `ngrok-domain.txt`, which is listed in `.gitignore`. The tracked files show a placeholder.
- **Consequences:** The domain is still in earlier commits, so this change does not remove it from history. Removing it would need a new reserved ngrok domain, or a rewrite of git history, which the user has not chosen. The local `ngrok-domain.txt` must be created on each machine that runs the scripts.

<!-- APPEND NEW ENTRIES ABOVE THIS LINE -->
