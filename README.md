
# LangGraph VSCode Multi-Agent (Windows 11)

**Purpose**: A production-ready scaffold for a two-agent system that:
- Orchestrates a **Reasoner** + **Vision Actor** in **LangGraph**.
- Manages **multiple VS Code windows** reliably on **Windows 11**.
- Uses **MCP adapters** for OS automation (list/focus windows, screenshots, keystrokes, text, clipboard).
- Periodically **nudges GitHub Copilot Chat** across repos and harvests context.
- Auto-resumes when stuck; checkpoints, observability, and plan/state persistence baked in.

> No mocks. The code runs as-is when you supply your MCP server endpoints (or enable the optional fallback adapter).

---

## Quick Start

### 1) Requirements
- Windows 11, Python 3.11+
- Git + GitHub CLI (`gh`) installed and on PATH
- A desktop automation **MCP server** reachable locally (HTTP/JSON or JSON-RPC over HTTP).  
  You can map its endpoints in `config/config.yaml` under `adapters.mcp.endpoints`.

> **Note**: This repo ships with a thin MCP HTTP adapter. If your server speaks stdio/WebSocket, lift the `mcp/client.py` to the right transport or drop in your own adapter with the same interface. An optional **local fallback** using `pyautogui` exists (off by default).

### 2) Install

```bash
pip install -e .
```

### 3) Configure
Edit `config/config.yaml`:
- `repos_root`: absolute path holding your git clones
- `adapters.mcp.base_url`: e.g., `http://127.0.0.1:43110`
- Endpoint mappings if needed
- Set the window title pattern you use (recommended to include `${folderPath}` in VS Code settings)

### 4) Run (once)

```bash
agent-cli run-once
```

### 5) Run watchdog (auto every ~30 min)
```bash
agent-watchdog
```

### 6) Dry-run vs Write
- Dry-run: captures screenshots and **does not** type/paste into VS Code.
- Write-mode: enables keystrokes and text input. Configure in `config.yaml` or CLI flags.

---

## Pillars Implemented

1. **LangGraph-first orchestration** with persistent plan & checkpoints.
2. **Auto-resume + watchdog** every ~30 minutes with recovery nodes.
3. **Multi-window VS Code control** via allow-listed titles + vision verification.
4. **Copilot Chat handling**: open/focus, busy-detect, copy transcript, post messages.
5. **Repo/PR scanning** with `git`/`gh` CLI; persistent `plan.yaml` + `world_state.json`.
6. **Two-agent loop**: Reasoner (planning) + Vision Actor (stateless, fresh context).
7. **Reuse-first**: pluggable **MCP** adapter; minimal net-new automation.
8. **Flexible Reasoner↔Actor contract** with open `payload/details/meta` fields.
9. **Observability**: spans, events, artifacts (screenshots), episodes on disk; OTLP hooks.
10. **Guardrails**: window allow-list; propose→verify→execute; rate limits; dry-run mode.

---

## Repo Layout

```
agent/
  __init__.py
  config.py
  main.py
  langgraph_app.py
  state_store.py
  observability.py
  prompts/
    reasoner_system.txt
    actor_system.txt
  nodes/
    scan_repos.py
    sync_plan.py
    reason_step.py
    act_step.py
    validate_evidence.py
    persist.py
    recovery.py
  adapters/
    __init__.py
    base.py
    mcp_adapter.py        # default
    fallback_adapter.py   # optional non-MCP (pyautogui)
  mcp/
    __init__.py
    client.py
  tools/
    git_ops.py
    gh_ops.py
config/
  config.yaml
plans/
  plan.yaml
state/
  world_state.json
  episodes/            # run traces
  checkpoints/         # langgraph sqlite db
tests/
  test_sanity.py
```

---

## Configure MCP (HTTP) Adapter

In `config/config.yaml`:

```yaml
adapters:
  type: "mcp"
  mcp:
    base_url: "http://127.0.0.1:43110"
    endpoints:
      list_windows: "/windows/list"
      focus_window: "/windows/focus"
      screenshot: "/windows/screenshot"
      keypress: "/input/keypress"
      text_input: "/input/text"
      clipboard_get: "/clipboard/get"
      clipboard_set: "/clipboard/set"
```

> Adjust endpoints to match your server. The adapter posts JSON like `{"keys": "Ctrl+Shift+P"}` or `{"hwnd": 12345}` and expects JSON replies. If your server is JSON-RPC, set `jsonrpc: true` in the same block and the adapter will wrap calls automatically.

---

## VS Code Tips (for robust mapping)

- Set your window titles to include the folder path:
  ```json
  "window.title": "${dirty}${activeEditorShort}${separator}${folderPath}${separator}${appName}"
  ```
- Prefer Command Palette actions over brittle key combos when driving Copilot Chat.
- Ensure `code` CLI is on PATH; we use it only to **open** missing windows (`code -r <path>`).

---

## Safety

- **Dry-run mode** by default: no keystrokes are sent unless you enable write-mode.
- Two-phase execution: **propose → verify (screenshot) → execute**.
- Allow-listed VS Code windows only (regex configurable).

---

## License

MIT (see `LICENSE`).
