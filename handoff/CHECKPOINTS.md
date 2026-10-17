# CHECKPOINTS

Append only. Newest entries go above the marker line. Each checkpoint: ID, date, agent, state, what was verified and how, and a Resume from note.

---

## CP-003: Handoff files committed
- **Date:** 2026-10-17
- **Agent:** Claude, session 1 (commit made by the user)
- **State:**
  - Branch `handoff-protocol` @ 6c14a42 ("added handoff files"), one commit ahead of `main` @ 8562201.
  - Files committed: `handoff/PROJECT_STATE.md`, `PLAN_LOG.md`, `CHECKPOINTS.md`, `DECISIONS.md`.
- **Verified:** git reflog shows the commit on `handoff-protocol`.
- **Not verified:** `handoff/` is in the commit's file list (the reflog does not list files); `test_tools.py` not run.
- **Resume from:** PLAN-002 step 1 (run the first half of the demo task in session A).

## CP-002: Filesystem reconnect; handoff files written
- **Date:** 2026-10-17
- **Agent:** Claude, session 1
- **State:**
  - `handoff/` contains `PROJECT_STATE.md`, `PLAN_LOG.md`, `CHECKPOINTS.md`, and `DECISIONS.md`.
  - Branch `handoff-protocol` @ 8562201; handoff files not yet committed at the time of this checkpoint.
- **Verified:**
  - Git reflog read directly: commit history and branch moves match the Build history in PROJECT_STATE.
  - Filesystem tools reconnected after a 2-minute timeout in Claude Desktop (logs showed the server answered after the client had dropped the connection).
- **Not verified:** test suite result (`test_tools.py` not run in this session); the server's current running state.
- **Resume from:** superseded by CP-003.

## CP-001: Handoff files drafted (superseded)
- **Date:** 2026-10-17
- **Agent:** Claude, session 1
- **State:** The first draft of `PROJECT_STATE.md` contained two unverified claims (a commit hash and branch status) and build dates that were not checked against git. These were corrected in CP-002 and PROJECT_STATE.md.
- **Resume from:** superseded by CP-002.

## CP-004: Append method tested and protocol corrected
- **Date:** 2026-10-17
- **Agent:** Claude, session 1
- **State:**
  - The built-in `str_replace` cannot use Windows paths here, so the protocol now names filesystem `edit_file` for appends.
  - `edit_file` appended an entry above the marker line in a scratch file and kept the marker in place.
  - `PROJECT_STATE.md` rewritten with the corrected protocol.
- **Verified:** `edit_file` dry run and real edit both produced the expected diff (entry above the marker).
- **Not verified:** the append method on the real log files (this file is the first real use; check the diff on the next append).
- **Cleanup pending:** `handoff/_append_test.md` should be deleted. `move_file` to `.trash/` failed because `.trash/` does not exist.
- **Resume from:** PLAN-002 step 2 (session A of the demo task).

## CP-005: Correction to CP-004
- **Date:** 2026-10-17
- **Agent:** Claude, session 1
- **Correction:** CP-004 says `edit_file` dry run and real edit both produced the diff. Only the real edit (`dryRun: false`) was run; no dry run was done. The real edit's diff showed the entry above the marker.
- **Resume from:** same as CP-004.

<!-- APPEND NEW ENTRIES ABOVE THIS LINE -->
