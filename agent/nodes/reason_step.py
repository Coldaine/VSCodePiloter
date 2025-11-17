
from __future__ import annotations
import json
from typing import Dict, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from agent.observability import span
from agent.prompts import reasoner_system_txt as _rs
from agent.llm_client import create_reasoner_llm


def _format_repo_context(repos: Dict[str, Any]) -> str:
    """Format repository information for LLM context."""
    context_parts = []
    for repo_name, repo_info in repos.items():
        context_parts.append(f"\n## Repository: {repo_name}")
        context_parts.append(f"Path: {repo_info.get('path', 'unknown')}")
        context_parts.append(f"Current branch: {repo_info.get('current_branch', 'unknown')}")

        # Add PR information if available
        prs = repo_info.get("prs", [])
        if prs:
            context_parts.append(f"Open PRs: {len(prs)}")
            for pr in prs[:3]:  # Show first 3 PRs
                context_parts.append(f"  - PR #{pr.get('number', '?')}: {pr.get('title', 'No title')}")
        else:
            context_parts.append("Open PRs: 0")

    return "\n".join(context_parts)


def _format_work_items(work_items: list[Dict[str, Any]]) -> str:
    """Format work items for LLM context."""
    if not work_items:
        return "No work items available."

    items_str = []
    for idx, item in enumerate(work_items):
        items_str.append(f"\n{idx}. Work Item ID: {item.get('id', item.get('task_id', 'unknown'))}")
        items_str.append(f"   Repository: {item.get('repo_name', 'unknown')}")
        items_str.append(f"   Task: {item.get('task_id', 'unknown')}")

        # Add any additional context from the work item
        if "description" in item:
            items_str.append(f"   Description: {item['description']}")
        if "actions" in item:
            items_str.append(f"   Actions: {', '.join(item['actions'])}")

    return "\n".join(items_str)


def _select_work_item_with_llm(
    state: Dict[str, Any],
    llm
) -> Optional[tuple[Dict[str, Any], str, str]]:
    """
    Use LLM to intelligently select the next work item.

    Returns:
        Tuple of (selected_work_item, reasoning, message) or None if no items available
    """
    work_items = state.get("work_items", [])
    if not work_items:
        return None

    repos = state.get("repos", {})
    plan = state.get("plan", {})

    # Build context for the LLM
    repo_context = _format_repo_context(repos)
    work_items_context = _format_work_items(work_items)

    # Create the prompt
    user_message = f"""
Current state of repositories:
{repo_context}

Available work items to choose from:
{work_items_context}

Plan objectives:
{json.dumps(plan.get('objectives', []), indent=2)}

Select the most appropriate work item to execute next. Consider:
- Repository health and activity
- PR status and blockers
- Plan alignment and priorities
- Load balancing across repositories

Respond with a JSON object containing your reasoning and selection.
"""

    messages = [
        SystemMessage(content=_rs),
        HumanMessage(content=user_message)
    ]

    try:
        response = llm.invoke(messages)
        response_text = response.content

        # Parse JSON response
        # Try to extract JSON if it's wrapped in markdown code blocks
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()

        decision = json.loads(response_text)

        # Find the selected work item
        selected_id = decision.get("selected_work_item_id")
        reasoning = decision.get("reasoning", "No reasoning provided")
        message = decision.get("message_to_post", "Sync on current plan and blockers.")

        # Try to find work item by ID or index
        selected_item = None

        # Try as index first
        try:
            idx = int(selected_id)
            if 0 <= idx < len(work_items):
                selected_item = work_items[idx]
        except (ValueError, TypeError):
            pass

        # Try as task_id
        if not selected_item:
            for item in work_items:
                if item.get("id") == selected_id or item.get("task_id") == selected_id:
                    selected_item = item
                    break

        # Fallback to first item
        if not selected_item:
            selected_item = work_items[0]
            reasoning += " (Fallback: using first work item due to ID mismatch)"

        return (selected_item, reasoning, message)

    except Exception as e:
        # Log error and fallback to simple selection
        print(f"Warning: LLM selection failed ({e}), falling back to round-robin")
        idx = state.get("_next_idx", 0) % len(work_items)
        state["_next_idx"] = idx + 1
        return (work_items[idx], f"Fallback selection due to error: {e}", "Sync on current plan and blockers.")


def reason_step(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reasoner node: Use LLM to intelligently select next work item.

    This replaces the naive round-robin with GLM-4.6 powered reasoning
    that considers repo health, PR status, and plan priorities.
    """
    with span("ReasonStep"):
        # Get LLM configuration from state (passed as _settings from main.py)
        settings = state.get("_settings")
        if not settings:
            # Fallback: no settings available
            state["task_envelope"] = None
            return state

        # Create LLM client
        try:
            llm = create_reasoner_llm(settings.llm)
        except Exception as e:
            print(f"Error creating LLM client: {e}")
            state["task_envelope"] = None
            return state

        # Use LLM to select work item
        result = _select_work_item_with_llm(state, llm)

        if not result:
            state["task_envelope"] = None
            return state

        wi, reasoning, message = result

        # Get repo info
        repo = state["repos"].get(wi["repo_name"])
        if not repo:
            state["task_envelope"] = None
            return state

        # Create task envelope with LLM-generated message
        envelope = {
            "type": "desktop_task",
            "intent": "harvest_and_nudge",
            "target_repo_path": repo["path"],
            "payload": {
                "message_to_post": message,
                "copy_scope": {"mode": "last_n", "n": 10}
            },
            "meta": {
                "task_id": wi.get("id", wi.get("task_id")),
                "repo_name": wi["repo_name"],
                "reasoning": reasoning  # Include LLM's reasoning for observability
            }
        }

        state["task_envelope"] = envelope

        # Log reasoning for debugging
        print(f"[Reasoner] Selected: {wi['repo_name']}/{wi.get('task_id')}")
        print(f"[Reasoner] Reasoning: {reasoning}")

        return state
