#!/usr/bin/env python
"""Debug Windows-MCP State-Tool and window detection."""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

async def test_direct_mcp():
    """Test Windows-MCP directly via subprocess to see raw output."""
    print("Testing Windows-MCP directly...")
    print("-" * 60)

    # Start Windows-MCP (use binary mode to avoid encoding issues)
    process = subprocess.Popen(
        ["uv", "--directory", "C:/Users/pmacl/Windows-MCP", "run", "main.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False  # Binary mode to handle all characters
    )

    # Send initialize request
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "VSCodePiloter-Debug",
                "version": "0.1.0"
            }
        }
    }

    print(f"Sending: {json.dumps(init_request, indent=2)}")
    process.stdin.write((json.dumps(init_request) + '\n').encode('utf-8'))
    process.stdin.flush()

    # Read response
    print("\nWaiting for response...")
    response = process.stdout.readline()
    print(f"Raw response: {response.decode('utf-8', errors='replace')}")

    if response:
        try:
            parsed = json.loads(response.decode('utf-8', errors='replace'))
            print(f"Parsed: {json.dumps(parsed, indent=2)}")
        except json.JSONDecodeError as e:
            print(f"JSON Error: {e}")

    # Send initialized notification
    init_notif = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {}
    }

    print(f"\nSending notification: {json.dumps(init_notif, indent=2)}")
    process.stdin.write((json.dumps(init_notif) + '\n').encode('utf-8'))
    process.stdin.flush()

    # Call State-Tool
    state_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "State-Tool",
            "arguments": {}
        }
    }

    print(f"\nCalling State-Tool: {json.dumps(state_request, indent=2)}")
    process.stdin.write((json.dumps(state_request) + '\n').encode('utf-8'))
    process.stdin.flush()

    # Read State-Tool response
    print("\nWaiting for State-Tool response...")
    for _ in range(10):  # Try reading multiple lines
        line = process.stdout.readline()
        if line:
            line_str = line.decode('utf-8', errors='replace').strip()
            print(f"Line {_+1}: {line_str[:200]}...")  # Show first 200 chars
            try:
                parsed = json.loads(line_str)
                print(f"Parsed: {json.dumps(parsed, indent=2)[:500]}...")
                if "result" in parsed:
                    # Check if result has content
                    result = parsed.get("result", {})
                    if isinstance(result, dict) and "content" in result:
                        content = result["content"]
                        if isinstance(content, list) and len(content) > 0:
                            text_item = content[0]
                            if isinstance(text_item, dict) and "text" in text_item:
                                state_text = text_item["text"]
                                print(f"\nState-Tool returned text of length: {len(state_text)}")
                                # Try parsing the text as JSON
                                try:
                                    state_data = json.loads(state_text)
                                    print(f"State data keys: {list(state_data.keys())}")
                                    if "windows" in state_data:
                                        print(f"Found {len(state_data['windows'])} windows")
                                        for w in state_data['windows'][:3]:  # Show first 3
                                            print(f"  - {w.get('title', 'No title')}")
                                except json.JSONDecodeError as e:
                                    print(f"State text is not JSON: {e}")
                                    print(f"First 200 chars: {state_text[:200]}")
                    break
            except json.JSONDecodeError:
                pass
        else:
            break

    # Check stderr for any errors
    print("\nChecking stderr...")
    process.poll()
    if process.stderr:
        stderr_output = process.stderr.read()
        if stderr_output:
            print(f"Stderr: {stderr_output}")

    # Cleanup
    process.terminate()
    process.wait()
    print("\nTest complete.")

async def test_with_mcp_sdk():
    """Test using the Python MCP SDK like vscode_copilot_monitor does."""
    print("\n" + "=" * 60)
    print("Testing with Python MCP SDK...")
    print("=" * 60)

    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
    except ImportError:
        print("MCP SDK not available")
        return

    params = StdioServerParameters(
        command="uv",
        args=["--directory", "C:/Users/pmacl/Windows-MCP", "run", "main.py"]
    )

    try:
        async with stdio_client(params) as (win_read, win_write):
            async with ClientSession(win_read, win_write) as win:
                await win.initialize()
                print("MCP session initialized")

                # Call State-Tool
                print("\nCalling State-Tool...")
                result = await win.call_tool("State-Tool", {})

                print(f"Result type: {type(result)}")
                print(f"Result attributes: {dir(result)}")

                # Extract text content
                if hasattr(result, 'content'):
                    for item in result.content:
                        if hasattr(item, 'text'):
                            text = item.text
                            print(f"Text length: {len(text)}")
                            print(f"First 500 chars: {text[:500]}")

                            # Try to parse as JSON
                            try:
                                data = json.loads(text)
                                print(f"\nParsed JSON keys: {list(data.keys())}")
                                if 'windows' in data:
                                    print(f"Found {len(data['windows'])} windows")
                                    for w in data['windows'][:3]:
                                        print(f"  - {w.get('title', 'No title')}")
                            except json.JSONDecodeError as e:
                                print(f"Failed to parse as JSON: {e}")
                                # Show the problematic part
                                lines = text.split('\n')
                                for i, line in enumerate(lines[:10]):
                                    print(f"Line {i+1}: {line[:100]}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run all debug tests."""
    await test_direct_mcp()
    await test_with_mcp_sdk()

if __name__ == "__main__":
    asyncio.run(main())