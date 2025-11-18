#!/usr/bin/env python
"""Discover available tools from Windows-MCP."""

import asyncio
import json
import subprocess
import sys

async def discover_tools():
    """Discover available tools from Windows-MCP."""
    print("Discovering tools from Windows-MCP...")
    print("-" * 50)

    # Start Windows-MCP
    process = subprocess.Popen(
        ["uv", "--directory", "C:/Users/pmacl/Windows-MCP", "run", "main.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
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
                "name": "Tool-Discoverer",
                "version": "0.1.0"
            }
        }
    }

    print("Sending initialize...")
    process.stdin.write(json.dumps(init_request) + '\n')
    process.stdin.flush()

    # Read response
    response = process.stdout.readline()
    print(f"Initialize response: {response.strip()}")

    # Send initialized notification
    notif = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {}
    }
    process.stdin.write(json.dumps(notif) + '\n')
    process.stdin.flush()

    # Send tools/list request
    tools_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }

    print("Requesting tools list...")
    process.stdin.write(json.dumps(tools_request) + '\n')
    process.stdin.flush()

    # Read tools response
    tools_response = process.stdout.readline()
    print(f"Tools response: {tools_response.strip()}")

    try:
        parsed = json.loads(tools_response)
        if "result" in parsed and "tools" in parsed["result"]:
            tools = parsed["result"]["tools"]
            print(f"\nFound {len(tools)} tools:")
            for tool in tools:
                print(f"  - {tool.get('name', 'Unknown')}")
                if "description" in tool:
                    print(f"    {tool['description']}")
                if "inputSchema" in tool:
                    schema = tool["inputSchema"]
                    if "properties" in schema:
                        props = schema["properties"]
                        print(f"    Parameters: {list(props.keys())}")
                        for prop_name, prop_info in props.items():
                            prop_type = prop_info.get("type", "unknown")
                            print(f"      {prop_name}: {prop_type}")
    except json.JSONDecodeError as e:
        print(f"Failed to parse tools response: {e}")

    # Cleanup
    process.terminate()
    process.wait()

if __name__ == "__main__":
    asyncio.run(discover_tools())