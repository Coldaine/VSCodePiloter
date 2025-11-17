# Canonical Architecture (Nov 2025)

This is the primary, guiding document for how the system runs. It establishes the canonical flow and clarifies that ActStep (x-step) operates synchronously, invoking the VSCodeCopilotMonitor once per cycle. Async is optional and not required for correctness.

## Core Principles
- Synchronous ActStep: one monitor/tool pass per LangGraph cycle; deterministic ordering and simpler debugging.
- Propose → Verify → Execute: preserve the two-phase guardrail around any desktop action.
- Reuse-first: use Windows-MCP via stdio and the `VSCodeCopilotMonitor` to harvest transcript and detect busy state.
- Vision-gated validation: post-action screenshot goes to `glm-4.5v`; failure routes to Recovery with bounded retries.

## End-to-End Flow (ASCII)

```
Start → SCAN_REPOS → SYNC_PLAN → REASON_STEP
       → ACT_STEP (Sync, uses VSCodeCopilotMonitor)
       → VALIDATE_EVIDENCE (Vision + structure)
         ├─ Success → PERSIST → End/Next Cycle
         └─ Failure → RECOVERY → (retry or end)
```

Detailed ACT_STEP (synchronous):
- Invoke `VSCodeCopilotMonitor`:
  - Enumerate VS Code windows (State-Tool)
  - Focus target window
  - Open Copilot Chat (palette)
  - Copy-All transcript (Clipboard-Tool)
- Pre-verify (optional): quick vision/state sanity check
- Decide action (from ReasonStep + transcript)
- Execute nudge (write-mode gated)
- Capture screenshot (after)
- Emit artifacts: transcript, before/after screenshots

Async is only needed if you introduce continuous telemetry or parallel long-latency tasks. For the current product goals, keep it sync.

---

# System Architecture Documentation

## System Status: Sprint 1 - Canonical Flow Established ✅

### Implementation Progress

| Component | Status | Implementation Details |
|-----------|--------|------------------------|
| **LLM Integration** | ✅ Implemented | Z.ai GLM-4.6 for text reasoning, GLM-4.5V for vision |
| **Reasoner Agent** | ✅ Implemented | GLM-4.6-powered intelligent task prioritization |
| **Vision Capabilities** | ✅ Implemented | GLM-4.5V for screenshot analysis and validation |
| **Secret Management** | ✅ Implemented | Bitwarden Secrets Manager + environment variable fallback |
| **Recovery Node** | ✅ Implemented | Wired into graph flow with conditional routing from ActStep |
| **Retry Logic** | ⚠️ Pending | No retry mechanism in MCP adapter |
| **Screenshot Validation** | ✅ Implemented | Vision integrated in ValidateEvidence; routes to Recovery on failure |

### LLM Architecture

**Text Model (Reasoning)**: Z.ai GLM-4.6
- Model: 355B total parameters (MoE), 32B active parameters
- Analyzes repository health (branches, PRs, activity)
- Intelligently prioritizes tasks based on team context
- Generates contextual messages for Copilot Chat
- Temperature: 0.7 (deterministic reasoning)
- Endpoint: `https://api.z.ai/api/coding/paas/v4/` (coding plan subscription)
- Context: 200K tokens
- Streaming: Enabled

**Vision Model (Screenshot Analysis)**: Z.ai GLM-4.5V
- Model: 106B total parameters (MoE), 12B active parameters
- Analyzes VS Code window screenshots
- Validates Copilot Chat state (open/busy/responsive)
- Verifies action completion
- Detects UI state for error recovery
- Temperature: 0.95 (creative interpretation)
- Endpoint: `https://api.z.ai/api/paas/v4/` (standard API, pay-as-you-go)
- Context: 64K-66K multimodal tokens
- Streaming: Disabled
- **CRITICAL**: Vision models do NOT work with coding endpoint

**Secret Management**: Auto-detecting composite provider
- Local dev: Bitwarden Secrets Manager (`bws` CLI)
- CI/CD: Environment variables
- Fallback: `.env` file or direct env vars

## Testing Requirements

### CRITICAL: No Mocks or Stubs for Acceptance Testing

