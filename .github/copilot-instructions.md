## Overview

This repository is a LangGraph-based two-agent system (Reasoner + Vision Actor) that orchestrates GitHub Copilot Chat across multiple VS Code windows on Windows 11. Start here: `README.md` and `ARCHITECTURE.md`.

## Quick Start Notes for AI Coding Agents
- **Platform**: Windows 11 (native). Python 3.11+. Not designed for WSL.
- **Install**: `pip install -e .`
- **Run a single cycle (dry-run default)**: `agent-cli run-once`
- **Run watchdog (auto-resume)**: `agent-watchdog`
- **Run tests**: `pytest tests/` (integration tests require real VS Code + MCP)

## Where to look first
- `README.md` — high-level purpose, commands, pillars.
- `ARCHITECTURE.md` — dataflow, LangGraph node sequence, guarantees and gaps.
- `docs/plans/Sprint1.md` + `CLAUDE.md` — sprint workflow; update sprint checklist when you finish tasks.
- `config/config.yaml` — runtime switches (e.g. `write_mode`, `adapters.type`, `adapters.mcp.endpoints`).

## Key Code Areas and Patterns
- `agent/` — core app: `main.py`, `langgraph_app.py`, `state_store.py`, `observability.py`.
- `agent/llm_client.py` — specialized clients: use `glm-4.6` (coding endpoint) for Reasoner and `glm-4.5v` (paas endpoint) for vision. Endpoints are different — do not mix.
- `agent/prompts/` — canonical system prompts: `reasoner_system.txt`, `actor_system.txt` (use these instead of inventing new system prompt formats).
- `agent/nodes/` — LangGraph node implementations (ScanRepos → SyncPlan → ReasonStep → ActStep → ValidateEvidence → Persist). Look at `act_step.py` for MCP interaction flow.
- `agent/adapters/` — adapter pattern: `mcp_adapter.py` (HTTP JSON to MCP server) and `fallback_adapter.py` (pyautogui). Swap by editing `config/config.yaml`.
- `agent/secrets/` — Bitwarden + envvar composite provider; prefer Bitwarden (`bws`) or env vars; do NOT hardcode API keys.

## Project-specific conventions (do not assume defaults)
- Dry-run default: the system captures screenshots and never types unless `write_mode: true` in `config/config.yaml` or CLI flags enable it.
- Two-phase execution for any GUI action: **propose → verify (screenshot) → execute**. Tests and patches must preserve this pattern.
- Acceptance tests: must use real components (NO MOCKS). Unit tests may mock, but integration/acceptance tests require real MCP server, real VS Code windows, and real LLM calls.
- Window selection: rely on a configurable window-title regex in `config.yaml`. Prefer changing VS Code `window.title` to include `${folderPath}` for reliability.

## LLM & Vision specifics (critical)
- Text Reasoner: Model `glm-4.6` via `https://api.z.ai/api/coding/paas/v4/` (coding endpoint). Use `agent/llm_client.py` helpers.
- Vision model: Model `glm-4.5v` via `https://api.z.ai/api/paas/v4/` (paas endpoint). Vision MUST NOT use the coding endpoint — endpoints and payload formats differ.
- Auth: `ZAI_API_KEY` environment variable; prefer retrieving via Bitwarden (see `scripts/get_api_key.ps1` and `SETUP.md`).

## MCP Adapter and Automation
- Default adapter: `adapters/mcp_adapter.py` — maps JSON calls to MCP endpoints defined in `config/config.yaml`.
- Fallback: `adapters/fallback_adapter.py` (pyautogui) — install extras with `pip install -e .[fallback]`.
- Important: MCP adapter currently lacks retry logic — handle HTTP failures conservatively or implement retries in adapter if necessary.

## Tests & CI expectations
- Unit tests can mock small helpers; acceptance tests must be real (see `ARCHITECTURE.md` testing section).
- Integration tests that exercise desktop automation require a running MCP server + live VS Code instances and valid `ZAI_API_KEY`.

## Common commands (copyable)
```
pip install -e .
python -m venv venv
venv\Scripts\activate    # Windows PowerShell
agent-cli run-once
agent-watchdog
pytest tests/
```

## What to update when you finish work
- Update `docs/plans/Sprint1.md` checkboxes per the relay workflow (`CLAUDE.md`) so subsequent agents know progress.
- Add a short commit message listing changed files and updated sprint items.

## Quick do/don't checklist
- Do: preserve two-phase propose→verify→execute.
- Do: reference `agent/prompts/*` and `agent/llm_client.py` helpers for LLM calls.
- Do: keep secrets out of git; use `bws` or env vars.
- Don't: change LLM endpoints or model names arbitrarily (use exact names `glm-4.6`, `glm-4.5v`).
- Don't: run acceptance tests without MCP server and real VS Code windows.

---
If any of these areas are unclear or you want more examples (e.g., a minimal integration test harness), tell me which section to expand and I'll iterate.
