
from __future__ import annotations
import requests
from typing import Any, Dict

class MCPHTTPClient:
    """Ultra-thin HTTP client for MCP-like servers that expose REST or JSON-RPC over HTTP.

    This is intentionally simple: configure endpoints in config.yaml. If your server is JSON-RPC,
    set jsonrpc=True and the client will wrap requests accordingly with method names matching keys.
    """
    def __init__(self, base_url: str, jsonrpc: bool = False):
        self.base_url = base_url.rstrip('/')
        self.jsonrpc = jsonrpc
        self._id = 0

    def _rpc(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        self._id += 1
        payload = {"jsonrpc": "2.0", "id": self._id, "method": method, "params": params}
        r = requests.post(self.base_url, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        if "error" in data:
            raise RuntimeError(f"MCP JSON-RPC error: {data['error']}")
        return data.get("result", {})

    def post(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        url = self.base_url + path
        r = requests.post(url, json=data, timeout=30)
        r.raise_for_status()
        return r.json()
