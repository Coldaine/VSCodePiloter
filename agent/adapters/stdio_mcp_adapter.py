from __future__ import annotations
import json
import subprocess
import threading
from typing import Any, Dict, List, Optional, BinaryIO
from queue import Queue, Empty
import base64
import logging
from .base import DesktopAdapter

logger = logging.getLogger(__name__)


class StdioMCPAdapter(DesktopAdapter):
    """
    Adapter for MCP servers using stdio transport (the standard MCP protocol).
    
    Launches an MCP server as a subprocess and communicates via JSON-RPC over stdin/stdout.
    This is compatible with standard MCP servers like MCPControl, Windows-MCP, etc.
    """
    
    def __init__(self, command: str, args: List[str], env: Optional[Dict[str, str]] = None):
        """
        Args:
            command: Command to launch the MCP server (e.g., "npx", "node", or full path)
            args: Arguments to pass (e.g., ["-y", "mcp-control"])
            env: Optional environment variables to pass to the subprocess
        """
        self.command = command
        self.args = args
        self.env = env or {}
        self.process: Optional[subprocess.Popen] = None
        self._request_id = 0
        self._response_queue: Queue = Queue()
        self._reader_thread: Optional[threading.Thread] = None
        self._running = False
        
        # Start the MCP server
        self._start_server()
    
    def _start_server(self):
        """Launch the MCP server subprocess and start reader thread."""
        import os
        full_env = os.environ.copy()
        full_env.update(self.env)
        
        logger.info(f"Starting MCP server: {self.command} {' '.join(self.args)}")
        
        self.process = subprocess.Popen(
            [self.command] + self.args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=full_env,
            text=False,  # Binary mode for proper buffering
            bufsize=0
        )
        
        self._running = True
        self._reader_thread = threading.Thread(target=self._read_responses, daemon=True)
        self._reader_thread.start()
        
        # Send initialize request
        self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "VSCodePiloter",
                "version": "0.1.0"
            }
        })
        
        # Wait for initialize response
        response = self._wait_for_response(timeout=5.0)
        if not response or "error" in response:
            raise RuntimeError(f"Failed to initialize MCP server: {response}")
        
        # Send initialized notification
        self._send_notification("notifications/initialized", {})
        logger.info("MCP server initialized successfully")
    
    def _read_responses(self):
        """Background thread to read JSON-RPC responses from server stdout."""
        if not self.process or not self.process.stdout:
            return
            
        buffer = b""
        while self._running:
            try:
                chunk = self.process.stdout.read(1)
                if not chunk:
                    break
                    
                buffer += chunk
                
                # Try to parse complete JSON objects
                if buffer.endswith(b'\n'):
                    try:
                        lines = buffer.split(b'\n')
                        for line in lines:
                            if line.strip():
                                response = json.loads(line.decode('utf-8'))
                                self._response_queue.put(response)
                        buffer = b""
                    except json.JSONDecodeError:
                        # Not complete yet, keep buffering
                        pass
            except Exception as e:
                if self._running:
                    logger.error(f"Error reading MCP response: {e}")
                break
    
    def _send_request(self, method: str, params: Dict[str, Any]) -> int:
        """Send a JSON-RPC request to the MCP server."""
        self._request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params
        }
        
        if self.process and self.process.stdin:
            message = json.dumps(request) + '\n'
            self.process.stdin.write(message.encode('utf-8'))
            self.process.stdin.flush()
        
        return self._request_id
    
    def _send_notification(self, method: str, params: Dict[str, Any]):
        """Send a JSON-RPC notification (no response expected)."""
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }
        
        if self.process and self.process.stdin:
            message = json.dumps(notification) + '\n'
            self.process.stdin.write(message.encode('utf-8'))
            self.process.stdin.flush()
    
    def _wait_for_response(self, timeout: float = 10.0) -> Optional[Dict[str, Any]]:
        """Wait for the next response from the queue."""
        try:
            return self._response_queue.get(timeout=timeout)
        except Empty:
            logger.warning(f"Timeout waiting for MCP response after {timeout}s")
            return None
    
    def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool and return the result."""
        req_id = self._send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })
        
        response = self._wait_for_response()
        if not response:
            raise RuntimeError(f"No response for tool call: {tool_name}")
        
        if "error" in response:
            raise RuntimeError(f"MCP tool error: {response['error']}")
        
        return response.get("result", {})
    
    # DesktopAdapter interface implementation
    
    def list_windows(self, app: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all windows, optionally filtered by app name."""
        result = self._call_tool("list_windows", {"app": app} if app else {})
        return result.get("windows", [])
    
    def focus_window(self, hwnd: Optional[int] = None, title_regex: Optional[str] = None) -> Dict[str, Any]:
        """Focus a window by handle or title regex."""
        args = {}
        if hwnd is not None:
            args["hwnd"] = hwnd
        if title_regex is not None:
            args["title_regex"] = title_regex
        
        return self._call_tool("focus_window", args)
    
    def screenshot(self, hwnd: Optional[int] = None) -> bytes:
        """Take a screenshot of a window."""
        result = self._call_tool("screenshot", {"hwnd": hwnd} if hwnd else {})
        
        # Expect base64-encoded image
        b64_image = result.get("image")
        if not b64_image:
            raise RuntimeError("MCP server returned no image data")
        
        return base64.b64decode(b64_image)
    
    def keypress(self, keys: str) -> Dict[str, Any]:
        """Send a keypress (e.g., 'Ctrl+Shift+P')."""
        return self._call_tool("keypress", {"keys": keys})
    
    def text_input(self, text: str) -> Dict[str, Any]:
        """Type text."""
        return self._call_tool("text_input", {"text": text})
    
    def clipboard_get(self) -> str:
        """Get clipboard contents."""
        result = self._call_tool("clipboard_get", {})
        return result.get("text", "")
    
    def clipboard_set(self, text: str) -> Dict[str, Any]:
        """Set clipboard contents."""
        return self._call_tool("clipboard_set", {"text": text})
    
    def __del__(self):
        """Cleanup: terminate the MCP server process."""
        self._running = False
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                self.process.kill()
