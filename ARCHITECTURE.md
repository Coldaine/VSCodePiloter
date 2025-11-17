# System Architecture Documentation

## Critical Architecture Notice

### Current State vs Intended Design

**WARNING**: This codebase currently operates as **automation theater** - using AI orchestration frameworks without any actual AI integration.

| Component | Current Implementation | Intended Design |
|-----------|----------------------|-----------------|
| **LangGraph** | Simple state machine (dict router) | Multi-agent AI orchestration with LLMs |
| **Reasoner Agent** | Round-robin selection (`i % n`) | Claude/GPT-powered intelligent prioritization |
| **Vision Actor** | Blind command execution | Vision model analyzing screenshots for validation |
| **Screenshots** | Captured but never analyzed | Fed to vision models for state detection |
| **Plan Execution** | Action semantics ignored | Dynamic interpretation of plan directives |
| **Recovery Node** | Defined but disconnected | Active error recovery with retry logic |

**This is architectural malpractice** - like using a Formula 1 car as a shopping cart. The system must be upgraded with LLM integration to fulfill its intended purpose.

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
3. **Error recovery flow** - Intentional failures triggering Recovery node
4. **LLM reasoning validation** - Complex plans with priority-based selection
5. **Watchdog resumption** - Automatic restart after interruption

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
- **MCP Desktop Adapter**: Thin HTTP/JSON-RPC translation layer to Windows automation servers.
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

## Critical Missing Components

### 1. LLM Integration (Currently Absent)
- **No LLM clients**: No OpenAI/Anthropic SDK imported or initialized
- **Unused prompts**: `reasoner_system.txt` and `actor_system.txt` loaded but never used
- **No tool calling**: LangGraph configured for dict passing, not AI tool use
- **No streaming**: No support for incremental LLM responses

### 2. Vision Analysis (Currently Blind)
- **Screenshots not analyzed**: Captured as base64 but never decoded or examined
- **No OCR**: Can't read text from VS Code windows
- **No state detection**: Can't verify if Copilot Chat is open, busy, or responsive
- **No validation**: Can't confirm if actions succeeded

### 3. Error Recovery (Currently Orphaned)
- **Recovery node disconnected**: Exists but has no edges from other nodes
- **No retry logic**: Failures just log warnings and continue
- **No circuit breakers**: Will keep failing on same error
- **No graceful degradation**: All-or-nothing execution

### 4. Plan Intelligence (Currently Ignored)
- **Action semantics unused**: Plan defines actions but they're not interpreted
- **No policy execution**: Selectors like "label:needs-review" ignored
- **No scheduling**: Cadence field exists but not enforced
- **No dependencies**: Can't model task relationships

## Adapters
### MCPAdapter
- Uses endpoint mapping from config
- Supports: list_windows, focus_window, screenshot, keypress, text_input, clipboard_get/set

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