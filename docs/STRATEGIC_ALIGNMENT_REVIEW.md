# Strategic Alignment Review & Fix Plan

## Current State Analysis

### Problem: Duplicate Automation Paths

**Path 1: LangGraph Main Flow (BROKEN)**
- Entry: `agent-cli run-once` 
- Flow: ScanRepos → SyncPlan → ReasonStep → **ActStep** → ValidateEvidence → Persist
- ActStep uses: `StdioMCPAdapter` or `MCPAdapter` (base desktop adapter)
- Method: Blind keyboard shortcuts (Ctrl+A, Ctrl+C) - **DOESN'T WORK for Copilot Chat**

**Path 2: VSCodeCopilotMonitor (WORKS but UNUSED)**
- Entry: `python test_monitor_live.py` (test only)
- Tool: `agent/tools/vscode_copilot_monitor.py`
- Method: 
  - Parses State-Tool textual output
  - Finds "Copy All" button visually
  - Clicks it
  - Uses PowerShell Get-Clipboard
  - **THIS WORKS**

### Root Cause

**ActStep never calls VSCodeCopilotMonitor**. It uses generic adapter methods that don't understand Copilot Chat UI.

## Strategic Goals (from PILLARS.md)

1. ✅ **LangGraph Multi-Agent** - Have this
2. ✅ **Auto-Resume & Unsticking** - Have watchdog
3. ⚠️ **Desktop Control via MCP** - Have MCP but wrong usage
4. ⚠️ **Multi-VS Code Window Awareness** - VSCodeCopilotMonitor does this, ActStep doesn't use it
5. ❌ **Copilot Chat Management** - BROKEN: Can't copy transcripts
6. ✅ **Repo & PR Scanning** - Works
7. ⚠️ **Minimal Custom Tooling** - Have VSCodeCopilotMonitor but not using it
8. ✅ **Flexible Interface** - Have TaskEnvelope
9. ✅ **Observability** - Have episodes/spans
10. ✅ **Safety** - Have dry-run mode

## The Fix: Integrate VSCodeCopilotMonitor into ActStep

### Option A: Replace ActStep Logic (RECOMMENDED)

**Remove:**
- `_copy_chat_context()` using Ctrl+C
- `_post_to_chat()` using Ctrl+V

**Add:**
- Use `VSCodeCopilotMonitor.check_all_windows()` in ActStep
- Extract Copilot text from monitor results
- Post messages via monitor's click + type approach

**Benefits:**
- Uses proven working code
- Vision-guided (State-Tool textual parsing)
- Handles multi-window correctly
- Detects busy state

### Option B: Port Monitor Logic to Adapter

**Create:**
- `CopilotAdapter` that wraps `StdioMCPAdapter`
- Implements Copilot-specific methods:
  - `get_copilot_transcript()` - uses "Copy All" button
  - `post_copilot_message()` - clicks chat input + types
  - `is_copilot_busy()` - checks textual diff

**Benefits:**
- Keeps adapter abstraction clean
- Reusable across ActStep/ValidateEvidence
- Maintains separation of concerns

### Option C: Minimal Patch (QUICK FIX)

**Change ActStep to:**
```python
async def act_step(state: Dict[str, Any]) -> Dict[str, Any]:
    from agent.tools.vscode_copilot_monitor import VSCodeCopilotMonitor
    
    # Use monitor instead of blind automation
    monitor = VSCodeCopilotMonitor()
    results = await monitor.connect()
    
    # Find target repo window
    target_repo = envelope.get("target_repo_path")
    for result in results:
        if target_repo in result.get("title", ""):
            transcript = result.get("transcript_diff")
            # ... use transcript
```

**Benefits:**
- Minimal code change
- Uses working approach immediately

**Drawbacks:**
- Async/sync mismatch (ActStep is sync, monitor is async)
- Doesn't fit adapter pattern

## Recommended Action Plan

**Phase 1: Immediate Fix (Today)**
1. Make ActStep call VSCodeCopilotMonitor
2. Handle async properly
3. Remove Ctrl+C blind automation
4. Test end-to-end with `agent-cli run-once`

**Phase 2: Refactor (Next Session)**
1. Create `CopilotAdapter` class
2. Move monitor logic into adapter
3. Update ActStep to use new adapter
4. Add vision-guided click detection

**Phase 3: Vision Enhancement (Future)**
1. Use GLM-4.5V to locate UI elements
2. Eliminate hardcoded coordinates
3. Add adaptive retry with vision feedback

## Questions to Answer

1. **Should ActStep be async?** Monitor requires async, ActStep is sync
2. **Keep two separate tools?** Or merge VSCodeCopilotMonitor into ActStep?
3. **Adapter abstraction?** Should Copilot-specific logic be in adapter or node?

## Current Broken Points

- [ ] ActStep `_copy_chat_context()` uses Ctrl+C - doesn't work
- [ ] ActStep `_post_to_chat()` uses Ctrl+V - may not work reliably
- [ ] Vision integration added but not tested
- [ ] Recovery routing works but never triggers (nothing fails)

## What Actually Works

- [x] VSCodeCopilotMonitor finds VS Code windows
- [x] VSCodeCopilotMonitor extracts Copilot text via State-Tool
- [x] VSCodeCopilotMonitor uses "Copy All" button
- [x] VSCodeCopilotMonitor detects busy state
- [x] State-Tool plain text parsing
- [x] Windows-MCP stdio connection
