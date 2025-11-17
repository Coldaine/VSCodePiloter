
from __future__ import annotations
import json, os, time
from typing import Any, Dict

WORLD_STATE_PATH = "state/world_state.json"

def read_world_state() -> Dict[str, Any]:
    if not os.path.exists(WORLD_STATE_PATH):
        return {"repos_root": "", "repos": {}, "last_heartbeat": None}
    with open(WORLD_STATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def write_world_state(state: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(WORLD_STATE_PATH), exist_ok=True)
    with open(WORLD_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def heartbeat() -> None:
    ws = read_world_state()
    ws["last_heartbeat"] = int(time.time())
    write_world_state(ws)
