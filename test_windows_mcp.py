#!/usr/bin/env python
"""Test script to verify Windows-MCP connection."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_connection():
    """Test Windows-MCP connection."""
    try:
        from agent.tools.vscode_copilot_monitor import VSCodeCopilotMonitor

        print("Creating VSCodeCopilotMonitor...")
        monitor = VSCodeCopilotMonitor()

        print(f"Windows-MCP path: {monitor.windows_mcp_path}")
        print(f"Command: {monitor.command}")
        print(f"Args: {monitor.command_args}")

        print("\nConnecting to Windows-MCP...")
        results = await monitor.connect()

        print(f"\n[SUCCESS] Connected!")
        print(f"Checked {len(results)} VS Code windows")

        for result in results:
            print(f"\nWindow: {result.get('title', 'Unknown')}")
            print(f"  Status: {'BUSY' if result.get('is_busy') else 'READY'}")
            print(f"  Copilot text length: {result.get('copilot_text_length', 0)}")
            print(f"  Transcript length: {result.get('transcript_length', 0)}")

        return True

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)