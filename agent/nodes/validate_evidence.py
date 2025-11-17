
from __future__ import annotations
from typing import Dict, Any
from agent.observability import span, log_event
from agent.llm_client import create_vision_llm, create_vision_message
from agent.config import Settings
import logging

logger = logging.getLogger(__name__)

def _analyze_screenshot_with_vision(
    screenshot_b64: str,
    settings: Settings,
    question: str = "What is visible in this VS Code window? Is GitHub Copilot Chat open and responsive?"
) -> Dict[str, Any]:
    """
    Analyze a screenshot using GLM-4.5V vision model.

    Args:
        screenshot_b64: Base64-encoded screenshot
        settings: Application settings with LLM config
        question: Question to ask the vision model

    Returns:
        Dict with 'success', 'content', and optional 'error'
    """
    try:
        # Create vision LLM client
        vision_llm = create_vision_llm(
            config=settings.llm,
            secret_provider=True  # Use global secret provider
        )

        # Create vision message with screenshot
        msg = create_vision_message(
            text=question,
            image_base64=screenshot_b64,
            detail=settings.llm.vision.detail
        )

        # Invoke vision model
        response = vision_llm.invoke([msg])
        content = response.content if hasattr(response, 'content') else str(response)

        return {
            "success": True,
            "content": content,
            "model": settings.llm.vision_model
        }

    except Exception as e:
        logger.error(f"Vision analysis failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "model": settings.llm.vision_model
        }

def validate_evidence(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate ActStep evidence with both structural checks and vision analysis.

    Checks:
    1. Structural: Screenshots exist in artifacts
    2. Vision: Analyze post-action screenshot with GLM-4.5V (if enabled)
    3. Content: Verify Copilot Chat state from vision analysis
    """
    settings: Settings = state.get("_settings")
    vision_enabled = settings and settings.llm.vision.enabled

    with span("ValidateEvidence", {"vision_enabled": vision_enabled}):
        rpt = state.get("action_report") or {}

        # Step 1: Structural validation (screenshots exist)
        artifacts = rpt.get("artifacts", {})
        has_screenshots = "pre" in artifacts and "post" in artifacts

        if not has_screenshots:
            log_event("validation.failed", {"reason": "missing_screenshots"})
            state["validated"] = False
            state["validation_detail"] = {"structural": False, "reason": "missing_screenshots"}
            return state

        # Step 2: Vision analysis (if enabled)
        vision_result = None
        if vision_enabled and settings:
            post_screenshot_b64 = artifacts.get("post")
            if post_screenshot_b64:
                vision_result = _analyze_screenshot_with_vision(
                    screenshot_b64=post_screenshot_b64,
                    settings=settings,
                    question=(
                        "Analyze this VS Code window screenshot. "
                        "Is GitHub Copilot Chat visible and open? "
                        "Is there any error message or busy indicator? "
                        "Describe what you see in 2-3 sentences."
                    )
                )

                # Log vision analysis
                log_event("vision.analysis", {
                    "success": vision_result.get("success"),
                    "model": vision_result.get("model"),
                    "content_preview": (vision_result.get("content", "")[:200] if vision_result.get("success") else None),
                    "error": vision_result.get("error")
                })

        # Step 3: Determine overall validation status
        structural_ok = has_screenshots
        vision_ok = True
        vision_issues = []

        # Parse vision analysis for specific issues
        if vision_result and vision_result.get("success"):
            content = (vision_result.get("content") or "").lower()
            
            # Check for failure indicators
            failure_keywords = [
                "error", "failed", "not open", "not visible", 
                "closed", "cannot see", "busy", "loading",
                "blocked", "unresponsive"
            ]
            
            success_keywords = [
                "copilot chat is open", "chat is visible",
                "chat view is open", "ready", "available"
            ]
            
            has_failure = any(kw in content for kw in failure_keywords)
            has_success = any(kw in content for kw in success_keywords)
            
            if has_failure and not has_success:
                vision_ok = False
                vision_issues.append(f"Vision detected issues: {content[:200]}")
                logger.warning(f"Vision validation failed: {content[:200]}")
            
        elif vision_result and not vision_result.get("success"):
            # Vision call failed entirely
            vision_ok = False
            vision_issues.append(f"Vision API error: {vision_result.get('error')}")
            logger.error(f"Vision API failed: {vision_result.get('error')}")

        overall_validated = structural_ok and vision_ok

        state["validated"] = overall_validated
        state["validation_detail"] = {
            "structural": structural_ok,
            "vision": vision_result,
            "vision_ok": vision_ok,
            "vision_issues": vision_issues,
            "overall": overall_validated
        }

        if overall_validated:
            log_event("validation.passed", {
                "has_vision": vision_result is not None,
                "vision_used": vision_enabled
            })
        else:
            log_event("validation.failed", {
                "structural": structural_ok,
                "vision_success": vision_ok
            })

        return state
