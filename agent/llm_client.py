"""
LLM client initialization for Z.ai GLM-4.6 and other providers.
"""
from __future__ import annotations
import os
from typing import Optional
from langchain_openai import ChatOpenAI
from agent.config import LLMConfig


def create_llm_client(config: LLMConfig, api_key: Optional[str] = None) -> ChatOpenAI:
    """
    Create a ChatOpenAI client configured for the specified provider.

    Args:
        config: LLM configuration from Settings
        api_key: Optional API key override. If not provided, reads from environment
                variable specified in config.api_key_env

    Returns:
        Configured ChatOpenAI instance

    Raises:
        ValueError: If API key is not found in environment or provided
    """
    # Get API key from environment or parameter
    if api_key is None:
        api_key = os.getenv(config.api_key_env)

    if not api_key:
        raise ValueError(
            f"API key not found. Set the {config.api_key_env} environment variable "
            f"or provide api_key parameter."
        )

    # Create ChatOpenAI with Z.ai coding endpoint configuration
    # Z.ai is OpenAI-compatible, so we use ChatOpenAI with custom base URL
    llm = ChatOpenAI(
        model=config.model,
        openai_api_key=api_key,
        openai_api_base=config.api_base,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        # Z.ai GLM-4.6 supports streaming
        streaming=True,
    )

    return llm


def create_reasoner_llm(config: LLMConfig, api_key: Optional[str] = None) -> ChatOpenAI:
    """
    Create an LLM specifically configured for the Reasoner agent.
    Uses slightly lower temperature for more consistent task selection.

    Args:
        config: LLM configuration from Settings
        api_key: Optional API key override

    Returns:
        Configured ChatOpenAI instance for Reasoner
    """
    llm = create_llm_client(config, api_key)
    # Override temperature for more deterministic reasoning
    llm.temperature = 0.7
    return llm


def create_actor_llm(config: LLMConfig, api_key: Optional[str] = None) -> ChatOpenAI:
    """
    Create an LLM specifically configured for the Vision Actor agent.
    Uses default temperature for balanced responses.

    Note: GLM-4.6 does not have native vision capabilities. For vision analysis,
    screenshots should be converted to text descriptions or OCR before sending.

    Args:
        config: LLM configuration from Settings
        api_key: Optional API key override

    Returns:
        Configured ChatOpenAI instance for Actor
    """
    return create_llm_client(config, api_key)
