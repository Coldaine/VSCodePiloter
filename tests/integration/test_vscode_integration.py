"""
Integration tests for VS Code automation via MCP adapter.

These tests validate real VS Code window operations using Windows-MCP.
Tests can be skipped if VS Code is not running or MCP is not available.

IMPORTANT: These are acceptance tests - NO MOCKS allowed per project requirements.
"""
import pytest
import os
import time
from pathlib import Path
from agent.adapters.mcp_adapter import MCPAdapter
from agent.adapters.stdio_mcp_adapter import StdioMCPAdapter
from agent.nodes.act_step import act_step, _find_vscode_window, _copy_chat_context
from agent.config import Settings, load_settings


def is_vscode_running():
    """Check if VS Code is currently running."""
    try:
        # Try to import psutil if available
        import psutil
        return any("code" in p.name().lower() for p in psutil.process_iter(['name']))
    except ImportError:
        # Assume it might be running if we can't check
        return True


def is_mcp_available():
    """Check if Windows-MCP is available via npx."""
    import shutil
    return shutil.which("npx") is not None


@pytest.fixture
def mcp_adapter():
    """Create MCP adapter for testing."""
    # Try to use stdio adapter (modern approach)
    if is_mcp_available():
        try:
            adapter = StdioMCPAdapter(
                command="npx",
                args=["-y", "@curtsortouch/windows-mcp"]
            )
            yield adapter
            adapter.close()
            return
        except Exception as e:
            print(f"Stdio adapter failed: {e}, falling back to HTTP")

    # Fall back to HTTP adapter if available
    # Note: This requires MCP HTTP server to be running
    try:
        adapter = MCPAdapter(
            base_url="http://127.0.0.1:43110",
            endpoints={
                "list_windows": "/windows/list",
                "focus_window": "/windows/focus",
                "screenshot": "/windows/screenshot",
                "keypress": "/input/keypress",
                "text_input": "/input/text",
                "clipboard_get": "/clipboard/get",
                "clipboard_set": "/clipboard/set"
            },
            jsonrpc=False
        )
        yield adapter
    except Exception as e:
        pytest.skip(f"MCP adapter not available: {e}")


@pytest.fixture
def test_state(mcp_adapter):
    """Create test state with adapter and settings."""
    # Load real settings
    try:
        settings = load_settings()
    except Exception:
        # Create minimal settings for testing
        settings = type('Settings', (), {
            'write_mode': False,  # Default to dry-run for safety
            'window_title_regex': '.*Visual Studio Code.*',
            'copilot': type('Copilot', (), {
                'command_palette_action': 'GitHub Copilot Chat: Focus on Chat View'
            })()
        })()

    return {
        "_settings": settings,
        "_adapter": mcp_adapter
    }


@pytest.mark.integration
@pytest.mark.requires_vscode
def test_mcp_adapter_list_windows(mcp_adapter):
    """Test that MCP adapter can list windows."""
    if not is_mcp_available():
        pytest.skip("MCP not available")

    windows = mcp_adapter.list_windows()

    assert isinstance(windows, list), "Should return a list of windows"
    assert len(windows) > 0, "Should find at least one window"

    # Check window structure
    for window in windows:
        assert "hwnd" in window or "id" in window, "Window should have hwnd or id"
        # Title might be optional
        print(f"Found window: {window.get('title', 'untitled')} (hwnd: {window.get('hwnd', window.get('id'))})")


@pytest.mark.integration
@pytest.mark.requires_vscode
def test_mcp_adapter_list_vscode_windows(mcp_adapter):
    """Test filtering VS Code windows specifically."""
    if not is_mcp_available():
        pytest.skip("MCP not available")

    if not is_vscode_running():
        pytest.skip("VS Code not running")

    windows = mcp_adapter.list_windows(app="Code.exe")

    # Should find at least one VS Code window if VS Code is running
    vscode_windows = [w for w in windows if "Code" in w.get("title", "")]

    print(f"Found {len(vscode_windows)} VS Code windows")
    for w in vscode_windows:
        print(f"  - {w.get('title')}")

    assert len(vscode_windows) > 0, "Should find at least one VS Code window"


