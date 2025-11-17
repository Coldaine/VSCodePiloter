"""
LLM client initialization for Z.ai GLM-4.6 (text) and GLM-4.5V (vision) models.

Supports multiple secret backends:
- Bitwarden Secrets Manager (for local development)
- Environment variables (for CI/CD)
- Auto-detection based on environment

Vision Support:
- GLM-4.5V for screenshot analysis and visual understanding
- Automatic image encoding and message formatting
- Compatible with OpenAI vision API format
"""
from __future__ import annotations
import os
import base64
from typing import Optional, Union, List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from agent.config import LLMConfig
from agent.secrets import get_secret_provider, SecretProvider, SecretNotFoundError
import logging

logger = logging.getLogger(__name__)

# Global secret provider instance (lazy-initialized)
_secret_provider: Optional[SecretProvider] = None


def get_global_secret_provider() -> SecretProvider:
    """
    Get or create the global secret provider.

    Returns:
        The global secret provider instance
    """
    global _secret_provider
    if _secret_provider is None:
        # Auto-detect the best provider for the environment
        _secret_provider = get_secret_provider()
        logger.info(f"Initialized secret provider: {_secret_provider}")
    return _secret_provider


def set_global_secret_provider(provider: SecretProvider) -> None:
    """
    Set a custom global secret provider.

    Args:
        provider: The secret provider to use globally
    """
    global _secret_provider
    _secret_provider = provider
    logger.info(f"Set global secret provider to: {provider}")


def create_llm_client(
    config: LLMConfig,
    api_key: Optional[str] = None,
    secret_provider: Optional[Union[SecretProvider, bool]] = None
) -> ChatOpenAI:
    """
    Create a ChatOpenAI client configured for the specified provider.

    Args:
        config: LLM configuration from Settings
        api_key: Optional API key override. If not provided, retrieves from secret provider
                or environment variable specified in config.api_key_env
        secret_provider: Optional secret provider to use. If True, uses global provider.
                        If False or None, uses legacy environment variable method.

    Returns:
        Configured ChatOpenAI instance

    Raises:
        ValueError: If API key is not found in any configured source
    """
    # Determine which secret retrieval method to use
    if api_key is None:
        if secret_provider is True:
            # Use global secret provider
            provider = get_global_secret_provider()
        elif isinstance(secret_provider, SecretProvider):
            # Use provided secret provider
            provider = secret_provider
        elif secret_provider is False or secret_provider is None:
            # Legacy: Use environment variable directly
            provider = None
        else:
            provider = None

        # Try to get API key from provider or environment
        if provider:
            try:
                # Try the exact key name first
                api_key = provider.get_secret(config.api_key_env)
                logger.debug(f"Retrieved API key from provider using key: {config.api_key_env}")
            except SecretNotFoundError:
                # Try alternative key names
                alt_keys = [
                    "Z_AI_API_KEY",  # Bitwarden format
                    "ZAI_API_KEY",   # Environment format
                    "OPENAI_API_KEY",  # Generic OpenAI format
                ]
                for alt_key in alt_keys:
                    try:
                        api_key = provider.get_secret(alt_key)
                        logger.debug(f"Retrieved API key from provider using alternative key: {alt_key}")
                        break
                    except SecretNotFoundError:
                        continue

                if not api_key:
                    # Fall back to environment variable
                    api_key = os.getenv(config.api_key_env)
                    if api_key:
                        logger.debug(f"Fell back to environment variable: {config.api_key_env}")
        else:
            # Legacy method: direct environment variable
            api_key = os.getenv(config.api_key_env)

    if not api_key:
        raise ValueError(
            f"API key not found. Checked: "
            f"1) Direct parameter, "
            f"2) Secret provider (if configured), "
            f"3) Environment variable {config.api_key_env}. "
            f"Set the environment variable or configure a secret provider."
        )

    # Create ChatOpenAI with Z.ai coding endpoint configuration
    # GLM-4.6 uses the coding endpoint (subscription-based)
    # Z.ai is OpenAI-compatible, so we use ChatOpenAI with custom base URL
    llm = ChatOpenAI(
        model=config.model,
        openai_api_key=api_key,
        openai_api_base=config.api_base_coding,  # Use coding endpoint for text models
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        # Z.ai GLM-4.6 supports streaming
        streaming=True,
    )

    return llm


