# VSCodePiloter Setup Guide

## Prerequisites

- Python 3.11 or higher
- Windows 11 (native, not WSL)
- VS Code with GitHub Copilot Chat enabled
- Git with `gh` CLI extension
- Z.ai API key (for GLM-4.6 coding plan)

## Installation

### 1. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate  # On Windows
```

### 2. Install Dependencies

```bash
pip install -e .
```

For fallback adapter (local automation):
```bash
pip install -e .[fallback]
```

### 3. Configure Z.ai API Key

VSCodePiloter uses Z.ai's GLM-4.6 model for intelligent task reasoning.

#### Get Your Z.ai API Key

1. Sign up at [https://z.ai](https://z.ai)
2. Subscribe to the **GLM Coding Plan** (free coding calls available)
3. Go to your dashboard and generate an API key

#### Set Environment Variable

**Windows (PowerShell):**
```powershell
$env:ZAI_API_KEY = "your-api-key-here"
```

**Windows (Command Prompt):**
```cmd
set ZAI_API_KEY=your-api-key-here
```

**Permanent (Windows):**
```powershell
[System.Environment]::SetEnvironmentVariable('ZAI_API_KEY', 'your-api-key-here', 'User')
```

**Linux/macOS:**
```bash
export ZAI_API_KEY="your-api-key-here"
```

To make it permanent, add to your `~/.bashrc` or `~/.zshrc`:
```bash
echo 'export ZAI_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

#### Verify Configuration

Test the API connection:

```bash
curl --location 'https://api.z.ai/api/coding/paas/v4/chat/completions' \
  --header "Authorization: Bearer $ZAI_API_KEY" \
  --header 'Content-Type: application/json' \
  --data '{
    "model": "glm-4.6",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant"},
      {"role": "user", "content": "Say hello"}
    ],
    "temperature": 0.95
  }'
```

Expected response: JSON with a `choices` array containing the model's response.

### 4. Configure Repository Root

Edit `config/config.yaml` and set your repos directory:

```yaml
repos_root: "C:\\your\\repos\\directory"  # Windows path with escaped backslashes
```

### 5. MCP Server Setup (Optional)

For desktop automation, you can either:

**Option A: Use MCP Server** (Recommended for production)
- Set up an MCP server running on `http://127.0.0.1:43110`
- See [MCP documentation](https://modelcontextprotocol.io) for server setup

**Option B: Use Fallback Adapter** (For testing)
- Install fallback dependencies: `pip install -e .[fallback]`
- Change `config/config.yaml`:
  ```yaml
  adapters:
    type: "fallback"  # Changed from "mcp"
  ```

### 6. Initialize State Directory

Create the state directory structure:

```bash
mkdir -p state/checkpoints
mkdir -p state/episodes
```

Create initial world state:

```bash
echo '{"repos": {}, "last_heartbeat": 0}' > state/world_state.json
```

### 7. Configure Your Plan

Edit `plans/plan.yaml` to define your objectives and tasks:

```yaml
objectives:
  - id: team-alignment
    description: Keep Copilot Chat synchronized with team plans
    cadence: hourly

tasks:
  - task_id: nudge-copilot
    repo_selectors:
      - "all"  # Or specific repo names
    actions:
      - harvest_chat
      - post_nudge
    policy: "pr:open, stale>1d"
```

## Usage

### Test Configuration

Scan repositories and validate configuration:

```bash
agent-cli scan
```

This will output the discovered repositories and loaded plan.

### Run Once (Dry Run)

Execute one cycle with screenshots only (no keyboard input):

```bash
agent-cli run-once
```

Check `state/episodes/` for execution traces and screenshots.

### Enable Write Mode

To actually interact with VS Code and Copilot Chat:

1. Edit `config/config.yaml`:
   ```yaml
   write_mode: true  # Changed from false
   ```

2. Run:
   ```bash
   agent-cli run-once
   ```

### Run Continuous Loop

Run every 30 minutes (default):

```bash
agent-cli run-loop
```

Or specify custom interval:

```bash
agent-cli run-loop --interval-sec 3600  # Every hour
```

### Run Watchdog (Auto-Resume)

For production deployment with automatic recovery:

```bash
agent-watchdog
```

This monitors the heartbeat and automatically restarts the agent if it stalls.

## Verification

### Check LLM Integration

The Reasoner agent should now use GLM-4.6 for intelligent task selection. Look for logs like:

```
[Reasoner] Selected: my-repo/nudge-copilot
[Reasoner] Reasoning: Selected this repo because it has 3 open PRs waiting for review and aligns with team-alignment objective
```

### Monitor API Usage

Z.ai Coding Plan provides free API calls. Monitor your usage at: [https://z.ai/dashboard](https://z.ai/dashboard)

### Troubleshooting

**"API key not found" error:**
- Verify `ZAI_API_KEY` environment variable is set
- Restart your terminal/IDE to pick up new environment variables

**"Connection refused" for MCP:**
- Check MCP server is running on `http://127.0.0.1:43110`
- Or switch to fallback adapter in config

**"No work items available":**
- Verify `repos_root` points to directory containing git repositories
- Check `plans/plan.yaml` has valid task definitions
- Run `agent-cli scan` to debug

**LLM selection failing:**
- Check API key has sufficient credits
- Verify network connectivity to `https://api.z.ai`
- Check logs for specific error messages
- System will fallback to round-robin selection if LLM fails

## Architecture

The system now uses **GLM-4.6 for intelligent reasoning**:

1. **ScanRepos**: Discovers git repositories and PR status
2. **SyncPlan**: Loads plan.yaml and creates work items
3. **ReasonStep**: **GLM-4.6 analyzes repos and selects highest-priority task**
4. **ActStep**: Executes desktop automation to interact with Copilot Chat
5. **ValidateEvidence**: Checks screenshots and artifacts
6. **Persist**: Saves traces and updates heartbeat

The **Reasoner Agent** is no longer "automation theater" - it uses real AI to:
- Prioritize tasks based on repo health
- Consider PR status and blockers
- Balance work across repositories
- Generate context-appropriate messages for Copilot Chat

## Next Steps

- Review [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed system design
- Check [PILLARS.md](./PILLARS.md) for core requirements
- Read [README.md](./README.md) for project overview
- See `state/episodes/` for execution traces

## Security

- Never commit `.env` files or API keys to git
- Use environment variables for all secrets
- Keep `write_mode: false` until you've verified behavior
- Review window title regex to prevent wrong window interaction
