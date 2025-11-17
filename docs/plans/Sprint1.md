# Sprint 1: Transform from Automation Theater to Intelligent AI System

**Created**: 2025-01-17 (Current date placeholder - update on execution)
**Created By**: Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)
**Sprint Goal**: Integrate Z.ai GLM-4.6 LLM, validate system functionality, and establish testing infrastructure
**Duration**: 2 weeks
**Status**: In Progress

---

## Executive Summary

VSCodePiloter was initially a well-architected skeleton - a LangGraph-based multi-agent system with no actual AI integration. This sprint transforms it from "automation theater" to a functional intelligent system by:

1. ✅ **COMPLETED**: Integrating Z.ai GLM-4.6 for Reasoner agent intelligence
2. 🔄 **IN PROGRESS**: Validating the integration with real API keys and testing
3. ⏳ **PENDING**: Adding error recovery, retry logic, and comprehensive testing
4. ⏳ **PENDING**: Implementing vision capabilities (or alternative validation)

---

## Context: What We Started With

### The Problem
The codebase was **"automation theater"**:
- LangGraph used as a glorified state machine, not AI orchestrator
- Reasoner agent: naive round-robin selection (`i % n`)
- Vision Actor: blind execution without validation
- Screenshots captured but never analyzed
- Plan action semantics defined but ignored
- Recovery node existed but disconnected from graph

### Key Insight from User's Documentation
Extensive documentation found in `E:\Obsidian Vault\` revealed:
- Z.ai GLM-4.6 is coding-optimized, best value at $3/month
- API keys stored in Bitwarden Secrets Manager (organization: MooseGoose)
- Active key: `Z_AI_API_KEY` (not the old or backup keys)
- Critical endpoint: `https://api.z.ai/api/coding/paas/v4/` (coding plan, not common API)
- Model name must be exact: `glm-4.6` (lowercase)
- Auth format: Standard Bearer token
- Working in Claude Code Router (75% success rate)
- Known issue: Auth format varies by tool (401 errors in Goose CLI)

---

## Sprint 1 Objectives

### Primary Goals
1. ✅ Integrate Z.ai GLM-4.6 for intelligent Reasoner agent
2. 🔄 Validate integration with real credentials and testing
3. ⏳ Establish error handling and retry mechanisms
4. ⏳ Create comprehensive testing infrastructure
5. ⏳ Document all changes and setup procedures

### Success Criteria
- [ ] Reasoner agent makes intelligent task selections based on repo health
- [ ] System runs end-to-end in dry-run mode without errors
- [ ] API key retrieval from Bitwarden works reliably
- [ ] Error recovery node is wired into graph flow
- [ ] At least 3 integration tests pass with real VS Code windows
- [ ] All configuration documented in SETUP.md

---

## Work Completed (Session 2025-01-17)

### ✅ Phase 1: LLM Integration (COMPLETED)

#### 1. Configuration Layer
**Files Modified**:
- `agent/config.py` - Added `LLMConfig` class
- `config/config.yaml` - Added LLM configuration section

**Changes**:
```python
class LLMConfig(BaseModel):
    provider: str = "z.ai"
    model: str = "glm-4.6"
    api_key_env: str = "ZAI_API_KEY"
    api_base: str = "https://api.z.ai/api/coding/paas/v4/"
    temperature: float = 0.95
    max_tokens: int = 131072
```

**Rationale**: Externalized LLM configuration for flexibility and environment-based API key management.

#### 2. LLM Client Module
**Files Created**:
- `agent/llm_client.py` - LLM initialization and client creation

**Key Functions**:
- `create_llm_client()` - General-purpose ChatOpenAI client
- `create_reasoner_llm()` - Specialized for Reasoner (temp=0.7 for consistency)
- `create_actor_llm()` - Specialized for Actor (default temp=0.95)

**Features**:
- Environment variable loading with validation
- Z.ai coding endpoint configuration
- OpenAI-compatible interface via `langchain-openai`
- Streaming support enabled

