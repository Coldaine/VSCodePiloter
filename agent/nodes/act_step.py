
from __future__ import annotations
import os, re, base64, time
from typing import Dict, Any, Optional, List
from agent.observability import span, log_event
from agent.adapters.base import DesktopAdapter

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

        # Copy chat context
        copied = _copy_chat_context(adapter)

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
        state["action_report"] = report
        return state
