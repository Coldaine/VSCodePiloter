
from __future__ import annotations
from typing import Dict, Any, Optional
from agent.observability import span
from agent.prompts import reasoner_system_txt as _rs

def _select_next_work_item(state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    items = state.get("work_items", [])
    if not items:
        return None
    # naive round-robin for now
    idx = state.get("_next_idx", 0) % len(items)
    state["_next_idx"] = idx + 1
    return items[idx]

def reason_step(state: Dict[str, Any]) -> Dict[str, Any]:
    with span("ReasonStep"):
        wi = _select_next_work_item(state)
        if not wi:
            state["task_envelope"] = None
            return state
        repo = state["repos"][wi["repo_name"]]
        # Create an open-ended envelope; allow extras as needed
        envelope = {
            "type": "desktop_task",
            "intent": "harvest_and_nudge",
            "target_repo_path": repo["path"],
            "payload": {
                "message_to_post": "Sync on current plan and blockers.",
                "copy_scope": {"mode":"last_n", "n":10}
            },
            "meta": {
                "task_id": wi["id"] if "id" in wi else wi["task_id"],
                "repo_name": wi["repo_name"]
            }
        }
        state["task_envelope"] = envelope
        return state
