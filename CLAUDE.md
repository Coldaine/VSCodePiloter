# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VSCodePiloter is a LangGraph-based multi-agent system that orchestrates GitHub Copilot Chat across multiple VS Code windows on Windows 11. It uses a Reasoner agent (powered by Z.ai GLM-4.6) and a Vision Actor to periodically monitor repositories, analyze PR status, and nudge Copilot Chat with contextual information.

## 🚨 CRITICAL: Sprint-Based Workflow

**This repository uses a sprint-based relay system where Claude instances collaborate via Sprint plans.**

**BEFORE you start any work on this repository, you MUST:**

1. ✅ **Read this entire file** (you're doing it now - good!)
2. ✅ **Check the current sprint plan** in `docs/plans/Sprint1.md`
3. ✅ **Update task checkboxes** as you complete work
4. ✅ **Review recent git commits** to understand context
5. ✅ **Check the user's Obsidian Vault** for configuration examples

**DO NOT skip these steps.** Future Claude instances depend on you following this workflow.

### The Relay Race Metaphor

You are part of a relay race. The baton is the sprint plan. Your job is to:
1. Pick up where the last Claude left off (read Sprint1.md)
2. Complete your portion of the work (check boxes as you go)
3. Pass the baton cleanly to the next Claude (update Sprint1.md)

## Workflow for All Claude Instances

### Step 1: Context Gathering (5 minutes)

Before writing any code, gather context:

```bash
# 1. Read the current sprint plan
cat docs/plans/Sprint1.md

# 2. Check recent commits for context
git log --oneline -10

# 3. Check current branch and status
git status

# 4. Review open tasks (look for unchecked boxes in Sprint1.md)
grep "\[ \]" docs/plans/Sprint1.md
```

**Key Questions to Answer:**
- What sprint are we on?
- What tasks are completed (checked boxes)?
- What tasks are pending (unchecked boxes)?
- What was the last commit about?
- Are there any blockers noted in the sprint plan?

### Step 2: Select Task (2 minutes)

From the sprint plan, identify:
- **BLOCKER** tasks (highest priority)
- **IMMEDIATE** tasks (next priority)
- **HIGH PRIORITY** tasks (if no blockers/immediate)
- **MEDIUM PRIORITY** tasks (if high priority done)

**Rules:**
- Complete tasks in order of priority
- Don't jump ahead unless explicitly requested by user
- If uncertain, ask user which task to tackle

### Step 3: Execute Task (variable time)

While working:
- ✅ **Follow the task steps** exactly as written in sprint plan
- ✅ **Test as you go** - don't write untested code
- ✅ **Log issues** - if something doesn't work, note it
- ✅ **Commit frequently** - small, focused commits

### Step 4: Update Sprint Plan (2 minutes)

**THIS IS MANDATORY - DO NOT SKIP**

After completing a task:

```bash
# 1. Edit Sprint1.md
# 2. Change [ ] to [x] for completed task
# 3. Add any notes or issues discovered
# 4. Save the file
```

**Example Change:**
```markdown
Before:
- [ ] Retrieve Z.ai API key from Bitwarden

After:
- [x] Retrieve Z.ai API key from Bitwarden
  - **Note**: Key retrieved successfully from Bitwarden project "AI Models"
  - **Issue**: None
```

### Step 5: Commit Progress (1 minute)

```bash
# Stage your changes
git add .

# Commit with descriptive message
git commit -m "Complete Task X.Y: [Brief description]

- Specific change 1
- Specific change 2
- Updated Sprint1.md task checklist

🤖 Generated with Claude Code"
```

### Step 6: Report to User (1 minute)

Tell the user:
- ✅ What you completed
- ✅ What you tested
- ✅ What you updated in the sprint plan
- ⚠️ Any issues or blockers discovered
- ➡️ What the next task is

## Common Development Commands

### Setup & Installation
```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -e .

# Install with fallback adapter (pyautogui)
pip install -e .[fallback]
```

### Running the Agent
```bash
# Scan repositories only (dry run, no LLM)
agent-cli scan

# Run once with LLM reasoning (dry run mode by default)
agent-cli run-once

# Run in continuous loop (every 30 minutes)
agent-cli run-loop --interval-sec 1800

# Run watchdog (production mode with auto-recovery)
agent-watchdog
```

### Testing
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_llm_client.py -v

# Run with coverage
pytest --cov=agent --cov-report=html

# Run integration tests (requires VS Code running)
pytest tests/integration/ -v
```

### API Key Management
```powershell
# Retrieve Z.ai API key from Bitwarden (Windows)
.\scripts\get_api_key.ps1

# Test Z.ai endpoint connectivity
.\scripts\test_zai_endpoint.ps1

# Linux/macOS equivalents
source ./scripts/get_api_key.sh
./scripts/test_zai_endpoint.sh
```

## Architecture & Key Components

### LangGraph State Flow
The system uses LangGraph for orchestration with the following node sequence:
1. **ScanRepos** → Discovers git repositories and PR status
2. **SyncPlan** → Loads plan.yaml and creates work items
3. **ReasonStep** → GLM-4.6 analyzes repos and selects highest-priority task
4. **ActStep** → Executes desktop automation to interact with VS Code
5. **ValidateEvidence** → Checks screenshots and artifacts
6. **Persist** → Saves traces and updates heartbeat
7. **Recovery** → (Currently disconnected) Should handle ActStep failures

**Critical Gap**: The Recovery node exists but has no edges connecting it to the graph flow. This needs to be fixed in Sprint 1.

### Secret Management Architecture
The system uses a composite pattern for automatic secret detection across environments:

- **BitwardenProvider**: Uses `bws` CLI when BWS_ACCESS_TOKEN is set (local dev)
- **EnvVarProvider**: Uses environment variables (CI/CD, production)
- **CompositeSecretProvider**: Automatically chains providers based on environment
- Located in `agent/secrets/` with factory pattern in `factory.py`

### LLM Integration Details

**Text Model (Reasoning)**: Z.ai GLM-4.6
- **Purpose**: Repository analysis and task prioritization
- **Endpoint**: `https://api.z.ai/api/coding/paas/v4/` (coding plan subscription)
- **Model Name**: `glm-4.6` (exact lowercase required)
- **Temperature**: 0.7 (deterministic reasoning)
- **Context**: 200K tokens
- **Client Function**: `create_reasoner_llm()`

**Vision Model (Screenshot Analysis)**: Z.ai GLM-4.5V
- **Purpose**: VS Code window analysis and action validation
- **Endpoint**: `https://api.z.ai/api/paas/v4/` (standard API, different from coding!)
- **Model Name**: `glm-4.5v` (configured in config.yaml)
- **Temperature**: 0.95 (creative interpretation)
- **Context**: 64K-66K multimodal tokens
- **Client Function**: `create_vision_llm()`
- **Helper Functions**: `create_vision_message()`, `encode_image_to_base64()`
- **⚠️ CRITICAL**: Vision models MUST use `/api/paas/v4/`, NOT `/api/coding/paas/v4/`

**Authentication**: Bearer token from `ZAI_API_KEY` environment variable
- Auto-retrieved from Bitwarden Secrets Manager (local dev)
- Falls back to environment variables (CI/CD)
- Client Module: `agent/llm_client.py` with specialized functions for each model

### Desktop Automation Adapters
Two adapter options (configured in config.yaml):

1. **MCPAdapter** (`agent/adapters/mcp_adapter.py`)
   - Communicates with MCP server via HTTP/JSON
   - Configurable endpoints for window operations
   - Production-ready with proper error handling
   - **Gap**: No retry logic - single HTTP failure = total failure

2. **FallbackAdapter** (`agent/adapters/fallback_adapter.py`)
   - Uses pyautogui for direct automation
   - Testing/development fallback option
   - Requires `pip install -e .[fallback]`

## Critical Project Rules

### Testing Requirements

**CRITICAL: NO MOCKS FOR ACCEPTANCE TESTING**

The user has explicitly stated:
> "Can you go ahead and make sure we write in our architecture that no mocks or live tests are suitable for acceptance testing?"

**What This Means:**
- ❌ **NO** mocked VS Code windows
- ❌ **NO** mocked LLM responses
- ❌ **NO** mocked git repositories
- ❌ **NO** mocked API calls for acceptance tests

- ✅ **YES** real VS Code instances
- ✅ **YES** real Z.ai API calls
- ✅ **YES** real git repositories
- ✅ **YES** real MCP server or fallback adapter

**Exception**: Unit tests may use mocks, but integration/acceptance tests must be real.

### API Key Management

**DO NOT ask user to paste API keys directly.**

Instead:
1. **Read from Bitwarden** using `bws` CLI tool
2. **Use environment variables** (`$ZAI_API_KEY`, etc.)
3. **Reference user's Obsidian Vault** for key locations

**Bitwarden Access:**
```powershell
# List all secrets
bws secret list --output table

# Get specific secret
bws secret get Z_AI_API_KEY | jq -r '.value'

# Copy to clipboard
bws secret get Z_AI_API_KEY | jq -r '.value' | clip

# Set environment variable
$env:ZAI_API_KEY = (bws secret get Z_AI_API_KEY | ConvertFrom-Json).value
```

**Key Locations** (from user's Obsidian Vault):
- **Active Z.ai key**: `Z_AI_API_KEY` in Bitwarden project "AI Models"
- **Backup keys**: `Z_AI_API_KEY_OLD`, `Z_AI_API_KEY_BACKUP`
- **Full inventory**: `E:\Obsidian Vault\LLM\API Key Repository.md`

### Z.ai Specific Quirks

**IMPORTANT**: Z.ai has specific requirements that differ from standard OpenAI:

1. **Endpoint**: MUST use coding endpoint
   - ✅ Correct: `https://api.z.ai/api/coding/paas/v4/`
   - ❌ Wrong: `https://api.z.ai/api/paas/v4/`

2. **Model Names**: MUST be exact lowercase
   - ✅ Correct (text): `glm-4.6`
   - ✅ Correct (vision): `glm-4.5v`
   - ❌ Wrong: `GLM-4.6`, `glm-4`, `GLM-4.5V`

3. **Auth Format**: Standard Bearer token
   - ✅ Correct: `Authorization: Bearer YOUR_KEY`
   - ❌ Wrong: Custom header formats

4. **Known Issues** (from user's docs):
   - Auth format varies by tool (401 errors in some CLIs)
   - Working in Claude Code Router (75% success rate)
   - Requires $3/month subscription to be active

**Always test with curl before implementing:**
```bash
curl -X POST https://api.z.ai/api/coding/paas/v4/chat/completions \
  -H "Authorization: Bearer $ZAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "glm-4.6",
    "messages": [{"role": "user", "content": "hello"}]
  }'
```

## Configuration

### Required Environment Variables
- `ZAI_API_KEY`: Z.ai API key for GLM-4.6 (retrieve from Bitwarden)
- `BWS_ACCESS_TOKEN`: (Optional) Bitwarden access token for automatic key retrieval

### Key Configuration Files
- `config/config.yaml`: Main configuration (repos_root, adapters, LLM settings)
- `plans/plan.yaml`: Work item definitions and policies
- `state/world_state.json`: Persistent agent state

### VS Code Requirements
- Window titles must include folder path for reliable mapping
- Recommended VS Code setting:
  ```json
  "window.title": "${dirty}${activeEditorShort}${separator}${folderPath}${separator}${appName}"
  ```

## Error Handling Protocol

### When You Encounter an Error

1. **Don't panic** - Most errors are expected during development
2. **Check the sprint plan** - Is there a known risk or issue noted?
3. **Check user's docs** - Has this been solved before?
4. **Log the issue** - Add to sprint plan under "Issues Discovered"
5. **Attempt recovery** - Try the troubleshooting steps
6. **Ask user if stuck** - Don't spend hours on a blocker

### Common Issues & Solutions

#### Issue: API Key Not Working
**Symptoms**: 401 Unauthorized from Z.ai
**Solutions**:
1. Verify using active key: `bws secret get Z_AI_API_KEY`
2. Check subscription is active ($3/month)
3. Test with curl command from user's docs
4. Verify endpoint is coding endpoint, not common API

#### Issue: LLM Client Creation Fails
**Symptoms**: Import errors, config errors
**Solutions**:
1. Check dependencies installed: `pip list | grep langchain`
2. Verify config.yaml LLM section exists
3. Check environment variable set: `echo $ZAI_API_KEY`
4. Review llm_client.py for errors

#### Issue: Graph Execution Fails
**Symptoms**: Errors in agent-cli run-once
**Solutions**:
1. Check state directory exists: `ls -la state/`
2. Verify repos_root in config.yaml points to real directory
3. Check plan.yaml is valid YAML
4. Review logs in state/episodes/

#### Issue: VS Code Window Not Found
**Symptoms**: ActStep fails to focus window
**Solutions**:
1. Check window_title_regex in config.yaml
2. Verify VS Code is running
3. Test with fallback adapter instead of MCP
4. Check MCP server is running: `curl http://127.0.0.1:43110/windows/list`

## Sprint Completion Protocol

When all tasks in Sprint1.md are checked:

1. **Create completion summary**
   - What was accomplished
   - What was deferred
   - Metrics achieved (test coverage, performance, etc.)
   - Issues discovered

2. **Create Sprint2.md**
   - Copy template from Sprint1.md
   - Define new objectives
   - Break down deferred tasks
   - Set new success criteria

3. **Tag the release**
   ```bash
   git tag -a v0.1.0-sprint1 -m "Sprint 1 Complete: Z.ai Integration"
   git push origin v0.1.0-sprint1
   ```

4. **Report to user**
   - Summary of sprint completion
   - Next steps recommendation
   - Any blockers for Sprint 2

## Contact & Escalation

### When to Ask User for Help

- **Blockers that can't be resolved** - After 30 minutes of troubleshooting
- **Missing information** - Can't find in docs or code
- **Decision points** - Multiple valid approaches, unclear which to choose
- **Scope changes** - Task significantly bigger than estimated
- **External dependencies** - Need user to install/configure something

### What NOT to Ask User

- **Things in the docs** - Check Obsidian Vault first
- **Things in the code** - Read the existing implementation
- **Things in the sprint plan** - The plan has the answers
- **API keys** - Use Bitwarden, don't ask for paste

### User's Documentation Resources

The user has extensive documentation in their Obsidian Vault at `E:\Obsidian Vault\`.

**Before implementing anything Z.ai related, check:**
- `E:\Obsidian Vault\Configuration\AI-Coding-Tools-Master-Configuration.md`
- `E:\Obsidian Vault\Configuration\claude-code-router-playbook.md`
- `E:\Obsidian Vault\Configuration\kilocode_provider_comparison.md`
- `E:\Obsidian Vault\LLM\API Key Repository.md`

**These docs contain:**
- Working configuration examples
- Curl test commands that are known to work
- Troubleshooting for common issues
- Provider comparison matrices
- Performance benchmarks

## Final Reminders

1. ✅ **Always update Sprint1.md** - Future Claude instances need accurate state
2. ✅ **Test with real components** - No mocks for acceptance tests
3. ✅ **Check user's Obsidian Vault** - Comprehensive examples exist
4. ✅ **Use Bitwarden for secrets** - Never ask user to paste keys
5. ✅ **Commit frequently** - Small, focused commits
6. ✅ **Document as you go** - Don't leave it for later
7. ✅ **Ask when blocked** - Don't waste hours on a known issue

---

**You are part of a relay race. The baton is the sprint plan. Pass it cleanly to the next Claude instance.**

Good luck! 🚀