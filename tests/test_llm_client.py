"""
Unit tests for the LLM client module.

Tests cover:
- LLM client creation with valid configuration
- Error handling when API key is missing
- Temperature overrides for different agent types
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from agent.llm_client import create_llm_client, create_reasoner_llm, create_actor_llm
from agent.config import LLMConfig


@pytest.fixture
def mock_llm_config():
    """Fixture providing a standard LLM configuration for testing."""
    return LLMConfig(
        provider="z.ai",
        model="glm-4.6",
        api_key_env="ZAI_API_KEY",
        api_base="https://api.z.ai/api/coding/paas/v4/",
        temperature=0.95,
        max_tokens=131072
    )


@pytest.fixture
def mock_api_key():
    """Fixture providing a mock API key."""
    return "test-api-key-12345"


class TestCreateLLMClient:
    """Tests for the create_llm_client function."""

    @patch('agent.llm_client.ChatOpenAI')
    def test_create_llm_client_success(self, mock_chat_openai, mock_llm_config, mock_api_key):
        """
        Test successful LLM client creation with valid configuration.

        Verifies that ChatOpenAI is initialized with correct parameters.
        """
        # Arrange
        mock_instance = MagicMock()
        mock_chat_openai.return_value = mock_instance

        # Act
        result = create_llm_client(mock_llm_config, api_key=mock_api_key)

        # Assert
        mock_chat_openai.assert_called_once_with(
            model="glm-4.6",
            openai_api_key=mock_api_key,
            openai_api_base="https://api.z.ai/api/coding/paas/v4/",
            temperature=0.95,
            max_tokens=131072,
            streaming=True
        )
        assert result == mock_instance

    @patch.dict(os.environ, {"ZAI_API_KEY": "env-api-key-67890"})
    @patch('agent.llm_client.ChatOpenAI')
    def test_create_llm_client_from_env(self, mock_chat_openai, mock_llm_config):
        """
        Test LLM client creation using API key from environment variable.

        Verifies that the client correctly reads the API key from the
        environment when not provided explicitly.
        """
        # Arrange
        mock_instance = MagicMock()
        mock_chat_openai.return_value = mock_instance

        # Act
        result = create_llm_client(mock_llm_config)

        # Assert
        mock_chat_openai.assert_called_once()
        call_kwargs = mock_chat_openai.call_args.kwargs
        assert call_kwargs['openai_api_key'] == "env-api-key-67890"
        assert result == mock_instance

    @patch.dict(os.environ, {}, clear=True)
    def test_create_llm_client_no_api_key(self, mock_llm_config):
        """
        Test error handling when API key is not provided and not in environment.

        Verifies that a ValueError is raised with an appropriate message.
        """
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            create_llm_client(mock_llm_config)

        assert "API key not found" in str(exc_info.value)
        assert "ZAI_API_KEY" in str(exc_info.value)

    @patch('agent.llm_client.ChatOpenAI')
    def test_create_llm_client_custom_parameters(self, mock_chat_openai):
        """
        Test LLM client creation with custom configuration parameters.

        Verifies that custom provider, model, and endpoint configurations
        are correctly passed to ChatOpenAI.
        """
        # Arrange
        custom_config = LLMConfig(
            provider="openai",
            model="gpt-4",
            api_key_env="OPENAI_API_KEY",
            api_base="https://api.openai.com/v1/",
            temperature=0.3,
            max_tokens=4096
        )
        mock_instance = MagicMock()
        mock_chat_openai.return_value = mock_instance

        # Act
        result = create_llm_client(custom_config, api_key="custom-key")

        # Assert
        mock_chat_openai.assert_called_once_with(
            model="gpt-4",
            openai_api_key="custom-key",
            openai_api_base="https://api.openai.com/v1/",
            temperature=0.3,
            max_tokens=4096,
            streaming=True
        )
        assert result == mock_instance


class TestCreateReasonerLLM:
    """Tests for the create_reasoner_llm function."""

    @patch('agent.llm_client.ChatOpenAI')
    def test_create_reasoner_llm_temperature(self, mock_chat_openai, mock_llm_config, mock_api_key):
        """
        Test Reasoner LLM has temperature override to 0.7.

        Verifies that the Reasoner agent uses a lower temperature (0.7)
        for more consistent and deterministic task selection.
        """
        # Arrange
        mock_instance = MagicMock()
        mock_instance.temperature = 0.95  # Initial value from config
        mock_chat_openai.return_value = mock_instance

        # Act
        result = create_reasoner_llm(mock_llm_config, api_key=mock_api_key)

        # Assert
        # Verify ChatOpenAI was created with default config temperature
        mock_chat_openai.assert_called_once_with(
            model="glm-4.6",
            openai_api_key=mock_api_key,
            openai_api_base="https://api.z.ai/api/coding/paas/v4/",
            temperature=0.95,
            max_tokens=131072,
            streaming=True
        )

        # Verify temperature was overridden to 0.7 after creation
        assert result.temperature == 0.7

    @patch.dict(os.environ, {}, clear=True)
    def test_create_reasoner_llm_no_api_key(self, mock_llm_config):
        """
        Test Reasoner LLM creation fails when API key is missing.

        Verifies that create_reasoner_llm propagates the ValueError
        from create_llm_client when no API key is available.
        """
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            create_reasoner_llm(mock_llm_config)

        assert "API key not found" in str(exc_info.value)


class TestCreateActorLLM:
    """Tests for the create_actor_llm function."""

    @patch('agent.llm_client.ChatOpenAI')
    def test_create_actor_llm_temperature(self, mock_chat_openai, mock_llm_config, mock_api_key):
        """
        Test Actor LLM uses default temperature (0.95).

        Verifies that the Actor agent uses the default configuration
        temperature without any overrides.
        """
        # Arrange
        mock_instance = MagicMock()
        mock_instance.temperature = 0.95
        mock_chat_openai.return_value = mock_instance

        # Act
        result = create_actor_llm(mock_llm_config, api_key=mock_api_key)

        # Assert
        mock_chat_openai.assert_called_once_with(
            model="glm-4.6",
            openai_api_key=mock_api_key,
            openai_api_base="https://api.z.ai/api/coding/paas/v4/",
            temperature=0.95,
            max_tokens=131072,
            streaming=True
        )

        # Verify temperature remains at default 0.95
        assert result.temperature == 0.95

    @patch('agent.llm_client.ChatOpenAI')
    def test_create_actor_llm_returns_base_client(self, mock_chat_openai, mock_llm_config, mock_api_key):
        """
        Test Actor LLM is created using base create_llm_client function.

        Verifies that create_actor_llm is a thin wrapper around
        create_llm_client with no temperature modification.
        """
        # Arrange
        mock_instance = MagicMock()
        mock_instance.temperature = 0.95  # Set initial temperature
        mock_chat_openai.return_value = mock_instance

        # Act
        result = create_actor_llm(mock_llm_config, api_key=mock_api_key)

        # Assert
        assert result == mock_instance
        # Temperature should not be modified (stays at config default)
        assert result.temperature == 0.95


class TestTemperatureComparison:
    """Integration tests comparing temperature settings across agent types."""

    @patch('agent.llm_client.ChatOpenAI')
    def test_reasoner_vs_actor_temperature(self, mock_chat_openai, mock_llm_config, mock_api_key):
        """
        Test that Reasoner and Actor use different temperatures.

        Verifies the architectural decision:
        - Reasoner: temp=0.7 for consistent task selection
        - Actor: temp=0.95 for more creative responses
        """
        # Arrange
        def create_mock_with_temp(temp):
            mock = MagicMock()
            mock.temperature = temp
            return mock

        # Create two separate mock instances
        reasoner_mock = create_mock_with_temp(0.95)  # Will be overridden to 0.7
        actor_mock = create_mock_with_temp(0.95)     # Will stay at 0.95

        mock_chat_openai.side_effect = [reasoner_mock, actor_mock]

        # Act
        reasoner = create_reasoner_llm(mock_llm_config, api_key=mock_api_key)
        actor = create_actor_llm(mock_llm_config, api_key=mock_api_key)

        # Assert
        assert reasoner.temperature == 0.7, "Reasoner should use temp=0.7 for consistency"
        assert actor.temperature == 0.95, "Actor should use temp=0.95 for creativity"
        assert reasoner.temperature != actor.temperature, "Different agents should use different temperatures"


# Run tests with coverage
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=agent.llm_client", "--cov-report=term-missing"])
