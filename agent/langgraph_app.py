
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

# Maximum retry attempts before giving up
MAX_RECOVERY_ATTEMPTS = 2

def _should_recover(state: Dict[str, Any]) -> str:
    """
    Determine if ActStep failed and should trigger recovery.

    Returns:
        - "Recovery" if failed and retry count < MAX_RECOVERY_ATTEMPTS
        - "ValidateEvidence" otherwise (success or exhausted retries)
    """
    action_report = state.get("action_report", {})
    status = action_report.get("status")
    retry_count = state.get("_recovery_retry_count", 0)

    # Check if ActStep failed
    if status == "failed" and retry_count < MAX_RECOVERY_ATTEMPTS:
        return "Recovery"

    # Either succeeded or exhausted retries - continue to validation
    return "ValidateEvidence"

def _should_recover_after_validation(state: Dict[str, Any]) -> str:
    """
    Determine if validation failed (vision detected issues) and should retry.

    Returns:
        - "Recovery" if validation failed and retry count < MAX_RECOVERY_ATTEMPTS
        - "Persist" otherwise (validation passed or exhausted retries)
    """
    validated = state.get("validated", True)
    retry_count = state.get("_recovery_retry_count", 0)

    # If validation failed (vision saw errors/busy/closed chat)
    if not validated and retry_count < MAX_RECOVERY_ATTEMPTS:
        return "Recovery"

    # Either validated successfully or exhausted retries
    return "Persist"

def _increment_retry_wrapper(node_func):
    """Wrapper to increment retry counter when entering Recovery."""
    def wrapper(state: Dict[str, Any]) -> Dict[str, Any]:
        # Increment retry counter
        state["_recovery_retry_count"] = state.get("_recovery_retry_count", 0) + 1
        return node_func(state)
    return wrapper

def build_graph(sqlite_path: str):
    g = StateGraph(dict)
    g.add_node("ScanRepos", scan_repos)
    g.add_node("SyncPlan", sync_plan)
    g.add_node("ReasonStep", reason_step)
    g.add_node("ActStep", act_step)
    g.add_node("ValidateEvidence", validate_evidence)
    g.add_node("Persist", persist)
    # Wrap recovery to increment retry counter
    g.add_node("Recovery", _increment_retry_wrapper(recovery))

    g.set_entry_point("ScanRepos")
    g.add_edge("ScanRepos", "SyncPlan")
    g.add_edge("SyncPlan", "ReasonStep")
    g.add_edge("ReasonStep", "ActStep")

    # CRITICAL: Conditional routing after ActStep
    # If failed → Recovery (up to MAX_RECOVERY_ATTEMPTS)
    # Otherwise → ValidateEvidence
    g.add_conditional_edges(
        "ActStep",
        _should_recover,
        {
            "Recovery": "Recovery",
            "ValidateEvidence": "ValidateEvidence"
        }
    )

    # After recovery, reset retry counter and try ActStep again
    def _reset_and_retry(state: Dict[str, Any]) -> Dict[str, Any]:
        # Clear the failure status to allow retry
        if "action_report" in state:
            state["action_report"]["status"] = "retrying"
        return state

    g.add_node("ResetRetry", _reset_and_retry)
    g.add_edge("Recovery", "ResetRetry")
    g.add_edge("ResetRetry", "ActStep")

    # CRITICAL: Conditional routing after ValidateEvidence
    # If validation failed (vision detected issues) → Recovery
    # Otherwise → Persist
    g.add_conditional_edges(
        "ValidateEvidence",
        _should_recover_after_validation,
        {
            "Recovery": "Recovery",
            "Persist": "Persist"
        }
    )

    # Final persistence
    g.add_edge("Persist", END)

    memory = SqliteSaver(sqlite_path)
    return g.compile(checkpointer=memory)
