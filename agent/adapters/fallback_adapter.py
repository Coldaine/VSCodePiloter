
from __future__ import annotations
from typing import Any, Dict, List, Optional
import io, time
from PIL import ImageGrab
import pyperclip

try:
    import pyautogui
except Exception as e:
    pyautogui = None

from .base import DesktopAdapter

class FallbackAdapter(DesktopAdapter):
    """Local automation fallback using pyautogui + ImageGrab.
    This is provided for completeness and testing; prefer MCPAdapter in production.
    """
    def list_windows(self, app: Optional[str] = None) -> List[Dict[str, Any]]:
        # Minimal placeholder: we can't enumerate windows reliably without OS APIs here.
        # Return single pseudo-window representing the current foreground.
        return [{"hwnd": None, "title": "UNKNOWN", "z": 0}]

    def focus_window(self, hwnd: Optional[int] = None, title_regex: Optional[str] = None) -> Dict[str, Any]:
        # No-op in fallback (user must ensure correct window is focused)
        return {"ok": True}

    def screenshot(self, hwnd: Optional[int] = None) -> bytes:
        img = ImageGrab.grab()
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def keypress(self, keys: str) -> Dict[str, Any]:
        if not pyautogui:
            raise RuntimeError("pyautogui not installed; install extra 'fallback'")
        pyautogui.hotkey(*[k.strip() for k in keys.split("+")])
        time.sleep(0.2)
        return {"ok": True}

    def text_input(self, text: str) -> Dict[str, Any]:
        if not pyautogui:
            raise RuntimeError("pyautogui not installed; install extra 'fallback'")
        pyautogui.typewrite(text, interval=0.02)
        return {"ok": True}

    def clipboard_get(self) -> str:
        return pyperclip.paste()

    def clipboard_set(self, text: str) -> Dict[str, Any]:
        pyperclip.copy(text)
        return {"ok": True}
