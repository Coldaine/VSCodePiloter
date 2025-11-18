import asyncio
import json

from agent.tools.vscode_copilot_monitor import VSCodeCopilotMonitor


class _FakeContent:
    def __init__(self, text: str = ""):
        self.text = text


class _FakeResponse:
    def __init__(self, text: str = ""):
        self.content = [_FakeContent(text)]


class _FakeSession:
    def __init__(self, states, transcript_text: str):
        self.states = list(states)
        self.transcript_text = transcript_text
        self.calls = []

    async def call_tool(self, name: str, payload):
        self.calls.append((name, payload))
        if name == "State-Tool":
            if not self.states:
                raise RuntimeError("No more states queued")
            state = self.states.pop(0)
            return _FakeResponse(json.dumps(state))
        if name == "Powershell-Tool":
            return _FakeResponse(self.transcript_text)
        if name == "Click-Tool":
            return _FakeResponse("")
        raise AssertionError(f"Unexpected tool call: {name}")


def _run(coro):
    return asyncio.run(coro)


def test_filter_vscode_windows_only_matches_titles():
    monitor = VSCodeCopilotMonitor("fake-path")
    state = {
        "windows": [
            {"title": "proj - Visual Studio Code"},
            {"title": "Terminal"},
            {"title": "Code - Insiders"},
            {"title": None},
        ]
    }

    filtered = monitor._filter_vscode_windows(state)

    titles = [w["title"] for w in filtered]
    assert titles == ["proj - Visual Studio Code", "Code - Insiders"]


def test_extract_copilot_text_limits_to_right_side():
    monitor = VSCodeCopilotMonitor("fake-path")
    window = {"x": 100, "y": 50, "width": 1000, "height": 600}
    state = {
        "textual": [
            {"x": 120, "y": 60, "text": "Explorer"},
            {"x": 980, "y": 80, "text": "Hello"},
            {"x": 950, "y": 150, "text": "World"},
        ]
    }

    text = monitor._extract_copilot_text(state, window)

    assert "Explorer" not in text
    assert "Hello" in text and "World" in text


def test_monitor_tracks_history_and_busy_detection():
    window = {
        "title": "sample - Visual Studio Code",
        "x": 100,
        "y": 100,
        "width": 1200,
        "height": 800,
    }

    textual_first = [
        {"x": 950, "y": 200, "text": "Thinking..."},
        {"x": 1050, "y": 250, "text": "Working on it"},
    ]
    textual_second = [
        {"x": 960, "y": 200, "text": "Answer ready"},
        {"x": 1040, "y": 250, "text": "Thanks for waiting"},
    ]

    states_run_one = [
        {"windows": [window], "textual": [], "screen_width": 2000, "screen_height": 1200},
        {"windows": [window], "textual": []},
        {"windows": [window], "textual": textual_first},
    ]

    monitor = VSCodeCopilotMonitor("fake-path", busy_diff_threshold=500)
    session_one = _FakeSession(states_run_one, "Transcript one")

    results_one = _run(monitor.run_with_session(session_one))
    assert len(results_one) == 1
    assert results_one[0]["is_busy"] is True
    assert any(call[0] == "Click-Tool" for call in session_one.calls)
    assert monitor.history[window["title"]]["transcript"] == "Transcript one"

    states_run_two = [
        {"windows": [window], "textual": [], "screen_width": 2000, "screen_height": 1200},
        {"windows": [window], "textual": []},
        {"windows": [window], "textual": textual_second},
    ]

    session_two = _FakeSession(states_run_two, "Transcript two")
    results_two = _run(monitor.run_with_session(session_two))

    assert len(results_two) == 1
    assert results_two[0]["is_busy"] is False
    assert "Transcript two" in results_two[0]["transcript_diff"]
    assert monitor.history[window["title"]]["copilot_text"].startswith("Answer ready")