**Rationale**: Abstracted LLM initialization to support multiple providers and use cases.

#### 3. Reasoner Agent Overhaul
**Files Modified**:
- `agent/nodes/reason_step.py` - Complete rewrite
- `agent/prompts/reasoner_system.txt` - Enhanced prompt with role definition

**Before**:
```python
idx = state.get("_next_idx", 0) % len(items)  # Round-robin
return items[idx]
```

**After**:
```python
# Build rich context: repos, PRs, plans
# Send to GLM-4.6 with system prompt
# Parse JSON response with reasoning + selection
# Create task envelope with LLM-generated message
```

**New Capabilities**:
- Analyzes repository health (branches, PRs, activity)
- Considers plan objectives and priorities
- Balances work across repositories
- Generates context-appropriate messages for Copilot Chat
- Logs reasoning for observability
- Falls back to round-robin on LLM failure (graceful degradation)

**Rationale**: Transformed from mechanical rotation to intelligent prioritization.

#### 4. Dependencies Updated
**Files Modified**:
- `pyproject.toml`

**Added**:
- `langchain-openai>=0.1.0`
- `langchain-core>=0.2.0`

**Rationale**: Required for Z.ai OpenAI-compatible integration.

#### 5. Documentation Created
**Files Created**:
- `SETUP.md` - Comprehensive setup guide
- `ARCHITECTURE.md` - Enhanced with current vs intended design table

**SETUP.md Covers**:
- Z.ai API key setup (environment variables)
- Virtual environment creation
- Dependency installation
- Configuration walkthrough
- MCP server setup (optional)
- Usage examples (scan, run-once, run-loop, watchdog)
- Verification steps
- Troubleshooting guide

**ARCHITECTURE.md Updates**:
- Critical warnings about "automation theater" state
- Comparison table (current vs intended design)
- Testing requirements (NO MOCKS for acceptance testing)
- Critical missing components documented
- Implementation priority roadmap

**Rationale**: Clear documentation for future developers and Claude instances.

#### 6. Git Repository Initialized
**Commits**:
1. `27b310c` - Initial commit with foundation code
2. `363696f` - Z.ai GLM-4.6 integration

**Files Tracked**: 32 files, 1,934 insertions total
**Ignored**: State files, checkpoints, logs, API keys, archives

---

## Work Remaining (Sprint 1 Continuation)

### 🔄 Phase 2: Validation & Testing (IN PROGRESS)

#### Task 2.1: API Key Integration with Bitwarden
**Status**: ⏳ Pending
**Priority**: Critical
**Estimated Time**: 1 hour

**Objective**: Integrate Bitwarden Secrets Manager for secure API key retrieval.

**Steps**:
- [ ] Install `bws` CLI tool (Bitwarden Secrets Manager)
- [ ] Set `BWS_ACCESS_TOKEN` environment variable
- [ ] Test retrieval: `bws secret get Z_AI_API_KEY`
- [ ] Update SETUP.md with Bitwarden retrieval instructions
- [ ] Create helper script: `scripts/get_api_key.ps1`
- [ ] Verify active key (not old/backup keys)

**Acceptance Criteria**:
- API key retrieved from Bitwarden successfully
- `ZAI_API_KEY` environment variable set correctly
- Documentation updated with Bitwarden workflow

**Files to Modify**:
- `SETUP.md` - Add Bitwarden section
- `scripts/get_api_key.ps1` (new) - PowerShell helper

---

#### Task 2.2: Endpoint Validation
**Status**: ⏳ Pending
**Priority**: Critical
**Estimated Time**: 30 minutes

**Objective**: Verify Z.ai coding endpoint is reachable and authentication works.

**Steps**:
- [ ] Create test script: `scripts/test_zai_endpoint.sh`
- [ ] Test with curl using active API key
- [ ] Verify model name `glm-4.6` (lowercase)
- [ ] Confirm response structure matches OpenAI format
- [ ] Test with different temperatures (0.7, 0.95)
- [ ] Document expected response format

