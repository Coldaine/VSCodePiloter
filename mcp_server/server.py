from __future__ import annotations
import base64
import re
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException

try:
    import win32gui
    import win32con
    import win32api
    import win32clipboard
except Exception as e:  # pragma: no cover
    """Removed. Use external Windows MCP servers instead (e.g., MCPControl).
    This stub remains only to avoid import errors during cleanup.
    """
