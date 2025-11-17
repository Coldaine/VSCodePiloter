
from __future__ import annotations
from typing import Any, Dict, List, Optional

class DesktopAdapter:
    """Abstract adapter for desktop automation operations."""
    def list_windows(self, app: Optional[str] = None) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def focus_window(self, hwnd: Optional[int] = None, title_regex: Optional[str] = None) -> Dict[str, Any]:
        raise NotImplementedError

    def screenshot(self, hwnd: Optional[int] = None) -> bytes:
        raise NotImplementedError

    def keypress(self, keys: str) -> Dict[str, Any]:
        raise NotImplementedError

    def text_input(self, text: str) -> Dict[str, Any]:
        raise NotImplementedError

    def clipboard_get(self) -> str:
        raise NotImplementedError

    def clipboard_set(self, text: str) -> Dict[str, Any]:
        raise NotImplementedError
