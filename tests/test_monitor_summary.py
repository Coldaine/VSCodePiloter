import json
from pathlib import Path

import pytest

from agent.diagnostics.monitor_summary import (
    compute_window_stats,
    latest_summary_path,
    load_summary,
)


def test_compute_window_stats_reports_counts():
    summary = {
        "window_metrics": [
            {
                "index": 1,
                "title": "One",
                "is_busy": True,
                "focus_ms": 120.0,
                "state_ms": 85.0,
                "transcript_ms": 210.0,
                "copilot_text_length": 50,
                "transcript_length": 100,
                "screenshot": "a.png",
            },
            {
                "index": 2,
                "title": "Two",
                "is_busy": False,
                "focus_ms": 80.0,
                "state_ms": 75.0,
                "transcript_ms": 190.0,
                "copilot_text_length": 10,
                "transcript_length": 0,
                "screenshot": None,
            },
        ]
    }

    stats = compute_window_stats(summary)

    assert stats["window_count"] == 2
    assert stats["busy_windows"] == 1
    assert stats["screenshots_missing"] == 1
    assert stats["avg_focus_ms"] == pytest.approx(100.0)
    assert stats["max_copilot_chars"] == 50


def test_load_and_locate_summary(tmp_path):
    logs_dir = tmp_path / "logs"
    summaries_dir = logs_dir / "summaries"
    summaries_dir.mkdir(parents=True)

    summary_path = summaries_dir / "vscode_monitor_20250101_000000.json"
    summary_path.write_text(json.dumps({"window_metrics": []}), encoding="utf-8")

    loaded = load_summary(summary_path)
    assert loaded["window_metrics"] == []

    latest = latest_summary_path(logs_dir)
    assert latest == summary_path

