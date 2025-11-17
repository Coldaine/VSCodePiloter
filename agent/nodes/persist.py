
from __future__ import annotations
import os, json, time
from typing import Dict, Any
from agent.observability import span, _episode_dir

def persist(state: Dict[str, Any]) -> Dict[str, Any]:
    with span("Persist"):
        run_dir = _episode_dir()
        fname = f"trace_{int(time.time())}.json"
        path = os.path.join(run_dir, fname)
        snap = {
            "ts": int(time.time()),
            "task_envelope": state.get("task_envelope"),
            "action_report": state.get("action_report"),
            "validated": state.get("validated", False)
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(snap, f, indent=2)
        return state
