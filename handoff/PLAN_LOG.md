# PLAN_LOG

Append only. Newest entries go above the marker line. Each entry: ID, date, agent, goal, steps, status, and outcome.

---

## PLAN-001: Create the handoff protocol
- **Date:** 2026-10-17
- **Agent:** Claude, session 1
- **Goal:** Create the four handoff files so work can continue across sessions and agents (midterm requirement 04).
- **Steps:**
  1. Create `handoff/` folder. Done.
  2. Write `PROJECT_STATE.md` with the protocol. Done.
  3. Write `PLAN_LOG.md`, `CHECKPOINTS.md`, `DECISIONS.md`. Done.
  4. Commit the files on `handoff-protocol`. Pending (see PROJECT_STATE next steps).
- **Status:** Mostly complete; commit pending
- **Outcome:** Filesystem tool timed out once during step 2 (see CP-002). Resumed after reconnect.

## PLAN-002: Multi-step demo task across 2 or more sessions
- **Date:** 2026-10-17
- **Agent:** Claude, session 1 (plan only)
- **Goal:** Satisfy requirement 05: run one real multi-step task with a real MCP client across at least two separate sessions, and record it.
- **Proposed task:** Create a short project audit, for example: list files, find TODOs, check broken links in the README, write the findings to a new file in `notes/`, then in a later session update the file with `str_replace` and check that the handoff files alone were enough to resume.
- **Steps:**
  1. Session A: run the first half. Write a checkpoint before stopping.
  2. Session B: start only from the handoff files. Record whether any information had to be asked again.
  3. Save the tool-call transcript to `handoff/transcripts/`.
- **Status:** Planned, not started

## PLAN-003: Report and README handoff section
- **Date:** 2026-10-17
- **Agent:** Claude, session 1 (plan only)
- **Goal:** Satisfy requirement 06 and the README deliverable.
- **Steps:**
  1. Add a "Design choices and tradeoffs" section to the report (soft delete, new-files-only writes, ngrok with `.bat` watchdogs, no authentication).
  2. Add a short handoff section to the README.
  3. Keep the report short and factual.
- **Status:** Planned, not started

<!-- APPEND NEW ENTRIES ABOVE THIS LINE -->
