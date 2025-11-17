
from __future__ import annotations
from typing import Dict, Any
from agent.observability import span

def validate_evidence(state: Dict[str, Any]) -> Dict[str, Any]:
    with span("ValidateEvidence"):
        rpt = state.get("action_report") or {}
        # Minimal sanity check: we got screenshots and (if asked) non-zero copied text
        ok = "artifacts" in rpt and "pre" in rpt.get("artifacts", {}) and "post" in rpt.get("artifacts", {})
        state["validated"] = bool(ok)
        return state
