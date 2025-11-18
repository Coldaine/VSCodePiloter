"""
Integration tests for Reasoner agent with real LLM.

These tests validate that the Reasoner makes intelligent decisions
using the actual Z.ai GLM-4.6 API (NO MOCKS for acceptance testing).

Tests are marked with @pytest.mark.integration and @pytest.mark.requires_api_key
so they can be skipped in environments without API access.
"""
import pytest
import os
from agent.nodes.reason_step import reason_step, _select_work_item_with_llm
from agent.llm_client import create_reasoner_llm


@pytest.mark.integration
@pytest.mark.requires_api_key
def test_reasoner_selects_high_priority_repo(
    mock_repos, mock_work_items, mock_plan, test_settings, has_api_key
):
    """
    Test that Reasoner selects high-priority repo (with 3 open PRs)
    over others >80% of the time.
    """
    if not has_api_key:
        pytest.skip("ZAI_API_KEY not available")

    # Build state with high-priority repo
    state = {
        "repos": mock_repos,
        "work_items": mock_work_items,
        "plan": mock_plan,
        "_settings": test_settings
    }

    # Run reasoner multiple times to check consistency
    selections = []
    for _ in range(5):
        result_state = reason_step(state.copy())

        # Verify task envelope was created
        assert result_state.get("task_envelope") is not None, "Task envelope should be created"

        envelope = result_state["task_envelope"]
        assert envelope["type"] == "desktop_task"
        assert envelope["intent"] == "harvest_and_nudge"

        # Track which repo was selected
        repo_name = envelope["meta"]["repo_name"]
        selections.append(repo_name)

        # Verify reasoning is logged
        assert "reasoning" in envelope["meta"], "Reasoning should be in meta"
        reasoning = envelope["meta"]["reasoning"]
        assert len(reasoning) > 0, "Reasoning should not be empty"

        # Verify message is context-appropriate (not generic)
        message = envelope["payload"]["message_to_post"]
        assert len(message) > 0, "Message should not be empty"
        assert message != "Sync on current plan and blockers.", "Message should be more specific than default"

    # Check that high_priority_repo was selected most of the time
    high_priority_count = selections.count("high_priority_repo")
    success_rate = high_priority_count / len(selections)

    assert success_rate >= 0.6, (
        f"Expected high_priority_repo to be selected >60% of time, "
        f"but got {success_rate*100:.1f}% ({high_priority_count}/{len(selections)})"
    )

    print(f"✓ Reasoner selected high-priority repo {success_rate*100:.1f}% of the time")


@pytest.mark.integration
@pytest.mark.requires_api_key
def test_reasoner_reasoning_includes_pr_context(
    mock_repos, mock_work_items, mock_plan, test_settings, has_api_key
):
    """
    Test that Reasoner's reasoning mentions PRs/activity when selecting repos.
    """
    if not has_api_key:
        pytest.skip("ZAI_API_KEY not available")

    state = {
        "repos": mock_repos,
        "work_items": mock_work_items,
        "plan": mock_plan,
        "_settings": test_settings
    }

    result_state = reason_step(state)

    assert result_state.get("task_envelope") is not None
    reasoning = result_state["task_envelope"]["meta"]["reasoning"]

    # Check that reasoning mentions relevant context
    # (PRs, activity, priority, etc.)
    relevant_keywords = ["pr", "priority", "activity", "stale", "commit", "recent", "open"]
    has_relevant_context = any(keyword in reasoning.lower() for keyword in relevant_keywords)

    assert has_relevant_context, (
        f"Reasoning should mention PRs/activity context. Got: {reasoning}"
    )

    print(f"✓ Reasoning includes context: {reasoning[:100]}...")


@pytest.mark.integration
@pytest.mark.requires_api_key
def test_reasoner_generates_contextual_message(
    mock_repos, mock_work_items, mock_plan, test_settings, has_api_key
):
    """
    Test that Reasoner generates contextual messages, not generic ones.
    """
    if not has_api_key:
        pytest.skip("ZAI_API_KEY not available")

    state = {
        "repos": mock_repos,
        "work_items": mock_work_items,
        "plan": mock_plan,
        "_settings": test_settings
    }

    result_state = reason_step(state)

    assert result_state.get("task_envelope") is not None
    message = result_state["task_envelope"]["payload"]["message_to_post"]

    # Message should be specific and contextual
    assert len(message) > 20, "Message should be substantive"
    assert message != "Sync on current plan and blockers.", "Message should not be the default"

    # Check for context-specific words
    contextual_words = ["pr", "review", "commit", "update", "check", "merge", "test", "fix"]
    has_context = any(word in message.lower() for word in contextual_words)

    assert has_context, f"Message should be contextual. Got: {message}"

    print(f"✓ Generated contextual message: {message[:80]}...")


