# Changelog

All notable changes to VSCodePiloter will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Stdio MCP Adapter** (`agent/adapters/stdio_mcp_adapter.py`) - Standard MCP protocol support via JSON-RPC over stdin/stdout
- **Claude Desktop Integration** (`agent/adapters/claude_config.py`) - Auto-detect and reuse MCP servers configured in Claude Desktop
- **VSCodeCopilotMonitor** (`agent/tools/vscode_copilot_monitor.py`) - High-level wrapper for monitoring VS Code Copilot Chat across multiple windows
- **Recovery Node Wiring** - Connected Recovery node to ActStep with conditional routing and retry logic
- **Transport Configuration** - `transport: "stdio"` option in config.yaml for MCP adapter selection
- `.vscode/settings.json` - VS Code workspace settings for window title formatting and pytest configuration
- `.github/copilot-instructions.md` - Project-specific AI coding agent instructions
- **Pre-commit hooks** (`.pre-commit-config.yaml`) with ruff lint/format and basic hygiene hooks
- **Testing framework**: pytest markers (unit/integration/acceptance), env-gated skips, coverage config, and `tests/conftest.py`

### Changed
- **Default MCP Server** - Changed from HTTP-based custom server to Windows-MCP via stdio (npx fallback)
- **MCP Adapter Selection** - Now auto-detects from Claude Desktop config, falls back to `npx -y @curtsortouch/windows-mcp`
- **Config Schema** - Updated `config.yaml` to support stdio/http transport selection
- **README.md** - Clarified MCP requirements, removed HTTP endpoint instructions, added Windows-MCP integration
- **ARCHITECTURE.md** - Updated adapter descriptions, marked Recovery node as implemented, added MCP stdio transport section
- **PILLARS.md** - Updated Pillar 3 and Pillar 7 to reflect stdio transport and VSCodeCopilotMonitor

### Removed
- Custom local MCP HTTP server implementation (`mcp_server/server.py`) - Replaced with standard MCP stdio approach
- HTTP-only MCP adapter configuration - Now legacy option, stdio is default

### Fixed
- Recovery node was defined but not connected to graph flow - now properly wired with conditional edges
- MCP transport mismatch - system expected HTTP but standard MCP servers use stdio

## [0.1.0] - 2025-11-17

### Added
- Initial LangGraph-based two-agent architecture (Reasoner + Vision Actor)
- Z.ai GLM-4.6 integration for intelligent task reasoning (355B MoE, 32B active)
- Z.ai GLM-4.5V integration for screenshot analysis (106B MoE, 12B active)
- Secret management with Bitwarden Secrets Manager and environment variable fallback
- LangGraph state machine: ScanRepos → SyncPlan → ReasonStep → ActStep → ValidateEvidence → Persist
- Git/GitHub CLI integration for repository and PR scanning
- Persistent plan management (`plans/plan.yaml`)
- World state tracking (`state/world_state.json`)
- Episode logging with spans and artifacts (`state/episodes/`)
- SQLite checkpointing for LangGraph state
- Watchdog script for auto-resume every ~30 minutes
- Dry-run mode (default) for safe testing without keyboard/mouse input
- Window allow-listing via regex for safety
- Fallback adapter using pyautogui for direct Windows automation
- Command-line interface: `agent-cli run-once`, `agent-cli run-loop`, `agent-watchdog`
- Comprehensive test suite: `test_llm_client.py`, `test_secret_providers.py`, `test_vscode_monitor.py`
- Documentation: README.md, ARCHITECTURE.md, PILLARS.md, SETUP.md, CLAUDE.md, SECRET_MANAGEMENT.md

### Architecture Decisions
- Sprint 1 focused on LLM integration and secret management
- No mocks allowed for acceptance testing - real components only
- Two-phase execution: propose → verify (screenshot) → execute
- Reasoner uses temperature 0.7 for deterministic decisions
- Vision Actor uses temperature 0.95 for creative interpretation
- Separate endpoints for text (coding) and vision (standard) models

---

## Version History Summary

- **0.1.0** (2025-11-17) - Initial release with LLM integration, secret management, LangGraph orchestration
- **Unreleased** - MCP stdio transport, Claude Desktop integration, VSCodeCopilotMonitor, Recovery node wiring
