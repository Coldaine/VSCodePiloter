
from __future__ import annotations
import yaml
from typing import Dict, Any
from agent.observability import span

def sync_plan(state: Dict[str, Any]) -> Dict[str, Any]:
    with span("SyncPlan"):
        with open("plans/plan.yaml", "r", encoding="utf-8") as f:
            plan = yaml.safe_load(f)
        state["plan"] = plan
        work_items = []
        repos = state.get("repos", {})
        for t in plan.get("tasks", []):
            selector = t.get("repo_selector", "all")
            targets = list(repos.keys()) if selector == "all" else [selector]
            for repo_name in targets:
                work_items.append({
                    "task_id": t["id"],
                    "repo_name": repo_name,
                    "actions": t.get("actions", [])
                })
        state["work_items"] = work_items
        return state