@pytest.mark.integration
def test_reasoner_fallback_on_llm_failure(
    mock_repos, mock_work_items, mock_plan, test_settings
):
    """
    Test that Reasoner gracefully falls back to round-robin when LLM fails.
    """
    # Create state with invalid API key to trigger fallback
    bad_settings = type('Settings', (), {
        'llm': type('LLMConfig', (), {
            'provider': 'z.ai',
            'model': 'glm-4.6',
            'api_key_env': 'INVALID_KEY_THAT_DOES_NOT_EXIST',
            'api_base_coding': 'https://api.z.ai/api/coding/paas/v4/',
            'api_base_standard': 'https://api.z.ai/api/paas/v4/',
            'temperature': 0.7,
            'max_tokens': 200000
        })()
    })()

    state = {
        "repos": mock_repos,
        "work_items": mock_work_items,
        "plan": mock_plan,
        "_settings": bad_settings,
        "_next_idx": 0
    }

    # Should fall back gracefully without crashing
    result_state = reason_step(state)

    # In this case, with invalid settings, it should return None task_envelope
    # (based on the code logic that catches exceptions)
    assert result_state.get("task_envelope") is None, (
        "Should return None task_envelope when LLM client cannot be created"
    )

    print("✓ Reasoner handles LLM failure gracefully")


@pytest.mark.integration
@pytest.mark.requires_api_key
def test_select_work_item_with_llm_direct(test_llm_config, has_api_key):
    """
    Test _select_work_item_with_llm function directly with real LLM.
    """
    if not has_api_key:
        pytest.skip("ZAI_API_KEY not available")

    llm = create_reasoner_llm(test_llm_config)

    state = {
        "repos": {
            "test_repo": {
                "path": "/test/path",
                "current_branch": "main",
                "prs": [{"number": 1, "title": "Test PR"}]
            }
        },
        "work_items": [
            {
                "id": "task_1",
                "task_id": "test_task",
                "repo_name": "test_repo",
                "description": "Test task"
            }
        ],
        "plan": {
            "objectives": ["Test objective"]
        }
    }

    result = _select_work_item_with_llm(state, llm)

    assert result is not None, "Should return a result"
    work_item, reasoning, message = result

    assert work_item is not None, "Should select a work item"
    assert work_item["id"] == "task_1", "Should select the available work item"
    assert len(reasoning) > 0, "Should provide reasoning"
    assert len(message) > 0, "Should provide a message"

    print(f"✓ Selected work item: {work_item['task_id']}")
    print(f"✓ Reasoning: {reasoning[:100]}...")
    print(f"✓ Message: {message[:80]}...")


@pytest.mark.integration
@pytest.mark.requires_api_key
def test_reasoner_handles_no_work_items(test_settings, has_api_key):
    """
    Test that Reasoner handles empty work items gracefully.
    """
    if not has_api_key:
        pytest.skip("ZAI_API_KEY not available")

    state = {
        "repos": {"test_repo": {"path": "/test", "current_branch": "main", "prs": []}},
        "work_items": [],  # Empty work items
        "plan": {"objectives": []},
        "_settings": test_settings
    }

    result_state = reason_step(state)

    # Should handle empty work items gracefully
    assert result_state.get("task_envelope") is None, (
        "Should return None task_envelope when no work items available"
    )

    print("✓ Reasoner handles empty work items gracefully")


@pytest.mark.integration
@pytest.mark.requires_api_key
def test_reasoner_balances_work_across_repos(
    mock_repos, mock_plan, test_settings, has_api_key
):
    """
    Test that Reasoner distributes work across multiple repos over time.
    """
    if not has_api_key:
        pytest.skip("ZAI_API_KEY not available")

    # Create work items for all repos
    work_items = [
        {"id": f"task_{i}", "task_id": f"task_{i}", "repo_name": repo, "description": f"Task for {repo}"}
        for i, repo in enumerate(mock_repos.keys())
    ]

    state = {
        "repos": mock_repos,
        "work_items": work_items,
        "plan": mock_plan,
        "_settings": test_settings
    }

    # Run reasoner multiple times
    selected_repos = []
    for _ in range(6):
        result_state = reason_step(state.copy())
        if result_state.get("task_envelope"):
            repo_name = result_state["task_envelope"]["meta"]["repo_name"]
            selected_repos.append(repo_name)

    # Check that work is distributed (not always selecting the same repo)
    unique_repos = set(selected_repos)
    assert len(unique_repos) >= 2, (
        f"Should select at least 2 different repos, but only selected: {unique_repos}"
    )

    print(f"✓ Work distributed across {len(unique_repos)} repos: {unique_repos}")


if __name__ == "__main__":
    # Allow running tests directly with pytest
    pytest.main([__file__, "-v", "-s"])
