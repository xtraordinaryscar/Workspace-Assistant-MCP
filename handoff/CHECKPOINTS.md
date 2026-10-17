# CHECKPOINTS

Append only. Newest entries go above the marker line. Each checkpoint: ID, date, agent, state, what was verified and how, and a Resume from note.

---

## CP-002: Filesystem reconnect; handoff files written
- **Date:** 2026-10-17
- **Agent:** Claude, session 1
- **State:**
  - `handoff/` contains `PROJECT_STATE.md`, `PLAN_LOG.md`, `CHECKPOINTS.md`, and `DECISIONS.md`.
  - Branch `handoff-protocol` @ 8562201; handoff files not yet committed.
- **Verified:**
  - Git reflog read directly: commit history and branch moves match the Build history in PROJECT_STATE.
  - Filesystem tools reconnected after a 2-minute timeout in Claude Desktop (logs showed the server answered after the client had dropped the connection).
- **Not verified:** test suite result (`test_tools.py` not run in this session); the server's current running state.
- **Resume from:** PLAN-002 step 1, after running `git status` and committing the handoff files.

## CP-001: Handoff files drafted (superseded)
- **Date:** 2026-10-17
- **Agent:** Claude, session 1
- **State:** The first draft of `PROJECT_STATE.md` contained two unverified claims (a commit hash and branch status) and build dates that were not checked against git. These were corrected in CP-002 and PROJECT_STATE.md.
- **Resume from:** superseded by CP-002.

<!-- APPEND NEW ENTRIES ABOVE THIS LINE -->