def create_reasoner_llm(
    config: LLMConfig,
    api_key: Optional[str] = None,
    secret_provider: Optional[Union[SecretProvider, bool]] = None
) -> ChatOpenAI:
    """
    Create an LLM specifically configured for the Reasoner agent.
    Uses slightly lower temperature for more consistent task selection.

    Args:
        config: LLM configuration from Settings
        api_key: Optional API key override
        secret_provider: Optional secret provider to use

    Returns:
        Configured ChatOpenAI instance for Reasoner
    """
    llm = create_llm_client(config, api_key, secret_provider)
    # Override temperature for more deterministic reasoning
    llm.temperature = 0.7
    return llm


def create_actor_llm(
    config: LLMConfig,
    api_key: Optional[str] = None,
    secret_provider: Optional[Union[SecretProvider, bool]] = None
) -> ChatOpenAI:
    """
    Create an LLM specifically configured for the Vision Actor agent.
    Uses default temperature for balanced responses.

    Note: This creates a text-only LLM. For vision analysis,
    use create_vision_llm() instead.

    Args:
        config: LLM configuration from Settings
        api_key: Optional API key override
        secret_provider: Optional secret provider to use

    Returns:
        Configured ChatOpenAI instance for Actor
    """
    return create_llm_client(config, api_key, secret_provider)


def create_vision_llm(
    config: LLMConfig,
    api_key: Optional[str] = None,
    secret_provider: Optional[Union[SecretProvider, bool]] = None
) -> ChatOpenAI:
    """
    Create an LLM specifically configured for vision analysis.
    Uses GLM-4.5V for screenshot analysis and visual understanding.

    Args:
        config: LLM configuration from Settings
        api_key: Optional API key override
        secret_provider: Optional secret provider to use

    Returns:
        Configured ChatOpenAI instance for vision tasks

    Example:
        vision_llm = create_vision_llm(config)
        response = vision_llm.invoke([
            HumanMessage(content=[
                {"type": "text", "text": "What do you see in this screenshot?"},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
            ])
        ])
    """
    # Get API key using same logic as text model
    if api_key is None:
        if secret_provider is True:
            provider = get_global_secret_provider()
        elif isinstance(secret_provider, SecretProvider):
            provider = secret_provider
        else:
            provider = None

        if provider:
            try:
                api_key = provider.get_secret(config.api_key_env)
            except SecretNotFoundError:
                for alt_key in ["Z_AI_API_KEY", "ZAI_API_KEY", "OPENAI_API_KEY"]:
                    try:
                        api_key = provider.get_secret(alt_key)
                        break
                    except SecretNotFoundError:
                        continue
                if not api_key:
                    api_key = os.getenv(config.api_key_env)
        else:
            api_key = os.getenv(config.api_key_env)

    if not api_key:
        raise ValueError(
            f"API key not found for vision model. "
            f"Set {config.api_key_env} environment variable or configure secret provider."
        )

    # Create vision-capable LLM with GLM-4.5V
    # CRITICAL: Vision models MUST use standard endpoint, NOT coding endpoint
    # The coding endpoint (/api/coding/paas/v4/) does NOT support vision models
    llm = ChatOpenAI(
        model=config.vision_model,  # Use vision_model instead of model
        openai_api_key=api_key,
        openai_api_base=config.api_base_standard,  # Use standard endpoint for vision
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        streaming=False,  # Vision typically doesn't stream
    )

    return llm


def encode_image_to_base64(image_path: str) -> str:
    """
    Encode an image file to base64 string.

    Args:
        image_path: Path to image file

    Returns:
        Base64-encoded image string

    Raises:
        FileNotFoundError: If image doesn't exist
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def create_vision_message(
    text: str,
    image_base64: Optional[str] = None,
    image_path: Optional[str] = None,
    detail: str = "high"
) -> HumanMessage:
    """
    Create a vision-compatible message for the LLM.

    Args:
        text: Text prompt/question about the image
        image_base64: Base64-encoded image (provide this OR image_path)
        image_path: Path to image file (provide this OR image_base64)
        detail: Detail level for vision analysis ("low", "high", "auto")

    Returns:
        HumanMessage with vision content

    Raises:
        ValueError: If neither image_base64 nor image_path is provided

    Example:
        msg = create_vision_message(
            "What's visible in this VS Code window?",
            image_path="screenshot.png"
        )
        response = vision_llm.invoke([msg])
    """
    if image_base64 is None and image_path is None:
        raise ValueError("Must provide either image_base64 or image_path")

    if image_base64 is None:
        image_base64 = encode_image_to_base64(image_path)

    content: List[Dict[str, Any]] = [
        {"type": "text", "text": text},
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{image_base64}",
                "detail": detail
            }
        }
    ]

    return HumanMessage(content=content)