**All acceptance tests MUST use real components**:
- ✅ Live MCP server or actual desktop automation
- ✅ Real VS Code instances with GitHub Copilot Chat
- ✅ Actual git repositories (not test fixtures)
- ✅ Live LLM API calls (not cached responses)
- ✅ Real window focus and interaction

**Mocked tests are worthless** for a desktop automation system. It's like testing a parachute without jumping.

### Required Integration Test Scenarios

1. **End-to-end VS Code interaction** - Full Copilot Chat cycle with real windows
2. **Multi-window orchestration** - Correct window selection from 3+ instances
3. **VSCodeCopilotMonitor integration** - Real Windows-MCP session scanning multiple VS Code windows, detecting busy states, capturing transcripts
4. **Error recovery flow** - Intentional failures triggering Recovery node
5. **LLM reasoning validation** - Complex plans with priority-based selection
6. **Watchdog resumption** - Automatic restart after interruption
7. **Stdio MCP adapter** - Launch Windows-MCP subprocess, verify JSON-RPC communication, confirm tool calls work

### Performance Benchmarks (Real-World Required)
- Window focus: <500ms
- Copilot Chat open: <2s
- Chat content copy: <1s
- LLM reasoning: <3s
- Full work item: <10s

## Overview
This system implements a multi-agent LangGraph orchestration for supervising, driving, and recovering multiple VS Code windows on Windows 11 using MCP desktop automation.

## High-Level Components
- **Reasoner Agent**: Maintains long-term intent, selects task envelopes, coordinates repo and plan state.
- **Vision Actor Agent**: Executes GUI automation via MCP; fresh context each invocation.
- **MCP Desktop Adapter**: Stdio or HTTP transport layer to Windows automation servers (Windows-MCP).
- **VSCodeCopilotMonitor**: High-level wrapper around Windows-MCP for monitoring VS Code Copilot Chat across multiple windows, tracking transcripts, and detecting busy states.
- **LangGraph Application**:
  - Nodes: ScanRepos → SyncPlan → ReasonStep → ActStep → ValidateEvidence → Persist
  - Checkpoints stored in SQLite
- **Watchdog**: Periodic auto-resume loop detecting stalls and forcing recovery.

## Data Flow
1. **ScanRepos**: Reads git/gh info for every repo.
2. **SyncPlan**: Loads plan.yaml → maps repos → produces work items.
3. **ReasonStep**: Chooses next work item → builds TaskEnvelope.
4. **ActStep**:
   - Find correct VS Code window via MCP
   - Focus window
   - Open Copilot Chat (palette command)
   - Screenshot before
   - Copy chat context
   - Optionally post nudge message
   - Screenshot after
5. **ValidateEvidence**: Ensures screenshots and copied context exist.
6. **Persist**: Stores run trace + artifacts, updates heartbeat.
7. **Watchdog**: If heartbeat stagnant, run recovery or re-invoke the graph.

## Recently Completed Components (Sprint 1)

### ✅ 1. LLM Integration
- **GLM-4.6 client**: Fully integrated via `langchain-openai`
- **Reasoner prompts**: `reasoner_system.txt` now actively used
- **Intelligent prioritization**: Repository health analysis with LLM reasoning
- **Streaming support**: Enabled for real-time responses
- **Secret management**: Bitwarden integration for secure API key storage

### ✅ 2. Vision Capabilities
- **GLM-4.5V integration**: Vision model client implemented
- **Screenshot encoding**: Base64 encoding with automatic resizing
- **Vision message formatting**: OpenAI-compatible vision API format
- **Helper functions**: `create_vision_message()`, `encode_image_to_base64()`
- **Configuration**: Vision settings in `config.yaml` with enable/disable toggle

### ✅ 3. Secret Management
- **Auto-detection**: Environment-aware provider selection
- **Bitwarden provider**: Full `bws` CLI integration
- **Composite provider**: Chains multiple secret sources
- **Fallback chain**: Bitwarden → .env → environment variables
- **Caching**: LRU cache for secret lookups

### ✅ 4. MCP Stdio Transport
- **StdioMCPAdapter**: Launches MCP servers as subprocesses
- **Standard protocol**: JSON-RPC over stdin/stdout
- **Claude Desktop integration**: Auto-detects MCP servers from Claude config
- **Fallback**: Uses Windows-MCP via npx if no config found
- **VSCodeCopilotMonitor**: High-level wrapper for VS Code Copilot monitoring

