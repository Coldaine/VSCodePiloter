
from __future__ import annotations
import argparse, os, time, json
from agent.config import load_settings, Settings
from agent.state_store import read_world_state, write_world_state, heartbeat
from agent.langgraph_app import build_graph
from agent.adapters.base import DesktopAdapter
from agent.adapters.mcp_adapter import MCPAdapter
from agent.adapters.fallback_adapter import FallbackAdapter
from agent.adapters.stdio_mcp_adapter import StdioMCPAdapter
from agent.observability import log_event
def _adapter_from_settings(settings: Settings) -> DesktopAdapter:
    if settings.adapters.type == "mcp":
        m = settings.adapters.mcp
        transport = getattr(m, 'transport', 'stdio')
        
        if transport == "stdio":
            # Use stdio MCP adapter (standard MCP protocol)
            from agent.adapters.stdio_mcp_adapter import StdioMCPAdapter
            from agent.adapters.claude_config import get_default_mcp_server_config
            
            # Check for explicit config, otherwise auto-detect from Claude Desktop
            if hasattr(m, 'command') and m.command:
                config = {
                    'command': m.command,
                    'args': getattr(m, 'args', []),
                    'env': getattr(m, 'env', {})
                }
            else:
                config = get_default_mcp_server_config()
            
            return StdioMCPAdapter(
                command=config['command'],
                args=config['args'],
                env=config.get('env', {})
            )
        else:
            # Legacy HTTP transport
            return MCPAdapter(m.base_url, endpoints=m.endpoints, jsonrpc=m.jsonrpc)
    
    elif settings.adapters.type == "mcp-http":
        # Explicit HTTP-based MCP
        m = settings.adapters.mcp
        return MCPAdapter(m.base_url, endpoints=m.endpoints, jsonrpc=m.jsonrpc)
    elif settings.adapters.type == "fallback":
        return FallbackAdapter()
    else:
        raise ValueError(f"Unknown adapter type: {settings.adapters.type}")e))
    elif settings.adapters.type == "fallback":
        return FallbackAdapter()
    else:
        raise ValueError(f"Unknown adapter type: {settings.adapters.type}")

def run_once(settings: Settings):
    app = build_graph(settings.checkpoint_db)
    ws = read_world_state()
    ws["repos_root"] = settings.repos_root
    # Pass non-serializable objects in the state via underscored keys
    adapter = _adapter_from_settings(settings)
    initial = {**ws, "_settings": settings, "_adapter": adapter}
    result = app.invoke(initial)
    # Persist heartbeat
    heartbeat()
    # Save the (possibly updated) world state fields back
    ws.update({k: v for k, v in result.items() if k in ("repos", "plan")})
    write_world_state(ws)
    return result

def run_loop(settings: Settings, interval_sec: int = 1800):
    while True:
        try:
            run_once(settings)
        except Exception as e:
            log_event("run.error", {"error": str(e)})
        time.sleep(interval_sec)

def cli():
    parser = argparse.ArgumentParser(prog="agent-cli", description="LangGraph VSCode Multi-Agent")
    parser.add_argument("command", choices=["run-once", "run-loop", "scan", "nudge-chats"])
    parser.add_argument("--config", default="config/config.yaml")
    parser.add_argument("--interval-sec", type=int, default=1800)
    args = parser.parse_args()

    settings = load_settings(args.config)

    if args.command == "run-once":
        run_once(settings)
        print("DONE")
    elif args.command == "run-loop":
        run_loop(settings, interval_sec=args.interval_sec)
    elif args.command == "scan":
        # Quick run that stops after ScanRepos + SyncPlan
        from agent.langgraph_app import build_graph
        app = build_graph(settings.checkpoint_db)
        ws = read_world_state()
        ws["repos_root"] = settings.repos_root
        adapter = _adapter_from_settings(settings)
        initial = {**ws, "_settings": settings, "_adapter": adapter}
        partial = app.invoke(initial, add_to_memory=False, until=["SyncPlan"])
        print(json.dumps({k: partial[k] for k in ("repos","plan") if k in partial}, indent=2))
    elif args.command == "nudge-chats":
        # Run ReasonStep -> ActStep only
        from agent.langgraph_app import build_graph
        app = build_graph(settings.checkpoint_db)
        ws = read_world_state()
        ws["repos_root"] = settings.repos_root
        adapter = _adapter_from_settings(settings)
        initial = {**ws, "_settings": settings, "_adapter": adapter}
        partial = app.invoke(initial, add_to_memory=False, until=["Persist"])
        print("Nudged chats. See state/episodes for evidence.")
