"""VS Code Copilot Chat monitor with extensive debug logging.

This is a heavily instrumented version of vscode_copilot_monitor.py
with detailed logging at every step for debugging Windows-MCP integration issues.
"""

from __future__ import annotations

import asyncio
import json
import os
import difflib
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Set up file-based logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"vscode_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Configure logger with both file and console output
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# File handler with detailed formatting
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter(
    '%(asctime)s.%(msecs)03d | %(levelname)-8s | %(funcName)-20s | L%(lineno)4d | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Console handler with simpler formatting
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)-8s | %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

logger.info(f"=== VS Code Monitor Session Started ===")
logger.info(f"Log file: {log_file.absolute()}")


def parse_state_tool_text(text: str) -> Dict[str, Any]:
    """Parse State-Tool plain text output into structured data.
    
    State-Tool returns formatted tables, not JSON:
    - "Opened Apps:" section contains window info
    - "List of Interactive Elements:" contains UI elements with coordinates
    """
    
    result = {
        'windows': [],
        'textual': [],
        'screen_width': 1920,
        'screen_height': 1080,
    }
    
    lines = text.split('\n')
    
    in_apps_section = False
    in_interactive_section = False
    header_seen = False
    
    for line in lines:
        stripped = line.strip()
        
        # Detect sections
        if 'Opened Apps:' in line or 'Focused App:' in line:
            in_apps_section = True
            in_interactive_section = False
            header_seen = False
            continue
        
        if 'List of Interactive Elements:' in line:
            in_apps_section = False
            in_interactive_section = True
            header_seen = False
            continue
        
        if 'List of Scrollable Elements:' in line:
            in_apps_section = False
            in_interactive_section = False
            continue
        
        # Skip headers and separators
        if '---' in line or not stripped:
            if '---' in line:
                header_seen = True
            continue
        
        if not header_seen:
            continue
        
        # Parse window lines from apps section
        if in_apps_section:
            parts = stripped.split()
            
            if len(parts) >= 5:
                try:
                    handle = parts[-1]
                    height = int(parts[-2])
                    width = int(parts[-3])
                    status = parts[-4]
                    depth = parts[-5]
                    
                    title_parts = parts[:-5]
                    title = ' '.join(title_parts) if title_parts else 'Unknown'
                    
                    result['windows'].append({
                        'title': title,
                        'depth': depth,
                        'status': status,
                        'width': width,
                        'height': height,
                        'handle': handle,
                        'x': 0,
                        'y': 0,
                    })
                except (ValueError, IndexError) as e:
                    logger.debug(f"Failed to parse window line: '{stripped}' with error: {e}")
        
        # Parse interactive elements (Name + Coordinates columns)
        elif in_interactive_section:
            # Look for coordinate tuples like (1234,5678)
            import re
            coord_match = re.search(r'\((\d+),(\d+)\)', stripped)
            
            if coord_match:
                try:
                    x = int(coord_match.group(1))
                    y = int(coord_match.group(2))
                    
                    # Extract text before coordinates
                    text_part = stripped[:coord_match.start()].strip()
                    
                    # Remove leading label number if present
                    text_parts = text_part.split(maxsplit=3)
                    if len(text_parts) >= 3:
                        # Skip label, app name, control type - keep name/value
                        text_content = ' '.join(text_parts[3:]) if len(text_parts) > 3 else text_parts[-1]
                    else:
                        text_content = text_part
                    
                    if text_content:
                        result['textual'].append({
                            'text': text_content,
                            'x': x,
                            'y': y,
                        })
                except (ValueError, IndexError) as e:
                    logger.debug(f"Failed to parse interactive element line: '{stripped}'. Exception: {e}")
    
    return result


