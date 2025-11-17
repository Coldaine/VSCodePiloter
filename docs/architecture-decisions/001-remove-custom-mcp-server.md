# ADR 001: Remove Custom MCP Server Implementation

**Date**: 2025-01-17
**Status**: Accepted
**Deciders**: Project maintainers

## Context

The project initially included a custom MCP HTTP server (`mcp_server/server.py`) that provided Windows automation tools via REST endpoints. This server implemented:

- Window listing and focus
- Screenshot capture
- Keyboard input
- Clipboard operations

However, this violated the project's core principle stated in README.md:

> "Reuse-first: pluggable MCP adapter; minimal net-new automation"

## Problem

1. **Anti-pattern**: Building custom MCP server tools when mature, feature-rich MCP servers already exist
2. **Maintenance burden**: Custom implementation requires ongoing maintenance and testing
3. **Limited capabilities**: Custom server had basic features compared to existing solutions like Windows-MCP
4. **Confusion**: Having both a custom server and references to external MCP servers created architectural ambiguity
5. **Abandoned code**: The HTTP server was never run - it was just example code that looked like production code

## Decision

**Remove `mcp_server/` directory entirely.**

Instead, use:

1. **Fallback Adapter** (default): Direct Windows automation via `pyautogui` + `win32` for the main agent
2. **Windows-MCP** (advanced): External MCP server with rich toolset for `vscode_copilot_monitor`

## Consequences

### Positive

- ✅ **Aligns with project principles**: Reusing existing tools instead of building new ones
- ✅ **Reduces maintenance**: No custom server code to maintain
- ✅ **Clearer architecture**: Single responsibility - agent uses fallback, monitor uses Windows-MCP
- ✅ **Better capabilities**: Windows-MCP provides 15+ tools vs our 7 basic endpoints
- ✅ **Eliminates confusion**: No phantom HTTP server that was never meant to run

### Negative

- ⚠️ **No example server**: Developers wanting HTTP MCP server reference must look elsewhere
- ⚠️ **Fallback adapter limitations**: Less sophisticated than MCP protocol (no retries, no state management)

### Neutral

- The fallback adapter is sufficient for basic automation needs
- Projects needing advanced MCP features should integrate Windows-MCP or similar for the main agent
- Custom MCP servers should only be built for truly unique use cases not covered by existing tools

## Future Options

If HTTP-based MCP is needed in the future:

1. **Use Windows-MCP's HTTP mode**: It supports SSE and streamable HTTP transports
2. **Integrate existing MCP servers**: Many community servers exist for different automation needs
3. **Only build custom tools**: If absolutely necessary, extend existing MCP servers, don't replace them

## Related

- [Windows-MCP Documentation](https://github.com/CursorTouch/Windows-MCP)
- [MCP Registry](https://github.com/modelcontextprotocol/registry)
- Project README.md "Reuse-first" principle
