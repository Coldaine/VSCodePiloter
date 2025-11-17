"""VS Code Copilot Chat monitor for Windows-MCP sessions.

This module exposes :class:`VSCodeCopilotMonitor`, a small utility that
drives the Windows-MCP tools exposed by the CursorTouch/Windows-MCP
project.  It scans every open VS Code window, captures the Copilot Chat
text, fetches the transcript via "Copy All", and reports diffs so that
agents can reason about activity across windows.

The implementation mirrors the reference snippet provided by the user but
adds a few guardrails so it can be imported and unit-tested without a
live MCP server.
"""

from __future__ import annotations

import asyncio
import json
import os
import difflib
from typing import Any, Dict, List, Optional


class VSCodeCopilotMonitor:
    """Monitor VS Code windows for Copilot Chat updates via Windows-MCP."""

    def __init__(
        self,
        windows_mcp_path: str = "C:/Users/pmacl/Windows-MCP",
        *,
        command: str = "uv",
        args: Optional[List[str]] = None,
        busy_diff_threshold: int = 100,
    ):
        self.windows_mcp_path = windows_mcp_path
        self.command = command
        self.command_args = list(args) if args is not None else [
            "--directory",
            windows_mcp_path,
            "run",
            "main.py",
        ]
        self.busy_diff_threshold = busy_diff_threshold
        self.win_session: Any = None
        self.history: Dict[str, Dict[str, str]] = {}
        self.screen_width = 1920
        self.screen_height = 1080

    async def connect(self) -> List[Dict[str, Any]]:
        """Connect to the Windows-MCP server and return window statuses."""

        if self.win_session is not None:
            return await self.run_with_session(self.win_session)

        try:
            from mcp import ClientSession, StdioServerParameters  # type: ignore
            from mcp.client.stdio import stdio_client  # type: ignore
        except ImportError as exc:  # pragma: no cover - exercised in production only
            raise RuntimeError(
                "The 'mcp' package is required to connect to Windows-MCP. "
                "Install it with 'pip install mcp'."
            ) from exc

        params = StdioServerParameters(
            command=self.command,
            args=self.command_args,
        )

        async with stdio_client(params) as (win_read, win_write):
            async with ClientSession(win_read, win_write) as win:
                await win.initialize()
                return await self.run_with_session(win)

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
                result = await self.win_session.call_tool("State-Tool", {})
                text = self._extract_text(result)
                if not text:
                    return {}
                return json.loads(text)
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
            x = int(window.get("x", 0)) + 50
            y = int(window.get("y", 0)) + 15
            await self.win_session.call_tool(
                "Click-Tool",
                {"coordinate": [x, y], "button": "left"},
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
                    {"coordinate": [copy_all_elem.get("x"), copy_all_elem.get("y")], "button": "left"},
                )
                await asyncio.sleep(0.3)
            else:
                chat_x = int(self.screen_width * 0.8)
                chat_y = int(self.screen_height * 0.5)
                await self.win_session.call_tool(
                    "Click-Tool",
                    {"coordinate": [chat_x, chat_y], "button": "right"},
                )
                await asyncio.sleep(0.3)
                await self.win_session.call_tool(
                    "Click-Tool",
                    {"coordinate": [chat_x, chat_y + 30], "button": "left"},
                )
                await asyncio.sleep(0.3)

            clipboard_result = await self.win_session.call_tool(
                "Clipboard-Tool",
                {"action": "paste"},
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

    windows_mcp_path = os.environ.get("WINDOWS_MCP_PATH", "C:/Users/pmacl/Windows-MCP")
    monitor = VSCodeCopilotMonitor(windows_mcp_path)
    results = await monitor.connect()
    print(f"\n{'=' * 70}")
    print(f"✅ Checked {len(results)} VS Code windows")
    print(f"{'=' * 70}")
    return results


if __name__ == "__main__":  # pragma: no cover - manual execution
    asyncio.run(main())