## Remaining Gaps (Sprint 2+)

### ✅ 1. Vision-Guided Validation (Completed Nov 2025)
- **GLM-4.5V integration**: Vision model analyzes post-action screenshots
- **Smart failure detection**: Parses vision responses for error keywords, busy indicators, closed chat
- **Auto-recovery routing**: Failed validations trigger Recovery node (max 2 retries)
- **Pre-action checks**: ActStep uses vision to verify Copilot Chat state before actions
- **Decision keywords**: "error", "busy", "not open" → fail; "chat is open", "ready" → pass

### ⚠️ 2. Error Recovery (Partially Implemented)
- **Recovery node wired**: Connected with conditional routing from ActStep
- **No retry logic in adapter**: MCP adapter failures abort immediately
- **No circuit breakers**: Will keep failing on same error
- **No graceful degradation**: All-or-nothing execution

### ⚠️ 3. Plan Intelligence (Partially Implemented)
- **Basic reasoning working**: LLM selects tasks based on repo health
- **Action semantics partial**: Some plan directives interpreted
- **Policy execution incomplete**: Selectors like "label:needs-review" partially implemented
- **No scheduling**: Cadence field exists but not enforced
- **No dependencies**: Can't model task relationships

## Adapters
### StdioMCPAdapter (Default)
- Uses stdio transport (standard MCP protocol)
- Launches Windows-MCP as subprocess
- Communicates via JSON-RPC over stdin/stdout
- Auto-detects from Claude Desktop config or falls back to npx

### MCPAdapter (Legacy)
- Uses HTTP/JSON-RPC endpoint mapping from config
- Supports: list_windows, focus_window, screenshot, keypress, text_input, clipboard_get/set

### VSCodeCopilotMonitor (High-Level Tool)
- Wraps Windows-MCP session for VS Code-specific monitoring
- Scans all VS Code windows, extracts Copilot Chat text via State-Tool
- Copies full transcript via Clipboard-Tool ("Copy All" action)
- Tracks history per window, detects busy state via text diffs
- Returns structured results: `{title, is_busy, text_diff, transcript_diff}`
- Used by ActStep for intelligent Copilot interaction

### Recovery Logic
- Focus last-known VS Code window
- Retry palette open
- Restart actor cycle

## Storage
- `state/world_state.json`
- `state/episodes/<date>/events.jsonl`
- `state/checkpoints/graph.sqlite`
- `plans/plan.yaml`

## Implementation Priority

### Phase 1: Add Intelligence (Immediate)
1. **Integrate Claude API** for Reasoner agent
2. **Add vision model** for Actor validation
3. **Wire Recovery node** into graph edges
4. **Add retry logic** to MCP adapter

### Phase 2: Make Reliable (Week 1)
5. **Write real integration tests** (no mocks)
6. **Implement plan semantics** parsing
7. **Add circuit breakers** for failure handling
8. **Strengthen validation** beyond existence checks

### Phase 3: Production Ready (Week 2)
9. **Add observability** (OTLP export)
10. **Performance optimization**
11. **Create runbooks** for operations
12. **Security hardening** (auth, secrets management)

## Deployment Requirements

### Development Environment
- Windows 11 native (not WSL)
- Python 3.11+ with virtual environment
- VS Code with GitHub Copilot Chat enabled
- MCP server running locally
- Git with gh CLI extension

### Production Environment
- Windows Service for watchdog
- MCP server as system service
- Centralized logging infrastructure
- Monitoring and alerting
- Automated backup of state files

## Security Considerations
- No credentials in code - use environment variables
- Window title filtering to prevent wrong window interaction
- Dry-run mode by default - explicit write_mode required
- All actions logged with timestamps for audit trail
- MCP authentication tokens for production

## Conclusion

This system has **solid architecture but no brain**. It's a well-designed skeleton that needs:
1. **LLM integration** for actual reasoning
2. **Vision capabilities** for validation
3. **Error recovery** wiring
4. **Real testing** with actual components

Without these, it's just expensive automation that could be replaced with a simple AutoHotkey script.