#!/usr/bin/env python
"""Summarize VSCodeCopilotMonitor runs for quick performance checks."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent.diagnostics.monitor_summary import (  # noqa: E402
    compute_window_stats,
    latest_summary_path,
    load_summary,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--summary",
        type=Path,
        help="Path to a specific vscode_monitor_*.json summary. Defaults to latest run.",
    )
    parser.add_argument(
        "--logs",
        type=Path,
        default=Path("logs"),
        help="Root logs directory (default: logs/)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    summary_path = args.summary
    if summary_path is None:
        summary_path = latest_summary_path(args.logs)

    if summary_path is None or not summary_path.exists():
        print("⚠️  No monitor summary found. Run test_monitor_live.py first.")
        return 1

    summary = load_summary(summary_path)
    stats = compute_window_stats(summary)

    print(f"Summary: {summary_path}")
    print(f"Log file: {summary.get('log_path')}")
    print(f"Screenshots: {summary.get('screenshot_dir')}")
    print()
    print(f"Windows processed: {stats['window_count']}")
    print(f"Busy windows: {stats['busy_windows']} | Ready windows: {stats['ready_windows']}")
    print(f"Screenshots missing: {stats['screenshots_missing']}")
    print()
    print("Timings (ms):")
    print(
        f"  Focus avg={stats['avg_focus_ms']} | State avg={stats['avg_state_ms']} | "
        f"Transcript avg={stats['avg_transcript_ms']}"
    )
    print("Characters:")
    print(
        f"  Copilot avg={stats['avg_copilot_chars']} max={stats['max_copilot_chars']} | "
        f"Transcript avg={stats['avg_transcript_chars']} max={stats['max_transcript_chars']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

