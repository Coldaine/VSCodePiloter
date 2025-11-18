"""
Pytest fixtures for integration tests.

These fixtures provide common setup for integration tests including:
- Mock repositories
- Test configuration
- API key management
"""
import pytest
import json
import os
from pathlib import Path
from agent.config import Settings, LLMConfig


@pytest.fixture
def mock_repos():
    """Load mock repository data from fixtures."""
    fixtures_path = Path(__file__).parent.parent / "fixtures" / "mock_repos.json"
    with open(fixtures_path) as f:
        return json.load(f)


@pytest.fixture
def mock_work_items():
    """Create mock work items for testing."""
    return [
        {
            "id": "task_1",
            "task_id": "pr_review",
            "repo_name": "high_priority_repo",
            "description": "Review critical PR",
            "actions": ["review_pr", "post_comment"]
        },
        {
            "id": "task_2",
            "task_id": "update_docs",
            "repo_name": "stale_repo",
            "description": "Update stale documentation",
            "actions": ["edit_file", "commit"]
        },
        {
            "id": "task_3",
            "task_id": "check_ci",
            "repo_name": "normal_repo",
            "description": "Check CI status",
            "actions": ["view_pr"]
        }
    ]


@pytest.fixture
def mock_plan():
    """Create mock plan objectives."""
    return {
        "objectives": [
            "Maintain high code quality",
            "Keep PRs moving",
            "Update stale repositories"
        ]
    }


@pytest.fixture
def test_llm_config():
    """Create test LLM configuration."""
    # Check if we have a real API key for integration tests
    api_key = os.getenv("ZAI_API_KEY")

    return LLMConfig(
        provider="z.ai",
        model="glm-4.6",
        vision_model="glm-4.5v",
        api_key_env="ZAI_API_KEY",
        api_base_coding="https://api.z.ai/api/coding/paas/v4/",
        api_base_standard="https://api.z.ai/api/paas/v4/",
        temperature=0.7,
        max_tokens=200000
    )


@pytest.fixture
def test_settings(test_llm_config):
    """Create test settings with LLM configuration."""
    return type('Settings', (), {'llm': test_llm_config})()


@pytest.fixture
def has_api_key():
    """Check if Z.ai API key is available for integration tests."""
    return bool(os.getenv("ZAI_API_KEY"))


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires real dependencies)"
    )
    config.addinivalue_line(
        "markers", "requires_api_key: mark test as requiring Z.ai API key"
    )
    config.addinivalue_line(
        "markers", "requires_vscode: mark test as requiring VS Code"
    )
