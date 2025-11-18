"""Helpers for analyzing VSCodeCopilotMonitor run summaries."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Optional

__all__ = [
    "load_summary",
    "compute_window_stats",
    "latest_summary_path",
]


def load_summary(path: Path | str) -> Dict[str, Any]:
    """Load a monitor run summary JSON file."""

    summary_path = Path(path)
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    return data


def compute_window_stats(summary: Dict[str, Any]) -> Dict[str, Any]:
    """Compute aggregate metrics from a monitor summary structure."""

    windows: List[Dict[str, Any]] = summary.get("window_metrics") or []

    def _numbers(field: str) -> List[float]:
        values: List[float] = []
        for metric in windows:
            value = metric.get(field)
            if isinstance(value, (int, float)):
                values.append(float(value))
        return values

    def _avg(values: List[float]) -> float:
        if not values:
            return 0.0
        return round(mean(values), 2)

    stats = {
        "window_count": len(windows),
        "busy_windows": sum(1 for m in windows if m.get("is_busy")),
        "ready_windows": sum(1 for m in windows if m.get("is_busy") is False),
        "screenshots_missing": sum(1 for m in windows if not m.get("screenshot")),
        "avg_focus_ms": _avg(_numbers("focus_ms")),
        "avg_state_ms": _avg(_numbers("state_ms")),
        "avg_transcript_ms": _avg(_numbers("transcript_ms")),
        "avg_copilot_chars": _avg(_numbers("copilot_text_length")),
        "avg_transcript_chars": _avg(_numbers("transcript_length")),
        "max_copilot_chars": max(_numbers("copilot_text_length") or [0.0]),
        "max_transcript_chars": max(_numbers("transcript_length") or [0.0]),
    }

    return stats


def latest_summary_path(log_dir: Path | str = Path("logs")) -> Optional[Path]:
    """Return the newest monitor summary file if available."""

    base = Path(log_dir)
    summaries_dir = base / "summaries"
    if not summaries_dir.exists():
        return None
    summaries = sorted(summaries_dir.glob("vscode_monitor_*.json"))
    return summaries[-1] if summaries else None

