# Sprint 2: Monitor Hardening, Integration Tests, and Performance

**Created**: 2025-11-17
**Created By**: GitHub Copilot (GPT-5.1 Preview)
**Sprint Goal**: Harden VSCodeCopilotMonitor against real multi-window setups, formalize live monitor success criteria, and build the integration/performance testing harness.

---

## Objectives

1. Make VSCodeCopilotMonitor trustworthy in real-world multi-window environments.
2. Encode and enforce clear success criteria for live monitor runs (including screenshots).
3. Add the integration tests and performance benchmarks that were deferred from Sprint 1.

---

## Monitor Success Criteria (Must-Haves)

A live monitor run (e.g., `test_monitor_live.py`) only counts as a **pass** if all of the following are true:

### 1. VS Code Window Detection
- Only real VS Code windows are treated as VS Code targets.
- Non-VS Code apps (browsers, terminals, other screens) must not be included.
- The count and titles in the monitor results must match the actual visible VS Code windows.

### 2. Per-Window Independence
- Each window result reflects that specific window, not reused state from another window.
- For N VS Code windows, there are N distinct `title` values in results.
- In normal usage, `copilot_text_length` and `transcript_length` differ between windows that show different chats.

### 3. Copilot Text Extraction
- `copilot_text_length` is:
  - Zero only when there is genuinely no Copilot Chat visible, and
  - Non-zero when Copilot Chat text is visible in the screenshot.
- The extracted text corresponds to the Copilot Chat region in the screenshot (not random UI text).
- Repeated runs on an unchanged chat produce stable copilot text and lengths; changes in chat yield meaningful diffs.

### 4. Transcript Capture
- `transcript_length` is non-zero whenever “Copy All” (or equivalent) is invoked on a chat with history.
- Clipboard content matches what a user would get by manually triggering “Copy All” in that window.
- Different windows with different chats produce different transcripts; identical transcripts across windows are only acceptable when the UI state is actually identical.

### 5. Diff Logic
- `text_diff` and `transcript_diff` are empty when there are no real changes between runs on the same window.
- When the chat content changes, diffs reflect those real textual changes (new responses, edited prompts, etc.).
- Within a single live test:
  - The initial pass may show large diffs (empty → populated).
  - Subsequent passes on unchanged windows show minimal or no diffs.

### 6. Busy / Ready Detection
- `is_busy` is **not** always `True`:
  - Idle Copilot (no spinner/status) must be reported as `False` for `is_busy`.
  - Active generation (spinners, “Thinking…”, similar indicators) should be reported as `True`.
- The heuristic (keywords + diff size) must not continuously classify stable screens as busy.

### 7. Multi-Window Sequencing
- The monitor focuses each VS Code window in turn and fetches a **fresh** state per window.
- Symptoms to avoid:
  - Identical metrics for different windows that clearly show different content.
  - Logs suggesting only one `State-Tool` response was reused for all windows.

### 8. Logging
- Every live run produces a log file under `logs/` with:
  - MCP session lifecycle entries.
  - A record of each `State-Tool` call.
  - Per-window summaries (title, `is_busy`, lengths, diff sizes).
  - Errors and warnings for tool failures (state, click, clipboard, etc.).
- Logs are sufficient to debug misclassified windows, missing Copilot text, busy logic errors, and per-window sequencing issues.

### 9. Screenshots
- Each live test run must produce screenshots saved under a timestamped directory, e.g., `logs/screenshots/YYYYMMDD_HHMMSS/`.
- At minimum:
  - One pre-run desktop screenshot.
  - One screenshot per VS Code window after focus.
- Filenames encode window index/title and phase, e.g., `pre_run.png`, `win1_focused.png`, `win2_focused.png`.
- Paths to these screenshots are logged so they can be correlated with monitor output.

### 10. Test Harness Expectations
- `test_monitor_live.py` (or its successor):
  - Prints a summary of windows, busy state, lengths, and diff sizes.
  - Exits cleanly without requiring `taskkill` in the happy path.
  - Optionally persists a JSON summary for automated checks.

---

## Sprint 2 Work Items

1. **Monitor hardening**
   - Refine VS Code window filtering (avoid other displays/apps).
   - Ensure per-window state refresh and unique metrics.
   - Re-tune `is_busy` logic using real-world sessions.

2. **Screenshot capture**
   - Extend monitor or live test to capture and save screenshots as described.
   - Wire screenshot paths into logs.

3. **Integration tests**
   - Implement the real VS Code integration scenarios from Sprint 1’s plan.
   - Use the monitor success criteria above as acceptance tests.

4. **Performance benchmarks**
   - Measure and document focus times, chat open/copy times, reasoning latency, and full-cycle timings.

5. **Docs & plan updates**
   - Keep `ARCHITECTURE.md`, `README.md`, and this file aligned with actual behavior.
