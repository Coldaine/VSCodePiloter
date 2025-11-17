
from __future__ import annotations
from typing import Any, Dict, List, Optional
import base64
from .base import DesktopAdapter
from agent.mcp.client import MCPHTTPClient

class MCPAdapter(DesktopAdapter):
    def __init__(self, base_url: str, endpoints: Dict[str, str], jsonrpc: bool = False):
        self.client = MCPHTTPClient(base_url, jsonrpc=jsonrpc)
        self.endpoints = endpoints
        self.jsonrpc = jsonrpc

    def _call(self, name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if self.jsonrpc:
            # JSON-RPC: method name is the endpoint key (e.g., "windows.list")
            return self.client._rpc(name, payload)
        else:
            path = self.endpoints.get(name)
            if not path:
                raise KeyError(f"No endpoint configured for {name}")
            return self.client.post(path, payload)

    def list_windows(self, app: Optional[str] = None) -> List[Dict[str, Any]]:
        data = self._call("list_windows", {"app": app})
        return data.get("windows", data)

    def focus_window(self, hwnd: Optional[int] = None, title_regex: Optional[str] = None) -> Dict[str, Any]:
        return self._call("focus_window", {"hwnd": hwnd, "title_regex": title_regex})

    def screenshot(self, hwnd: Optional[int] = None) -> bytes:
        data = self._call("screenshot", {"hwnd": hwnd})
        # Expect base64-encoded PNG in 'image'
        b64 = data.get("image")
        if not b64:
            raise RuntimeError("MCP server returned no 'image' field")
        return base64.b64decode(b64)

    def keypress(self, keys: str) -> Dict[str, Any]:
        return self._call("keypress", {"keys": keys})

    def text_input(self, text: str) -> Dict[str, Any]:
        return self._call("text_input", {"text": text})

    def clipboard_get(self) -> str:
        data = self._call("clipboard_get", {})
        return data.get("text", "")

    def clipboard_set(self, text: str) -> Dict[str, Any]:
        return self._call("clipboard_set", {"text": text})