**Test Command** (from user's Obsidian docs):
```bash
curl -X POST https://api.z.ai/api/coding/paas/v4/chat/completions \
  -H "Authorization: Bearer $ZAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "glm-4.6",
    "messages": [
      {"role": "system", "content": "You are a professional programming assistant"},
      {"role": "user", "content": "Say hello"}
    ],
    "temperature": 0.95
  }'
```

**Expected Output**:
```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "Hello! ..."
    }
  }]
}
```

**Acceptance Criteria**:
- Curl test returns 200 OK
- Response contains valid completion
- No 401 (auth), 404 (endpoint), or 400 (model) errors

**Files to Create**:
- `scripts/test_zai_endpoint.sh` (new)
- `docs/api_validation_results.md` (new) - Test output log

---

#### Task 2.3: LLM Client Unit Tests
**Status**: ⏳ Pending
**Priority**: High
**Estimated Time**: 2 hours

**Objective**: Validate LLM client initialization and error handling.

**Steps**:
- [ ] Create `tests/test_llm_client.py`
- [ ] Test API key loading from environment
- [ ] Test error when API key missing
- [ ] Test client creation with valid config
- [ ] Test Reasoner-specific temperature override
- [ ] Mock ChatOpenAI to avoid real API calls in unit tests

**Test Cases**:
1. `test_create_llm_client_success()` - Happy path
2. `test_create_llm_client_no_api_key()` - Missing key error
3. `test_create_reasoner_llm_temperature()` - Verify temp=0.7
4. `test_create_actor_llm_temperature()` - Verify default temp

**Acceptance Criteria**:
- All 4 unit tests pass
- Code coverage >80% for `llm_client.py`

**Files to Create**:
- `tests/test_llm_client.py` (new)

---

#### Task 2.4: Reasoner Agent Integration Tests
**Status**: ⏳ Pending
**Priority**: High
**Estimated Time**: 3 hours

**Objective**: Validate Reasoner makes intelligent decisions with real LLM.

**Steps**:
- [ ] Create `tests/integration/test_reasoner_with_llm.py`
- [ ] Create mock state with multiple repos and work items
- [ ] Call `reason_step()` with real LLM client
- [ ] Verify task envelope created
- [ ] Verify reasoning is logged
- [ ] Verify message is context-appropriate
- [ ] Test fallback to round-robin when LLM fails

**Test Scenarios**:
1. **High-priority repo** - Repo with 3 open PRs should be selected
2. **Stale repo** - Repo not touched in 2 days should be prioritized
3. **Balanced selection** - Work distributed across repos
4. **LLM failure** - Graceful fallback to round-robin

**Acceptance Criteria**:
- Reasoner selects high-priority repo >80% of the time
- Reasoning includes mention of PRs/activity
- Generated message is contextual (not generic)
- Fallback works when API key invalid

**Files to Create**:
- `tests/integration/test_reasoner_with_llm.py` (new)
- `tests/fixtures/mock_repos.json` (new) - Test data

---

#### Task 2.5: End-to-End Dry Run Test
**Status**: ⏳ Pending
**Priority**: Critical
**Estimated Time**: 2 hours

**Objective**: Run full graph execution in dry-run mode (no VS Code interaction).

**Prerequisites**:
- Real `plan.yaml` configured
- Real repos directory specified
- Valid Z.ai API key
- `write_mode: false` in config

**Steps**:
- [ ] Set up test repos directory with 2-3 git repos
- [ ] Configure `config/config.yaml` with test paths
- [ ] Run: `agent-cli run-once`
- [ ] Verify all graph nodes execute
- [ ] Check episode logs created in `state/episodes/`
- [ ] Verify LLM reasoning appears in logs
- [ ] Confirm no errors in execution

**Expected Flow**:
```
ScanRepos → finds 3 repos
SyncPlan → loads plan.yaml
ReasonStep → GLM-4.6 selects repo with PRs
ActStep → (dry-run, no actual VS Code interaction)
ValidateEvidence → checks artifacts exist
Persist → saves trace to episodes/
```

**Acceptance Criteria**:
- Graph completes without errors
- Trace file created in `state/episodes/YYYYMMDD/`
- Reasoner logs show GLM-4.6 decision
- No crashes or unhandled exceptions

**Files to Check**:
- `state/episodes/<date>/trace_<timestamp>.json`
- `state/episodes/<date>/events.jsonl`

---

### ⏳ Phase 3: Error Handling & Resilience (PENDING)

#### Task 3.1: Wire Recovery Node into Graph
**Status**: ⏳ Pending
**Priority**: High
**Estimated Time**: 2 hours

**Current Problem**: Recovery node exists but has no edges connecting it to the main graph flow.

**Objective**: Connect Recovery node to handle ActStep failures.

**Steps**:
- [ ] Read `agent/nodes/recovery.py` to understand logic
- [ ] Modify `agent/langgraph_app.py` to add conditional edge
- [ ] Add edge: `ActStep → Recovery` when `action_report.status == "failed"`
- [ ] Add edge: `Recovery → ActStep` for retry
- [ ] Test recovery with intentional failure (invalid window)

**Graph Changes**:
```python
# Before: ActStep → ValidateEvidence (always)
workflow.add_edge("ActStep", "ValidateEvidence")

# After: ActStep → Recovery (on failure) → ActStep (retry)
workflow.add_conditional_edges(
    "ActStep",
    lambda state: "Recovery" if state.get("action_report", {}).get("status") == "failed" else "ValidateEvidence",
    {
        "Recovery": "Recovery",
        "ValidateEvidence": "ValidateEvidence"
    }
)
workflow.add_edge("Recovery", "ActStep")  # Retry after recovery
```

**Acceptance Criteria**:
- Recovery node triggers on ActStep failure
- System attempts window refocus + retry
- Logs show recovery attempt
- Graph doesn't crash on failure

**Files to Modify**:
- `agent/langgraph_app.py`

---

#### Task 3.2: Add Retry Logic to MCP Adapter
**Status**: ⏳ Pending
**Priority**: Medium
**Estimated Time**: 1.5 hours

**Current Problem**: MCP adapter has no retry logic - single failure = total failure.

**Objective**: Add retry with exponential backoff using `tenacity` library.

**Steps**:
- [ ] Modify `agent/adapters/mcp_adapter.py`
- [ ] Add `@retry` decorator to HTTP calls
- [ ] Configure: 3 retries, exponential backoff, 30s timeout
- [ ] Log retry attempts
- [ ] Test with intentionally unreachable MCP server

**Implementation**:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def _http_request(self, endpoint, payload):
    # Existing HTTP logic
```

**Acceptance Criteria**:
- Failed requests retry up to 3 times
- Backoff delays: 2s, 4s, 8s
- Logs show retry attempts
- Final failure raises exception

**Files to Modify**:
- `agent/adapters/mcp_adapter.py`
- `agent/mcp/client.py`

---

#### Task 3.3: Strengthen Validation Logic
**Status**: ⏳ Pending
**Priority**: Medium
**Estimated Time**: 1 hour

**Current Problem**: `validate_evidence.py` only checks if screenshot keys exist, not if they're valid.

**Objective**: Validate screenshot content (size, format, non-empty).

**Steps**:
- [ ] Modify `agent/nodes/validate_evidence.py`
- [ ] Decode base64 screenshots
- [ ] Verify image size >100KB
- [ ] Check image dimensions >100x100
- [ ] Verify PNG format
- [ ] Reject black/empty screenshots

**Implementation**:
```python
import base64
from PIL import Image
from io import BytesIO

def _validate_screenshot(artifact_b64: str) -> bool:
    try:
        img_data = base64.b64decode(artifact_b64)
        img = Image.open(BytesIO(img_data))

        # Check size
        if len(img_data) < 100_000:  # <100KB
            return False

        # Check dimensions
        if img.width < 100 or img.height < 100:
            return False

        # Check not all black
        if img.getextrema() == ((0, 0), (0, 0), (0, 0)):
            return False

        return True
    except Exception:
        return False
```

**Acceptance Criteria**:
- Invalid screenshots rejected
- Logs show validation failure reason
- Empty/corrupt images don't pass validation

**Files to Modify**:
- `agent/nodes/validate_evidence.py`

---

### ⏳ Phase 4: Comprehensive Testing (PENDING)

#### Task 4.1: Create Integration Test Suite
**Status**: ⏳ Pending
**Priority**: High
**Estimated Time**: 4 hours

**Objective**: Real integration tests with actual VS Code windows (NO MOCKS).

**Test Scenarios**:
1. **Single VS Code Window** - Focus and interact
2. **Multiple Windows** - Select correct window by title regex
3. **Copilot Chat Open** - Copy existing chat content
4. **Copilot Chat Closed** - Open chat via palette
5. **Window Not Found** - Trigger recovery

**Requirements**:
- Real VS Code instance running
- GitHub Copilot Chat extension installed
- MCP server running (or fallback adapter)
- Test repos with actual git repositories

**Steps**:
- [ ] Create `tests/integration/test_vscode_interaction.py`
- [ ] Set up test fixtures (VS Code automation)
- [ ] Test window focus by title regex
- [ ] Test Command Palette automation
- [ ] Test clipboard operations
- [ ] Verify screenshots captured
- [ ] Test error recovery

**Acceptance Criteria**:
- All 5 test scenarios pass
- Tests run on real VS Code (not mocked)
- CI/CD can skip these tests (require manual setup)
- Tests documented in `docs/testing.md`

**Files to Create**:
- `tests/integration/test_vscode_interaction.py` (new)
- `docs/testing.md` (new) - Testing guide

---

#### Task 4.2: Performance Benchmarks
**Status**: ⏳ Pending
**Priority**: Low
**Estimated Time**: 1 hour

**Objective**: Measure and document real-world performance.

**Metrics to Track**:
- Time to focus VS Code window (<500ms target)
- Time to open Copilot Chat (<2s target)
- Time to copy chat content (<1s target)
- LLM reasoning latency (<3s target)
- Full work item execution (<10s target)

**Steps**:
- [ ] Add timing instrumentation to each node
- [ ] Run 10 iterations of full graph
- [ ] Calculate average, min, max, p95
- [ ] Document in `docs/performance.md`

**Files to Create**:
- `docs/performance.md` (new)

---

### ⏳ Phase 5: Vision Capabilities (FUTURE SPRINT)

**Note**: GLM-4.6 does not have native vision capabilities. This phase is deferred to Sprint 2.

#### Options for Vision Analysis:
1. **OCR Preprocessing** - Use Tesseract to extract text from screenshots
2. **Vision Model Integration** - Add GPT-4V or Claude 3.5 for screenshot analysis
3. **Hybrid Approach** - Z.ai for reasoning, vision model for validation
4. **State Detection Heuristics** - Detect Copilot Chat state without vision

**Decision Required**: Select approach based on budget and requirements.

---

## Sprint 1 Checklist

### Configuration & Setup
- [x] LLM configuration added to `config.py` and `config.yaml`
- [x] Z.ai coding endpoint configured
- [x] Environment variable management documented
- [ ] Bitwarden integration documented and tested
- [ ] API key retrieval script created

### Code Implementation
- [x] `llm_client.py` module created
- [x] Reasoner agent rewritten to use GLM-4.6
- [x] System prompt enhanced with role definition
- [x] Graceful fallback to round-robin on LLM failure
- [ ] Recovery node wired into graph
- [ ] MCP adapter retry logic added
- [ ] Validation logic strengthened

### Testing
- [ ] Endpoint validation test passed
- [ ] LLM client unit tests created and passing
- [ ] Reasoner integration tests created and passing
- [ ] End-to-end dry run successful
- [ ] Integration tests with real VS Code passing
- [ ] Performance benchmarks documented

### Documentation
- [x] `SETUP.md` created with comprehensive setup guide
- [x] `ARCHITECTURE.md` updated with warnings and roadmap
- [x] `PILLARS.md` exists (already present)
- [x] `README.md` exists (already present)
- [ ] `docs/testing.md` created
- [ ] `docs/performance.md` created
- [ ] `docs/api_validation_results.md` created

### Git & Version Control
- [x] Repository initialized
- [x] `.gitignore` configured
- [x] Initial commit created
- [x] Z.ai integration committed
- [ ] Sprint 1 completion commit

---

## Risk Register

### High Priority Risks

#### Risk 1: Z.ai API Key Issues
**Probability**: Medium
**Impact**: Critical
**Mitigation**:
- Verify subscription is active ($3/month)
- Confirm using active key, not old/backup keys
- Test endpoint before full integration
- Document troubleshooting in SETUP.md

#### Risk 2: Auth Format Mismatch
**Probability**: Medium
**Impact**: High
**Context**: User's Obsidian docs show 401 errors in Goose CLI despite correct endpoint
**Mitigation**:
- Test curl command exactly as documented
- Verify Bearer token format
- Check LangChain OpenAI compatibility
- Have fallback to round-robin ready

#### Risk 3: MCP Server Unavailable
**Probability**: Medium
**Impact**: Medium
**Mitigation**:
- Fallback adapter already implemented
- Document both MCP and fallback setup
- Test both adapters independently

#### Risk 4: VS Code Automation Reliability
**Probability**: High
**Impact**: Medium
**Context**: Window focus and palette commands may be flaky
**Mitigation**:
- Recovery node with retry logic
- Screenshot verification
- Timeout handling
- Detailed logging for debugging

### Medium Priority Risks

#### Risk 5: GLM-4.6 No Vision Support
**Probability**: Certain
**Impact**: Medium
**Context**: GLM-4.6 cannot analyze screenshots
**Mitigation**:
- Defer vision to Sprint 2
- Use OCR or separate vision model
- Focus on text-based validation for now

#### Risk 6: Performance Issues
**Probability**: Low
**Impact**: Medium
**Mitigation**:
- Benchmark early in sprint
- Optimize if >10s per work item
- Consider faster models for Actor

---

## Dependencies & Blockers

### External Dependencies
- [x] Z.ai API key available in Bitwarden
- [ ] Z.ai subscription active ($3/month)
- [ ] MCP server running (or fallback adapter configured)
- [ ] VS Code with Copilot Chat installed
- [ ] Git with `gh` CLI extension

### Internal Dependencies
- [x] LangGraph and LangChain installed
- [x] Configuration files created
- [ ] Test repos directory set up
- [ ] State directory structure created

### Blockers
- **BLOCKER 1**: API key not yet retrieved from Bitwarden
  - **Owner**: Next Claude instance
  - **Target**: Within 1 hour of sprint continuation

- **BLOCKER 2**: Endpoint not yet validated with curl
  - **Owner**: Next Claude instance
  - **Target**: Before any LLM integration tests

---

## Success Metrics

### Code Quality
- [ ] No linting errors (`pylint`, `mypy`)
- [ ] Code coverage >70%
- [ ] All critical paths tested

### Functionality
- [ ] Reasoner makes intelligent decisions >80% of time
- [ ] End-to-end dry run completes successfully
- [ ] Error recovery works for common failures
- [ ] System runs for 30 minutes without crashes

### Documentation
- [ ] All setup steps documented and tested
- [ ] Troubleshooting guide covers common issues
- [ ] Architecture decisions recorded
- [ ] API usage examples provided

### Performance
- [ ] LLM reasoning <3s average
- [ ] Full work item <10s average
- [ ] No memory leaks over 1 hour run
- [ ] CPU usage reasonable (<50% average)

---

## Next Steps (Immediate Priority)

### For Next Claude Instance:

1. **IMMEDIATE** (30 min):
   - [ ] Retrieve Z.ai API key from Bitwarden
   - [ ] Set `ZAI_API_KEY` environment variable
   - [ ] Run curl test to validate endpoint

2. **HIGH PRIORITY** (2 hours):
   - [ ] Run `agent-cli scan` to verify configuration
   - [ ] Run `agent-cli run-once` in dry-run mode
   - [ ] Check logs in `state/episodes/` for errors

3. **MEDIUM PRIORITY** (4 hours):
   - [ ] Create and run LLM client unit tests
   - [ ] Create and run Reasoner integration tests
   - [ ] Wire Recovery node into graph

4. **ONGOING**:
   - [ ] Update this plan with checkmarks as tasks complete
   - [ ] Log any issues in `docs/issues.md`
   - [ ] Commit progress regularly with descriptive messages

---

## Notes for Future Claude Instances

### Critical Reminders
1. **ALWAYS check this plan first** - Don't start work without reading Sprint1.md
2. **Check off tasks as you complete them** - Update the checkboxes in this file
3. **NO MOCKS for acceptance testing** - Real VS Code, real LLM, real repos
4. **Read CLAUDE.md in repo root** - Contains workflow instructions
5. **User's Obsidian Vault has critical info** - Check `E:\Obsidian Vault\` for API keys, endpoints, configuration examples

### What Makes This Different from Other Projects
- **User has comprehensive documentation** - Don't reinvent, check Obsidian vault first
- **API keys in Bitwarden** - Use `bws` CLI, don't ask user to paste keys
- **Z.ai has quirks** - Coding endpoint required, exact model name, auth format varies
- **Testing is non-negotiable** - User explicitly requires no mocks, real integration tests

### If You Get Stuck
1. Check `E:\Obsidian Vault\Configuration\` for similar setups
2. Check `E:\Obsidian Vault\LLM\API Key Repository.md` for credentials
3. Review `ARCHITECTURE.md` for system design
4. Check recent git commits for context
5. Ask user for clarification if truly blocked

---

## Appendix: Key File Locations

### Configuration
- `config/config.yaml` - Main configuration
- `plans/plan.yaml` - Work item definitions
- `agent/config.py` - Pydantic models
- `agent/prompts/reasoner_system.txt` - Reasoner prompt

### Core Modules
- `agent/llm_client.py` - LLM initialization
- `agent/nodes/reason_step.py` - Reasoner agent
- `agent/nodes/act_step.py` - Vision actor
- `agent/nodes/recovery.py` - Recovery logic
- `agent/langgraph_app.py` - Graph definition
- `agent/main.py` - CLI entry point

### Adapters
- `agent/adapters/mcp_adapter.py` - MCP HTTP client
- `agent/adapters/fallback_adapter.py` - PyAutoGUI fallback
- `agent/adapters/base.py` - Adapter interface

### Documentation
- `SETUP.md` - Setup guide
- `ARCHITECTURE.md` - System architecture
- `PILLARS.md` - Core requirements
- `README.md` - Project overview

### State & Logs
- `state/world_state.json` - Persistent state
- `state/episodes/<date>/` - Execution traces
- `state/checkpoints/graph.sqlite` - LangGraph checkpoints

### User Resources
- `E:\Obsidian Vault\Configuration\` - Configuration examples
- `E:\Obsidian Vault\LLM\` - API keys and model info
- `E:\Obsidian Vault\cockpit\_dashboards_experiments\Api key.md` - Legacy key reference

---

**End of Sprint 1 Plan**

*Remember: This is a living document. Update it as work progresses. Future Claude instances depend on accurate status tracking.*