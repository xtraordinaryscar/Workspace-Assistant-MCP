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

## PLAN-002 update: session A blocked (2026-10-17, Claude, session 1)
- **Status:** Blocked. Not started.
- **Reason:** The demo must run through the `workspace-assistant` connector (requirement 05: real MCP client). In this chat the filesystem tools are available, but the workspace-assistant tools are not in the tool list.
- **Not done:** no audit was run and no notes were written. Running the same audit with the filesystem tools would not satisfy requirement 05.
- **Next:** open the workspace-assistant connector in claude.ai (Settings > Connectors) and confirm it is enabled for this chat; make sure the server and ngrok tunnel are running (`start-all.bat`, then `check-status.bat`). Start a new chat and use the connector's tools for session A.

## PLAN-002 update: session A done (2026-10-17, Claude, session 2)
- **Status:** Session A complete. Counts toward requirement 05.
- **Connector:** the user's custom MCP connector, named "Lazaro's MCP" in claude.ai. It is the user's own server (the user confirmed this); the name differs from `workspace-assistant` by the user's choice. The URL was not checked by the agent.
- **Result:** `notes/audit-session-a.md` written; checkpoint CP-006. Findings: 17 project files, 16 marker hits (none are open work items), 1 intentional broken link (`nope.md` in the README demo prompt).
- **Next:** session B, in a new chat, using only the handoff files and `notes/audit-session-a.md`. Use the same connector.

## PLAN-002 update: step 5 done (2026-10-17, Claude, session 3)
- **Status:** Complete. Audit finished in session B.
- **Connector:** "Lazaro's MCP", same as session A.
- **Result:** Re-ran the TODO scan (19 hits in 13 files; the increase is the audit note itself) and the README broken-link check (1 intentional break, `nope.md`). No open work items. Recorded in `notes/audit-session-a.md`, section 6.
- **Not verified:** `test_tools.py` not run; `logs/` not reviewed. Transcript not yet saved to `handoff/transcripts/`.
- **Next:** save the tool-call transcript (PLAN-002 step 3), then PLAN-003.

## PLAN-002 update: complete (2026-10-17, Claude, session 3)
- **Status:** Complete. Session B resumed from the handoff files and finished the audit without asking the user for anything the files contain.
- **Step 3 (transcript):** saved to `handoff/transcripts/plan-002-session-b-tool-calls.md`. The folder was created in session 3 because it did not exist.
- **Findings:** recorded in CP-009 (protocol deviation: `edit_file` not available in session B, `str_replace` used without asking; gap: no rule for a missing transcript folder).
- **Next:** PLAN-003 (report and README handoff section), after the protocol fixes in CP-009.

<!-- APPEND NEW ENTRIES ABOVE THIS LINE -->

