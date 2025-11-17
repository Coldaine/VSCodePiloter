
from __future__ import annotations
import time
from typing import Dict, Any
from agent.observability import span, log_event
from agent.adapters.base import DesktopAdapter

def recovery(state: Dict[str, Any]) -> Dict[str, Any]:
    adapter: DesktopAdapter = state.get("_adapter")
    with span("Recovery"):
        # Simple recovery: try to refocus VS Code and retry a palette open
        try:
            adapter.focus_window(title_regex=state.get("_settings").window_title_regex)
            time.sleep(0.2)
            if state.get("_settings").write_mode:
                adapter.keypress("Ctrl+Shift+P")
                time.sleep(0.1)
        except Exception as e:
            log_event("recovery.failed", {"error": str(e)})
        return state
