
from __future__ import annotations
import os, re, base64, time, logging, asyncio
from typing import Dict, Any, Optional, List
from agent.observability import span, log_event
from agent.adapters.base import DesktopAdapter
from agent.llm_client import create_vision_llm, create_vision_message
from agent.tools.vscode_copilot_monitor import VSCodeCopilotMonitor

logger = logging.getLogger(__name__)

def _verify_with_vision(screenshot_b64: str, state: Dict[str, Any], question: str) -> Dict[str, str]:
    """Use GLM-4.5V to analyze screenshot and return vision insights."""
    settings = state.get("_settings")
    if not settings or not settings.llm.vision.enabled:
        return {"enabled": False}
    
    try:
        vision_llm = create_vision_llm(
            config=settings.llm,
            secret_provider=True
        )
        msg = create_vision_message(
            text=question,
            image_base64=screenshot_b64,
            detail=settings.llm.vision.detail
        )
        response = vision_llm.invoke([msg])
        content = response.content if hasattr(response, 'content') else str(response)
        
        return {
            "enabled": True,
            "success": True,
            "content": content,
            "model": settings.llm.vision_model
        }
    except Exception as e:
        logger.error(f"Vision verification failed: {e}", exc_info=True)
        return {
            "enabled": True,
            "success": False,
            "error": str(e)
        }

def _find_vscode_window(adapter: DesktopAdapter, title_regex: str) -> Optional[Dict[str, Any]]:
    windows = adapter.list_windows(app="Code.exe")
    for w in windows:
        title = w.get("title") or ""
        if re.match(title_regex, title):
            return w
    # fallback: return first Code.exe window if regex too strict
    for w in windows:
        if "Visual Studio Code" in (w.get("title") or ""):
            return w
    return None

def _focus_and_open_chat(adapter: DesktopAdapter, hwnd: Optional[int], palette_action: str, write_mode: bool) -> None:
    adapter.focus_window(hwnd=hwnd)
    time.sleep(0.3)
    if not write_mode:
        return
    # Open command palette and invoke Copilot Chat focus command
    adapter.keypress("Ctrl+Shift+P")
    time.sleep(0.1)
    adapter.text_input(palette_action)
    time.sleep(0.1)
    adapter.keypress("Enter")
    time.sleep(0.5)

def _copy_chat_context(adapter: DesktopAdapter) -> str:
    # Attempt select-all + copy; assumes focus in chat view
    adapter.keypress("Ctrl+A")
    time.sleep(0.1)
    adapter.keypress("Ctrl+C")
    time.sleep(0.1)
    text = adapter.clipboard_get()
    return text or ""

def _post_to_chat(adapter: DesktopAdapter, text: str) -> None:
    # Paste and send
    adapter.clipboard_set(text)
    time.sleep(0.1)
    adapter.keypress("Ctrl+V")
    time.sleep(0.1)
    adapter.keypress("Enter")

def act_step(state: Dict[str, Any]) -> Dict[str, Any]:
    settings = state.get("_settings")
    adapter: DesktopAdapter = state.get("_adapter")
    envelope = state.get("task_envelope")
    if not envelope:
        return state

    write_mode = settings.write_mode if settings else False
    regex = settings.window_title_regex if settings else ".*Visual Studio Code.*"
    palette_action = settings.copilot.command_palette_action if settings else "GitHub Copilot Chat: Focus on Chat View"

    with span("ActStep", {"repo": envelope.get("target_repo_path")}):
        # Focus the correct VS Code window
        win = _find_vscode_window(adapter, regex)
        if not win:
            log_event("warn.no_vscode_window", {"regex": regex})
            state["action_report"] = {"status": "failed", "reason": "no vscode window"}
            return state

        hwnd = win.get("hwnd")
        _focus_and_open_chat(adapter, hwnd, palette_action, write_mode)

        # Screenshot before
        pre_img = adapter.screenshot(hwnd=hwnd)
        pre_b64 = base64.b64encode(pre_img).decode("ascii")
        
        # Vision check: Is Copilot Chat open?
        pre_vision = _verify_with_vision(
            pre_b64, state,
            "Look at this VS Code window. Is GitHub Copilot Chat panel visible and open on the right side? Answer YES or NO and explain briefly."
        )
        
        chat_already_open = False
        if pre_vision.get("success"):
            content = (pre_vision.get("content") or "").lower()
            chat_already_open = "yes" in content[:50] or "copilot chat" in content and "open" in content
            log_event("vision.pre_check", {
                "chat_open": chat_already_open,
                "vision_says": content[:200]
            })
        
        # If chat not open and we're in write mode, the open action should have worked
        # But we can't verify until post-screenshot

        # Copy chat context via monitor (canonical). Fallback to Ctrl+C if monitor fails.
        copied = ""
        monitor_error = None
        try:
            monitor = VSCodeCopilotMonitor()
            # Run the async monitor in a short-lived loop (ActStep remains sync)
            results: List[Dict[str, Any]] = asyncio.run(monitor.connect())

            # Pick the result matching our focused window title or containing repo path
            target_title = (win.get("title") or "").lower()
            target_repo = (envelope.get("target_repo_path") or "").lower()
            target: Optional[Dict[str, Any]] = None
            for r in results or []:
                title = (r.get("title") or "").lower()
                if title == target_title or (target_repo and target_repo in title):
                    target = r
                    break
            if not target and results:
                # fallback: first VS Code window result
                target = results[0]

            if target:
                # Prefer transcript_diff if available; else transcript_length doesn't expose content, so rely on monitor history
                # The debug monitor stores latest transcript in monitor.history[title]['transcript']
                title_key = target.get("title") or target_title
                transcript_text = ""
                try:
                    transcript_text = monitor.history.get(title_key, {}).get("transcript", "")
                except Exception:
                    transcript_text = ""
                copied = transcript_text or copied
        
        except Exception as e:
            monitor_error = str(e)
            logger.warning(f"Monitor-based transcript capture failed; falling back. Error: {monitor_error}")
            # Fallback: naive select-all + copy
            try:
                copied = _copy_chat_context(adapter)
            except Exception:
                copied = ""

        # Optionally nudge Copilot
        message = (envelope.get("payload") or {}).get("message_to_post")
        if message and write_mode:
            _post_to_chat(adapter, message)
            time.sleep(0.5)

        # Screenshot after
        post_img = adapter.screenshot(hwnd=hwnd)
        post_b64 = base64.b64encode(post_img).decode("ascii")

        report = {
            "status": "ok",
            "window": {"hwnd": hwnd, "title": win.get("title")},
            "copied_chat_chars": len(copied),
            "artifacts": {"pre": pre_b64, "post": post_b64},
            "next": "await_response" if message else "idle"
        }
        if monitor_error:
            report["notes"] = {"monitor_error": monitor_error}
        state["action_report"] = report
        return state
