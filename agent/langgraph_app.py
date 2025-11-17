
from __future__ import annotations
from typing import Any, Dict
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from agent.nodes.scan_repos import scan_repos
from agent.nodes.sync_plan import sync_plan
from agent.nodes.reason_step import reason_step
from agent.nodes.act_step import act_step
from agent.nodes.validate_evidence import validate_evidence
from agent.nodes.persist import persist
from agent.nodes.recovery import recovery

def build_graph(sqlite_path: str):
    g = StateGraph(dict)
    g.add_node("ScanRepos", scan_repos)
    g.add_node("SyncPlan", sync_plan)
    g.add_node("ReasonStep", reason_step)
    g.add_node("ActStep", act_step)
    g.add_node("ValidateEvidence", validate_evidence)
    g.add_node("Persist", persist)
    g.add_node("Recovery", recovery)

    g.set_entry_point("ScanRepos")
    g.add_edge("ScanRepos", "SyncPlan")
    g.add_edge("SyncPlan", "ReasonStep")
    g.add_edge("ReasonStep", "ActStep")
    g.add_edge("ActStep", "ValidateEvidence")
    g.add_edge("ValidateEvidence", "Persist")
    g.add_edge("Persist", END)

    memory = SqliteSaver(sqlite_path)
    return g.compile(checkpointer=memory)
