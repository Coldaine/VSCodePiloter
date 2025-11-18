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

VSCodePiloter uses Z.ai's GLM-4.6 model for intelligent task reasoning. The system includes **automatic secret management** that works across all environments (local, CI/CD, cloud).

#### Automatic Secret Detection (NEW - Recommended)

The system automatically detects your environment and uses the appropriate secret backend:

```bash
# The system will automatically:
# - Use Bitwarden if BWS_ACCESS_TOKEN is set (local dev)
# - Use environment variables in CI/CD (GitHub Actions, etc.)
# - Fall back to .env files if present

# No configuration needed - just run:
agent-cli run-once
```

For detailed information, see [Secret Management Documentation](docs/SECRET_MANAGEMENT.md).

#### Option A: Retrieve from Bitwarden Secrets Manager (Local Development)

If you store your API keys in Bitwarden Secrets Manager, use the provided helper script for secure retrieval:

**Prerequisites:**
- Bitwarden Secrets Manager CLI (`bws`) installed
- `BWS_ACCESS_TOKEN` environment variable set with your access token
- Secret named `Z_AI_API_KEY` exists in your Bitwarden organization

**Install Bitwarden Secrets Manager CLI:**
```bash
# Windows (PowerShell)
winget install Bitwarden.BWS

# macOS
brew install bitwarden/tap/bws

# Linux
# Download from https://bitwarden.com/help/secrets-manager-cli/
```

**Set Your BWS Access Token:**
```powershell
# Windows (PowerShell)
$env:BWS_ACCESS_TOKEN = "your-bws-access-token"

# Linux/macOS (Bash)
export BWS_ACCESS_TOKEN="your-bws-access-token"
```

Get your access token from: https://vault.bitwarden.com/#/settings/security/security-keys

**Run the Helper Script:**

**Windows:**
```powershell
.\scripts\get_api_key.ps1
```

**Linux/macOS:**
```bash
source ./scripts/get_api_key.sh
```

The script will:
- Retrieve the `Z_AI_API_KEY` secret from Bitwarden
- Set the `ZAI_API_KEY` environment variable for your current session
- Display instructions for making it permanent
- Show a preview of the key (first 8 characters)

**Verify the key was retrieved:**
```bash
echo $env:ZAI_API_KEY  # PowerShell
echo $ZAI_API_KEY       # Bash
```

#### Option B: Manual API Key Setup

If you don't use Bitwarden, you can set the API key manually.

**Get Your Z.ai API Key:**

1. Sign up at [https://z.ai](https://z.ai)
2. Subscribe to the **GLM Coding Plan** ($3/month, free coding calls available)
3. Go to your dashboard and generate an API key

**Set Environment Variable:**

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

### 5. Windows-MCP Setup

VSCodePiloter uses **Windows-MCP** for desktop automation via stdio communication.

**Automatic Configuration (Recommended):**

The system automatically uses Windows-MCP via npx if available:

```bash
# The system will automatically run:
# npx -y @curtsortouch/windows-mcp
# No manual setup required!
```

**Manual Verification:**

Test Windows-MCP is available:

```bash
# Check npx is installed (comes with Node.js)
npx --version

# Test Windows-MCP
npx -y @curtsortouch/windows-mcp
```

**Configuration Options:**

The default configuration in `config/config.yaml` uses stdio transport:

```yaml
adapters:
  type: "mcp"  # MCP adapter with stdio
  mcp:
    transport: "stdio"  # Recommended: stdio communication
    # Optional: Override auto-detection
    # command: "npx"
    # args: ["-y", "@curtsortouch/windows-mcp"]
```

**Alternative: Legacy HTTP Mode**

If you have an MCP HTTP server running:

```yaml
adapters:
  type: "mcp"
  mcp:
    transport: "http"  # Use HTTP instead of stdio
    base_url: "http://127.0.0.1:43110"
    jsonrpc: false
```

**Fallback Adapter (Testing Only):**

For testing without MCP:

```bash
pip install -e .[fallback]
```

Edit `config/config.yaml`:
```yaml
adapters:
  type: "fallback"  # Use pyautogui
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

**"Windows-MCP connection error":**
- Verify npx is installed: `npx --version`
- Install Node.js if needed: https://nodejs.org/
- Test Windows-MCP manually: `npx -y @curtsortouch/windows-mcp`
- Check stdio transport is configured in `config/config.yaml`
- Or switch to fallback adapter for testing

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

The system uses **dual AI models** for intelligent orchestration:

### Text Model: GLM-4.6 (Reasoning)
1. **ScanRepos**: Discovers git repositories and PR status
2. **SyncPlan**: Loads plan.yaml and creates work items
3. **ReasonStep**: **GLM-4.6 analyzes repos and selects highest-priority task**
4. **ActStep**: Executes desktop automation to interact with Copilot Chat
5. **ValidateEvidence**: **GLM-4.5V verifies actions via screenshot analysis**
6. **Persist**: Saves traces and updates heartbeat

### Vision Model: GLM-4.5V (Screenshot Analysis)
The **Vision Actor** uses GLM-4.5V to:
- Analyze VS Code window screenshots
- Verify Copilot Chat state (open/closed/busy)
- Validate that actions succeeded
- Detect UI errors for recovery

### Intelligent Capabilities
The **Reasoner Agent** uses real AI to:
- Prioritize tasks based on repo health
- Consider PR status and blockers
- Balance work across repositories
- Generate context-appropriate messages for Copilot Chat

The **Vision Actor** can:
- Read text from screenshots
- Detect UI state changes
- Verify window focus and content
- Provide feedback for error recovery

## Testing

### Run Tests

```bash
# Run all unit tests
pytest tests/ -v

# Run integration tests (requires API key)
pytest tests/integration/ -v -m integration

# Run performance benchmarks
pytest tests/benchmarks/ -v -m benchmark

# Run with coverage
pytest --cov=agent --cov-report=html tests/
```

### Test Requirements

- **Unit tests**: No special requirements
- **Integration tests**: Require `ZAI_API_KEY` environment variable
- **VS Code tests**: Require VS Code running and Windows-MCP available
- **Benchmarks**: Require API key and optionally VS Code

See [docs/testing.md](docs/testing.md) for comprehensive testing guide.

## Next Steps

- Review [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed system design
- Check [PILLARS.md](./PILLARS.md) for core requirements
- Read [README.md](./README.md) for project overview
- See [docs/testing.md](docs/testing.md) for testing procedures
- Review [docs/performance.md](docs/performance.md) for performance benchmarks
- See `state/episodes/` for execution traces

## Security

- Never commit `.env` files or API keys to git
- Use environment variables for all secrets
- Keep `write_mode: false` until you've verified behavior
- Review window title regex to prevent wrong window interaction