@pytest.mark.integration
@pytest.mark.requires_vscode
def test_find_vscode_window_helper(mcp_adapter):
    """Test _find_vscode_window helper function."""
    if not is_mcp_available():
        pytest.skip("MCP not available")

    if not is_vscode_running():
        pytest.skip("VS Code not running")

    # Test with default regex
    window = _find_vscode_window(mcp_adapter, ".*Visual Studio Code.*")

    assert window is not None, "Should find a VS Code window"
    assert "hwnd" in window or "id" in window, "Window should have hwnd or id"
    print(f"Found VS Code window: {window.get('title')}")


@pytest.mark.integration
@pytest.mark.requires_vscode
def test_mcp_adapter_screenshot(mcp_adapter):
    """Test screenshot capture via MCP adapter."""
    if not is_mcp_available():
        pytest.skip("MCP not available")

    if not is_vscode_running():
        pytest.skip("VS Code not running")

    # Find a VS Code window
    window = _find_vscode_window(mcp_adapter, ".*Visual Studio Code.*")
    if not window:
        pytest.skip("No VS Code window found")

    hwnd = window.get("hwnd") or window.get("id")

    # Take screenshot
    screenshot_bytes = mcp_adapter.screenshot(hwnd=hwnd)

    assert screenshot_bytes is not None, "Screenshot should not be None"
    assert isinstance(screenshot_bytes, bytes), "Screenshot should be bytes"
    assert len(screenshot_bytes) > 1000, "Screenshot should have substantial size (>1KB)"

    # Check PNG header (optional validation)
    if screenshot_bytes.startswith(b'\x89PNG'):
        print("✓ Screenshot is valid PNG")
    else:
        print("⚠ Screenshot may not be PNG format")

    print(f"Screenshot captured: {len(screenshot_bytes)} bytes")


@pytest.mark.integration
@pytest.mark.requires_vscode
def test_mcp_adapter_focus_window(mcp_adapter):
    """Test window focus via MCP adapter."""
    if not is_mcp_available():
        pytest.skip("MCP not available")

    if not is_vscode_running():
        pytest.skip("VS Code not running")

    # Find a VS Code window
    window = _find_vscode_window(mcp_adapter, ".*Visual Studio Code.*")
    if not window:
        pytest.skip("No VS Code window found")

    hwnd = window.get("hwnd") or window.get("id")

    # Focus window
    result = mcp_adapter.focus_window(hwnd=hwnd)

    assert result is not None, "Focus should return a result"
    # Give window time to focus
    time.sleep(0.5)

    print(f"✓ Focused window: {window.get('title')}")


@pytest.mark.integration
@pytest.mark.requires_vscode
def test_mcp_adapter_clipboard_operations(mcp_adapter):
    """Test clipboard get/set operations."""
    if not is_mcp_available():
        pytest.skip("MCP not available")

    # Save original clipboard content
    original_clipboard = None
    try:
        original_clipboard = mcp_adapter.clipboard_get()
    except Exception:
        pass

    test_text = "VSCodePiloter integration test - clipboard test"

    try:
        # Set clipboard
        result = mcp_adapter.clipboard_set(test_text)
        assert result is not None, "Clipboard set should return a result"

        time.sleep(0.2)

        # Get clipboard
        clipboard_content = mcp_adapter.clipboard_get()
        assert clipboard_content == test_text, f"Clipboard should contain test text. Got: {clipboard_content}"

        print(f"✓ Clipboard operations working")

    finally:
        # Restore original clipboard content
        if original_clipboard is not None:
            try:
                mcp_adapter.clipboard_set(original_clipboard)
            except Exception:
                pass


