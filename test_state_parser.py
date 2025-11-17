#!/usr/bin/env python
"""Test parsing State-Tool output."""

import re

def parse_state_tool_output(text: str) -> dict:
    """Parse the text output from State-Tool into structured data."""
    result = {
        "windows": [],
        "textual": [],
        "screen_width": 1920,
        "screen_height": 1080,
    }

    # Find the table section
    lines = text.split('\n')
    table_start = None
    for i, line in enumerate(lines):
        if line.strip().startswith('Name') and 'Depth' in line and 'Status' in line:
            table_start = i
            break

    if table_start is None:
        return result

    # Skip the separator line
    data_start = table_start + 2

    # Parse each window row
    for line in lines[data_start:]:
        line = line.strip()
        if not line or line.startswith('-'):
            continue

        # Split by multiple spaces, but preserve the name which may have spaces
        # The columns seem to be: Name (long), Depth, Status, Width, Height, Handle
        # Use regex to split on 2+ spaces
        parts = re.split(r'\s{2,}', line)
        if len(parts) >= 6:
            try:
                name = parts[0]
                depth = int(parts[1])
                status = parts[2]
                width = int(parts[3])
                height = int(parts[4])
                handle = parts[5]

                # Extract bounds if possible (assuming centered for now)
                window = {
                    "title": name,
                    "bounds": {
                        "x": 0,  # Would need more parsing
                        "y": 0,
                        "width": width,
                        "height": height,
                    },
                    "handle": handle,
                    "depth": depth,
                    "status": status,
                }
                result["windows"].append(window)
            except (ValueError, IndexError):
                continue

    return result

# Test with sample data
sample_text = """Default Language of User:
    English (United States) with encoding: cp1252

    Focused App:
    Name                                                                                      Depth  Status       Width    Height    Handle
--------------------------------------------------------------------------------------  -------  ---------  -------  --------  --------
CLAUDE.md - E:\\_OneOffs\\VSCodePiloter - Visual Studio Code - Pending                           1  Pending     1920     1040    0x0000000000A00E1A
"""

parsed = parse_state_tool_output(sample_text)
print("Parsed result:")
import json
print(json.dumps(parsed, indent=2))