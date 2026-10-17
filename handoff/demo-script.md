# Live demo script (5 minutes)

Use "Lazaro's MCP" in claude.ai. Run these steps in order in a single new chat. Do not retry a step silently: if a step fails, say so and note the error.

## Before the demo (not timed)

1. Run `start-all.bat`, then `check-status.bat`. Both lines must show HTTP 406. If the local line shows 000, the server is down: run `start-all.bat` again after stopping old processes.
2. In claude.ai, confirm "Lazaro's MCP" is enabled for the chat.

## The demo (about 3 minutes)

| Step | Prompt | What the audience should see |
|---|---|---|
| 1 | "List the files in the project root." | A file list from `list_project_files` |
| 2 | "Create a note called `demo.md` in notes/ containing the line `TODO: write the tests` and the link `[missing](nope.md)`." | `write_note` creates the file |
| 3 | "Find all TODO, FIXME and NOTE markers in the project." | The new TODO appears in `notes/demo.md`, among others |
| 4 | "Check `notes/demo.md` for broken links." | `nope.md` reported as broken |
| 5 | "In `notes/demo.md`, replace `TODO: write the tests` with `DONE: tests written`." | `str_replace` succeeds: one match |
| 6 | "Analyze `..\hello.txt`." | Refused: "outside the allowed folder" |
| 7 | "Delete `notes/demo.md`." | The file moves to `.trash/`, not erased |

## Explain while it runs (about 2 minutes)

- **Sandbox:** step 6 shows every path is checked against the project folder.
- **Soft delete:** step 7 moves the file, so nothing is erased for good.
- **Limits:** there is no login. The public address must stay private, and the tunnel stays off when not in use.
- **Handoff:** show `handoff/PROJECT_STATE.md` and the latest entry in `handoff/CHECKPOINTS.md`, and explain that a new session resumes from them.

## After the demo

1. Save the chat transcript to `handoff/transcripts/demo-session.md`.
2. Add a checkpoint to `handoff/CHECKPOINTS.md` recording which steps passed and any that failed.

## If something fails

- **Step 1 fails with "not available":** the connector dropped for this chat. Start a new chat and ask only for step 1.
- **Server shows 000 or 502:** the server is down. Check Task Manager for `python.exe` and `ngrok.exe`, then restart with `start-all.bat`.
- **Step 7 fails:** `.trash/` may not exist. Say so, then continue; the other steps still show the tool works.