class VSCodeCopilotMonitor:
    """Monitor VS Code windows for Copilot Chat updates via Windows-MCP."""

    def __init__(
        self,
        windows_mcp_path: Optional[str] = None,
        *,
        command: str = "uv",
        args: Optional[List[str]] = None,
        busy_diff_threshold: int = 100,
    ):
        resolved_path = windows_mcp_path or os.environ.get("WINDOWS_MCP_PATH") or str(Path.home() / "Windows-MCP")
        self.windows_mcp_path = resolved_path
        self.command = command
        self.command_args = list(args) if args is not None else [
            "--directory",
            resolved_path,
            "run",
            "main.py",
        ]
        self.busy_diff_threshold = busy_diff_threshold
        self.win_session: Any = None
        self.history: Dict[str, Dict[str, str]] = {}
        self.screen_width = 1920
        self.screen_height = 1080

        logger.info(f"Monitor initialized with:")
        logger.info(f"  - MCP Path: {windows_mcp_path}")
        logger.info(f"  - Command: {command}")
        logger.info(f"  - Args: {self.command_args}")
        logger.info(f"  - Busy threshold: {busy_diff_threshold}")
        logger.info(f"  - Default screen: {self.screen_width}x{self.screen_height}")

    async def connect(self) -> List[Dict[str, Any]]:
        """Connect to the Windows-MCP server and return window statuses."""

        logger.info("=== Starting MCP Connection ===")

        if self.win_session is not None:
            logger.info("Using existing MCP session")
            return await self.run_with_session(self.win_session)

        try:
            logger.info("Importing MCP modules...")
            from mcp import ClientSession, StdioServerParameters  # type: ignore
            from mcp.client.stdio import stdio_client  # type: ignore
            logger.info("MCP modules imported successfully")
        except ImportError as exc:  # pragma: no cover - exercised in production only
            logger.error(f"Failed to import MCP: {exc}")
            logger.error(traceback.format_exc())
            raise RuntimeError(
                "The 'mcp' package is required to connect to Windows-MCP. "
                "Install it with 'pip install mcp'."
            ) from exc

        params = StdioServerParameters(
            command=self.command,
            args=self.command_args,
        )

        logger.info(f"Creating stdio client with command: {self.command} {' '.join(self.command_args)}")

        try:
            async with stdio_client(params) as (win_read, win_write):
                logger.info("Stdio client created, creating ClientSession...")
                async with ClientSession(win_read, win_write) as win:
                    logger.info("ClientSession created, initializing...")
                    await win.initialize()
                    logger.info("MCP session initialized successfully")
                    return await self.run_with_session(win)
        except Exception as exc:
            logger.error(f"Failed to establish MCP connection: {exc}")
            logger.error(traceback.format_exc())
            raise

    async def run_with_session(self, session: Any) -> List[Dict[str, Any]]:
        """Run the monitor using an existing MCP session (handy for tests)."""

        if session is None:
            raise ValueError("session must be provided")

        self.win_session = session
        try:
            initial_state = await self._get_state()
            self.screen_width = int(initial_state.get("screen_width", self.screen_width))
            self.screen_height = int(initial_state.get("screen_height", self.screen_height))
            results = await self.check_all_windows()
            return results
        finally:
            self.win_session = None

    async def _get_state(self, retries: int = 3) -> Dict[str, Any]:
        """Fetch the full desktop state with brief retry logic."""

        if self.win_session is None:
            raise RuntimeError("MCP session is not initialized")

        for attempt in range(retries):
            try:
                # State-Tool returns plain text, not JSON
                result = await self.win_session.call_tool("State-Tool", {})
                text = self._extract_text(result)
                if not text:
                    return {}
                # Parse the structured text format
                return parse_state_tool_text(text)
            except Exception as exc:
                if attempt == retries - 1:
                    print(f"Failed to get state after {retries} attempts: {exc}")
                    break
                await asyncio.sleep(0.5)

        return {
            "windows": [],
            "textual": [],
            "screen_width": self.screen_width,
            "screen_height": self.screen_height,
        }

    async def check_all_windows(self) -> List[Dict[str, Any]]:
        """Check every VS Code window sequentially and return status dicts."""

        if self.win_session is None:
            raise RuntimeError("MCP session is not initialized")

        results: List[Dict[str, Any]] = []
        try:
            state = await self._get_state()
            vscode_windows = self._filter_vscode_windows(state)
            print(f"Found {len(vscode_windows)} VS Code windows")

            for window in vscode_windows:
                try:
                    result = await self._check_window(window)
                    if result:
                        results.append(result)
                except Exception as exc:
                    title = window.get("title", "unknown")
                    print(f"Error checking window '{title}': {exc}")
                    results.append(
                        {
                            "title": title,
                            "error": str(exc),
                            "is_busy": False,
                            "text_diff": "",
                            "transcript_diff": "",
                        }
                    )
        except Exception as exc:
            print(f"Critical error in check_all_windows: {exc}")

        return results

    def _filter_vscode_windows(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return only windows that appear to belong to VS Code."""

        windows = state.get("windows") or []
        vscode_windows = []
        for window in windows:
            if not isinstance(window, dict):
                continue
            title = window.get("title") or ""
            if "Visual Studio Code" in title or "Code - " in title:
                vscode_windows.append(window)
        return vscode_windows

    async def _check_window(self, window: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check Copilot text + transcript for a single VS Code window."""

        title = window.get("title", "unknown")

        if title not in self.history:
            self.history[title] = {"copilot_text": "", "transcript": ""}

        await self._focus_window(window)
        fresh_state = await self._get_state()

        copilot_text = self._extract_copilot_text(fresh_state, window)
        previous_text = self.history[title]["copilot_text"]
        text_diff = self._diff(previous_text, copilot_text)
        is_busy = self._is_busy(text_diff, copilot_text)

        transcript = await self._get_transcript(fresh_state)
        previous_transcript = self.history[title]["transcript"]
        transcript_diff = self._diff(previous_transcript, transcript)

        self.history[title]["copilot_text"] = copilot_text
        self.history[title]["transcript"] = transcript

        self._print_status(title, is_busy, text_diff, transcript_diff)

        return {
            "title": title,
            "is_busy": is_busy,
            "text_diff": text_diff,
            "transcript_diff": transcript_diff,
            "copilot_text_length": len(copilot_text),
            "transcript_length": len(transcript),
        }

    async def _focus_window(self, window: Dict[str, Any]) -> None:
        """Focus a VS Code window by clicking its title bar."""

        if self.win_session is None:
            return

        try:
            win_x = int(window.get("x", 0))
            win_y = int(window.get("y", 0))
            if win_x == 0 and win_y == 0:
                logger.warning("Skipping focus: window coordinates unknown (x=y=0) in fallback state parse")
                return
            x = win_x + 50
            y = win_y + 15
            await self.win_session.call_tool(
                "Click-Tool",
                {"loc": [x, y], "button": "left"},
            )
            await asyncio.sleep(0.5)
        except Exception as exc:
            print(f"Warning: Could not focus window: {exc}")

    def _extract_copilot_text(self, state: Dict[str, Any], window: Dict[str, Any]) -> str:
        """Extract visible text from the approximate Copilot Chat region."""

        textual = state.get("textual") or []
        window_x = float(window.get("x", 0) or 0)
        window_y = float(window.get("y", 0) or 0)
        window_width = float(window.get("width", 0) or 0)
        window_height = float(window.get("height", 0) or 0)

        # If coordinates are unknown (fallback parse), avoid misclassification
        if (window_x == 0 and window_y == 0) or window_width == 0 or window_height == 0:
            logger.warning("Skipping copilot text extraction: window bounds unknown from fallback parse")
            return ""

        window_right = window_x + window_width
        chat_area_left = window_right - (window_width * 0.4)
        window_bottom = window_y + window_height

        copilot_texts: List[str] = []
        for elem in textual:
            if not isinstance(elem, dict):
                continue
            elem_x = elem.get("x")
            elem_y = elem.get("y")
            elem_text = elem.get("text")
            if elem_x is None or elem_y is None or not elem_text:
                continue
            if (
                window_x <= elem_x <= window_right
                and window_y <= elem_y <= window_bottom
                and elem_x >= chat_area_left
            ):
                copilot_texts.append(elem_text)

        return "\n".join(copilot_texts)

    async def _get_transcript(self, state: Dict[str, Any]) -> str:
        """Retrieve the Copilot transcript using "Copy All"."""

        if self.win_session is None:
            return ""

        try:
            copy_all_elem = self._find_element_by_text(state, "Copy All")
            if copy_all_elem:
                await self.win_session.call_tool(
                    "Click-Tool",
                    {"loc": [copy_all_elem.get("x"), copy_all_elem.get("y")], "button": "left"},
                )
                await asyncio.sleep(0.3)
            else:
                chat_x = int(self.screen_width * 0.8)
                chat_y = int(self.screen_height * 0.5)
                await self.win_session.call_tool(
                    "Click-Tool",
                    {"loc": [chat_x, chat_y], "button": "right"},
                )
                await asyncio.sleep(0.3)
                await self.win_session.call_tool(
                    "Click-Tool",
                    {"loc": [chat_x, chat_y + 30], "button": "left"},
                )
                await asyncio.sleep(0.3)

            clipboard_result = await self.win_session.call_tool(
                "Powershell-Tool",
                {"command": "Get-Clipboard -Raw"},
            )
            return self._extract_text(clipboard_result)
        except Exception as exc:
            print(f"Transcript extraction failed: {exc}")
            return ""

    def _find_element_by_text(self, state: Dict[str, Any], target_text: str) -> Optional[Dict[str, Any]]:
        """Find the first textual element that contains the provided text."""

        textual = state.get("textual") or []
        for elem in textual:
            if not isinstance(elem, dict):
                continue
            elem_text = elem.get("text", "")
            if target_text.lower() in elem_text.lower():
                return elem
        return None

    def _is_busy(self, text_diff: str, current_text: str) -> bool:
        """Infer whether Copilot is actively generating a reply."""

        busy_indicators = [
            "generating...",
            "thinking...",
            "typing...",
            "•••",
            "...",
        ]

        current_lower = (current_text or "").lower()
        for indicator in busy_indicators:
            if indicator in current_lower:
                return True

        return len(text_diff) > self.busy_diff_threshold

    @staticmethod
    def _diff(old: str, new: str) -> str:
        """Return a unified diff preview between the provided strings."""

        old = old if isinstance(old, str) else str(old)
        new = new if isinstance(new, str) else str(new)
        if not old and not new:
            return ""

        return "".join(
            difflib.unified_diff(
                old.splitlines(keepends=True),
                new.splitlines(keepends=True),
                n=2,
                lineterm="",
            )
        )

    @staticmethod
    def _extract_text(response: Any) -> str:
        """Return the first textual payload from an MCP response."""

        if response is None:
            return ""
        if isinstance(response, str):
            return response

        content = getattr(response, "content", None)
        if content:
            for item in content:
                text = getattr(item, "text", None)
                if text:
                    return text
                if isinstance(item, dict) and item.get("text"):
                    return item["text"]

        if isinstance(response, dict):
            if isinstance(response.get("text"), str):
                return response["text"]
            items = response.get("content")
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict) and isinstance(item.get("text"), str):
                        return item["text"]

        return ""

    def _print_status(self, title: str, is_busy: bool, text_diff: str, transcript_diff: str) -> None:
        """Print a quick human-readable summary for debugging."""

        print(f"\n{'=' * 70}")
        print(f"Window: {title}")
        print(f"Status: {'🔴 BUSY' if is_busy else '🟢 READY'}")
        print(f"{'=' * 70}")

        if text_diff.strip():
            print("\n📝 Text Changes:")
            preview = text_diff[:500]
            print(preview + ("..." if len(text_diff) > 500 else ""))
        else:
            print("\n📝 Text Changes: None")

        if transcript_diff.strip():
            print("\n💬 Transcript Changes:")
            preview = transcript_diff[:500]
            print(preview + ("..." if len(transcript_diff) > 500 else ""))
        else:
            print("\n💬 Transcript Changes: None")

        print(f"{'=' * 70}\n")


async def main() -> List[Dict[str, Any]]:
    """CLI entry point for manual experimentation."""

    windows_mcp_path = os.environ.get("WINDOWS_MCP_PATH") or str(Path.home() / "Windows-MCP")
    monitor = VSCodeCopilotMonitor(windows_mcp_path)
    results = await monitor.connect()
    print(f"\n{'=' * 70}")
    print(f"✅ Checked {len(results)} VS Code windows")
    print(f"{'=' * 70}")
    return results


if __name__ == "__main__":  # pragma: no cover - manual execution
    asyncio.run(main())
