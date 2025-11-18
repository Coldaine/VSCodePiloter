#!/usr/bin/env python
"""Live test runner for VS Code monitor with Windows-MCP.

This script runs the heavily instrumented debug version of the monitor
and captures all output to help debug integration issues.

Requirements:
- Windows-MCP must be installed
- MCP Python package must be installed (pip install mcp)
- At least one VS Code window must be open
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import our module
sys.path.insert(0, str(Path(__file__).parent))

from agent.tools.vscode_copilot_monitor_debug import VSCodeCopilotMonitor

async def test_monitor():
    """Run monitor test with detailed output."""

    print("=" * 80)
    print("VS CODE MONITOR LIVE TEST")
    print("=" * 80)
    print()

    # Check environment
    windows_mcp_path = os.environ.get("WINDOWS_MCP_PATH") or str(Path.home() / "Windows-MCP")

    print(f"Windows-MCP Path: {windows_mcp_path}")

    if not Path(windows_mcp_path).exists():
        print(f"⚠️  WARNING: Path {windows_mcp_path} does not exist!")
        print("   Set WINDOWS_MCP_PATH environment variable to correct location")

    print()
    print("Creating monitor instance...")

    # Create monitor
    monitor = VSCodeCopilotMonitor(
        windows_mcp_path=windows_mcp_path,
        busy_diff_threshold=100  # Lower threshold for testing
    )

    print("Monitor created.")
    print()
    print("Attempting to connect to Windows-MCP...")
    print("-" * 40)

    try:
        # Run monitor
        results = await monitor.connect()

        print()
        print("=" * 80)
        print("RESULTS")
        print("=" * 80)
        print()

        if not results:
            print("❌ No results returned!")
        else:
            print(f"✅ Checked {len(results)} VS Code windows")
            print()

            for i, result in enumerate(results, 1):
                print(f"Window {i}:")
                print(f"  Title: {result.get('title', 'unknown')}")

                if result.get("error"):
                    print(f"  ❌ ERROR: {result['error']}")
                else:
                    print(f"  Status: {'🔴 BUSY' if result.get('is_busy') else '🟢 READY'}")
                    print(f"  Copilot text length: {result.get('copilot_text_length', 0)}")
                    print(f"  Transcript length: {result.get('transcript_length', 0)}")

                    if result.get("text_diff"):
                        print(f"  Text changes: {len(result['text_diff'])} chars")

                    if result.get("transcript_diff"):
                        print(f"  Transcript changes: {len(result['transcript_diff'])} chars")

                print()

        # Check log file
        log_dir = Path("logs")
        if log_dir.exists():
            log_files = sorted(log_dir.glob("vscode_monitor_*.log"))
            if log_files:
                latest_log = log_files[-1]
                print(f"📝 Log file created: {latest_log}")
                print(f"   Size: {latest_log.stat().st_size:,} bytes")
                print()
                print("   To view log: notepad " + str(latest_log))
            else:
                print("⚠️  No log file found in logs directory")
        else:
            print("⚠️  Logs directory not created")

    except ImportError as ie:
        print()
        print("❌ Import Error:", ie)
        print()
        print("Make sure MCP is installed:")
        print("  pip install mcp")

    except FileNotFoundError as fe:
        print()
        print("❌ File Not Found:", fe)
        print()
        print("Possible issues:")
        print("  1. Windows-MCP not installed at expected location")
        print("  2. Set WINDOWS_MCP_PATH environment variable")
        print("  3. Make sure 'uv' command is available or Windows-MCP is set up")

    except Exception as e:
        print()
        print("❌ Error:", e)
        print()

        import traceback
        print("Full traceback:")
        print(traceback.format_exc())

    print()
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    print("Starting VS Code Monitor Live Test...")
    print(f"Time: {datetime.now()}")
    print()

    # Check Python version
    print(f"Python: {sys.version}")
    print()

    # Run async test
    try:
        asyncio.run(test_monitor())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)