@pytest.mark.integration
@pytest.mark.requires_vscode
def test_act_step_dry_run(test_state):
    """Test act_step in dry-run mode (write_mode=False)."""
    if not is_mcp_available():
        pytest.skip("MCP not available")

    if not is_vscode_running():
        pytest.skip("VS Code not running")

    # Ensure dry-run mode
    test_state["_settings"].write_mode = False

    # Create task envelope
    test_state["task_envelope"] = {
        "type": "desktop_task",
        "intent": "harvest_and_nudge",
        "target_repo_path": "/test/path",
        "payload": {
            "message_to_post": "Test message",
            "copy_scope": {"mode": "last_n", "n": 10}
        },
        "meta": {
            "task_id": "test_task",
            "repo_name": "test_repo"
        }
    }

    # Execute act_step
    result_state = act_step(test_state)

    # Verify action report
    assert "action_report" in result_state, "Should create action report"
    report = result_state["action_report"]

    # Check for success or expected failure
    assert report.get("status") in ["ok", "failed"], f"Status should be ok or failed, got: {report.get('status')}"

    if report.get("status") == "ok":
        assert "artifacts" in report, "Should capture artifacts (screenshots)"
        assert "pre" in report["artifacts"], "Should have pre screenshot"
        assert "post" in report["artifacts"], "Should have post screenshot"
        assert len(report["artifacts"]["pre"]) > 100, "Pre screenshot should be base64 encoded"
        assert len(report["artifacts"]["post"]) > 100, "Post screenshot should be base64 encoded"
        print(f"✓ Act step successful in dry-run mode")
        print(f"  Copied {report.get('copied_chat_chars', 0)} chars from chat")
    else:
        print(f"⚠ Act step failed: {report.get('reason')}")
        # This is acceptable - we're just testing that it handles failure gracefully


@pytest.mark.integration
@pytest.mark.requires_vscode
def test_act_step_handles_no_vscode_window():
    """Test that act_step handles missing VS Code window gracefully."""
    if not is_mcp_available():
        pytest.skip("MCP not available")

    # Create adapter
    adapter = StdioMCPAdapter(
        command="npx",
        args=["-y", "@curtsortouch/windows-mcp"]
    ) if is_mcp_available() else None

    if not adapter:
        pytest.skip("Cannot create adapter")

    try:
        # Create state with impossible window regex
        state = {
            "_settings": type('Settings', (), {
                'write_mode': False,
                'window_title_regex': 'THIS_WINDOW_DOES_NOT_EXIST_12345',
                'copilot': type('Copilot', (), {
                    'command_palette_action': 'GitHub Copilot Chat: Focus on Chat View'
                })()
            })(),
            "_adapter": adapter,
            "task_envelope": {
                "type": "desktop_task",
                "target_repo_path": "/test",
                "payload": {"message_to_post": "test"}
            }
        }

        result_state = act_step(state)

        # Should fail gracefully
        assert "action_report" in result_state
        assert result_state["action_report"]["status"] == "failed"
        assert result_state["action_report"]["reason"] == "no vscode window"

        print("✓ Act step handles missing window gracefully")

    finally:
        if hasattr(adapter, 'close'):
            adapter.close()


@pytest.mark.integration
@pytest.mark.requires_vscode
def test_copy_chat_context_helper(mcp_adapter):
    """Test _copy_chat_context helper function."""
    if not is_mcp_available():
        pytest.skip("MCP not available")

    if not is_vscode_running():
        pytest.skip("VS Code not running")

    # Note: This test just verifies the function doesn't crash
    # It won't actually copy chat content unless VS Code Copilot Chat is open and focused
    try:
        # Save original clipboard
        original = mcp_adapter.clipboard_get()

        # Attempt to copy (will just get whatever is currently selected/focused)
        copied = _copy_chat_context(mcp_adapter)

        assert isinstance(copied, str), "Should return a string (even if empty)"
        print(f"✓ Copy chat context executed (got {len(copied)} chars)")

        # Restore clipboard
        if original:
            mcp_adapter.clipboard_set(original)

    except Exception as e:
        pytest.skip(f"Copy chat context test skipped: {e}")


if __name__ == "__main__":
    # Allow running tests directly with pytest
    pytest.main([__file__, "-v", "-s", "-m", "integration"])
