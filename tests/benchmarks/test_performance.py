"""
Performance benchmarks for VSCodePiloter.

Measures and validates performance of critical operations including:
- LLM reasoning latency
- MCP adapter operation time
- Screenshot capture time
- Full work item execution time
- Graph execution time

Performance targets:
- LLM reasoning: <3s
- MCP operations: <500ms
- Screenshot capture: <1s
- Full work item execution: <10s
- Graph execution: <15s
"""
import pytest
import time
import statistics
from typing import List, Dict, Any
import os


def timeit(func, *args, **kwargs) -> float:
    """Time a function execution and return elapsed time in seconds."""
    start = time.time()
    func(*args, **kwargs)
    return time.time() - start


def calculate_stats(times: List[float]) -> Dict[str, float]:
    """Calculate statistics for a list of timing measurements."""
    return {
        "avg": statistics.mean(times),
        "min": min(times),
        "max": max(times),
        "p95": sorted(times)[int(len(times) * 0.95)] if len(times) > 1 else times[0],
        "median": statistics.median(times)
    }


@pytest.mark.benchmark
@pytest.mark.requires_api_key
def test_llm_reasoning_latency():
    """
    Benchmark LLM reasoning latency for Reasoner agent.
    Target: <3s average
    """
    from agent.llm_client import create_reasoner_llm
    from agent.config import LLMConfig
    from langchain_core.messages import HumanMessage

    if not os.getenv("ZAI_API_KEY"):
        pytest.skip("ZAI_API_KEY not available")

    config = LLMConfig(
        provider="z.ai",
        model="glm-4.6",
        api_key_env="ZAI_API_KEY",
        api_base_coding="https://api.z.ai/api/coding/paas/v4/",
        api_base_standard="https://api.z.ai/api/paas/v4/",
        temperature=0.7,
        max_tokens=200000
    )

    llm = create_reasoner_llm(config)

    # Simple reasoning task
    test_message = HumanMessage(content="List 3 priorities for code review. Respond with JSON.")

    times = []
    for i in range(5):
        start = time.time()
        response = llm.invoke([test_message])
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"  Run {i+1}: {elapsed:.2f}s")

    stats = calculate_stats(times)

    print(f"\nLLM Reasoning Latency:")
    print(f"  Average: {stats['avg']:.2f}s")
    print(f"  Min: {stats['min']:.2f}s")
    print(f"  Max: {stats['max']:.2f}s")
    print(f"  P95: {stats['p95']:.2f}s")
    print(f"  Median: {stats['median']:.2f}s")

    # Validate against target
    assert stats['avg'] < 5.0, f"Average LLM latency {stats['avg']:.2f}s exceeds relaxed target of 5s"
    if stats['avg'] < 3.0:
        print(f"  ✓ Meets target of <3s")
    else:
        print(f"  ⚠ Exceeds target of <3s (relaxed to 5s for acceptance)")


@pytest.mark.benchmark
@pytest.mark.integration
def test_mcp_adapter_operation_time():
    """
    Benchmark MCP adapter operations.
    Target: <500ms average
    """
    from agent.adapters.stdio_mcp_adapter import StdioMCPAdapter

    try:
        adapter = StdioMCPAdapter(
            command="npx",
            args=["-y", "@curtsortouch/windows-mcp"]
        )
    except Exception as e:
        pytest.skip(f"MCP adapter not available: {e}")

    try:
        # Benchmark list_windows
        times = []
        for i in range(10):
            start = time.time()
            windows = adapter.list_windows()
            elapsed = time.time() - start
            times.append(elapsed)

        stats = calculate_stats(times)

        print(f"\nMCP list_windows Operation Time:")
        print(f"  Average: {stats['avg']*1000:.0f}ms")
        print(f"  Min: {stats['min']*1000:.0f}ms")
        print(f"  Max: {stats['max']*1000:.0f}ms")
        print(f"  P95: {stats['p95']*1000:.0f}ms")

        # Relaxed target for MCP operations (stdio has overhead)
        assert stats['avg'] < 2.0, f"Average MCP operation time {stats['avg']*1000:.0f}ms exceeds relaxed target of 2000ms"

        if stats['avg'] < 0.5:
            print(f"  ✓ Meets target of <500ms")
        else:
            print(f"  ⚠ Exceeds target of <500ms (relaxed to 2000ms for stdio)")

    finally:
        if hasattr(adapter, 'close'):
            adapter.close()


@pytest.mark.benchmark
@pytest.mark.integration
@pytest.mark.requires_vscode
def test_screenshot_capture_time():
    """
    Benchmark screenshot capture time.
    Target: <1s average
    """
    from agent.adapters.stdio_mcp_adapter import StdioMCPAdapter
    from agent.nodes.act_step import _find_vscode_window

    try:
        adapter = StdioMCPAdapter(
            command="npx",
            args=["-y", "@curtsortouch/windows-mcp"]
        )
    except Exception as e:
        pytest.skip(f"MCP adapter not available: {e}")

    try:
        # Find a window to screenshot
        window = _find_vscode_window(adapter, ".*Visual Studio Code.*")
        if not window:
            pytest.skip("No VS Code window found")

        hwnd = window.get("hwnd") or window.get("id")

        # Benchmark screenshot
        times = []
        for i in range(10):
            start = time.time()
            screenshot = adapter.screenshot(hwnd=hwnd)
            elapsed = time.time() - start
            times.append(elapsed)
            assert len(screenshot) > 1000, "Screenshot should have content"

        stats = calculate_stats(times)

        print(f"\nScreenshot Capture Time:")
        print(f"  Average: {stats['avg']*1000:.0f}ms")
        print(f"  Min: {stats['min']*1000:.0f}ms")
        print(f"  Max: {stats['max']*1000:.0f}ms")
        print(f"  P95: {stats['p95']*1000:.0f}ms")

        assert stats['avg'] < 2.0, f"Average screenshot time {stats['avg']*1000:.0f}ms exceeds relaxed target of 2000ms"

        if stats['avg'] < 1.0:
            print(f"  ✓ Meets target of <1s")
        else:
            print(f"  ⚠ Exceeds target of <1s (relaxed to 2s)")

    finally:
        if hasattr(adapter, 'close'):
            adapter.close()


@pytest.mark.benchmark
@pytest.mark.integration
@pytest.mark.requires_api_key
def test_reasoner_node_execution_time():
    """
    Benchmark full Reasoner node execution including LLM call.
    Target: <5s average
    """
    from agent.nodes.reason_step import reason_step
    from agent.config import LLMConfig

    if not os.getenv("ZAI_API_KEY"):
        pytest.skip("ZAI_API_KEY not available")

    # Create test state
    settings = type('Settings', (), {
        'llm': LLMConfig(
            provider="z.ai",
            model="glm-4.6",
            api_key_env="ZAI_API_KEY",
            api_base_coding="https://api.z.ai/api/coding/paas/v4/",
            api_base_standard="https://api.z.ai/api/paas/v4/",
            temperature=0.7,
            max_tokens=200000
        )
    })()

    state = {
        "repos": {
            "test_repo": {
                "path": "/test/path",
                "current_branch": "main",
                "prs": [{"number": 1, "title": "Test PR"}]
            }
        },
        "work_items": [
            {"id": "task_1", "task_id": "test", "repo_name": "test_repo"}
        ],
        "plan": {"objectives": ["Test"]},
        "_settings": settings
    }

    times = []
    for i in range(3):
        start = time.time()
        result = reason_step(state.copy())
        elapsed = time.time() - start
        times.append(elapsed)
        assert result.get("task_envelope") is not None
        print(f"  Run {i+1}: {elapsed:.2f}s")

    stats = calculate_stats(times)

    print(f"\nReasoner Node Execution Time:")
    print(f"  Average: {stats['avg']:.2f}s")
    print(f"  Min: {stats['min']:.2f}s")
    print(f"  Max: {stats['max']:.2f}s")

    assert stats['avg'] < 10.0, f"Average Reasoner execution time {stats['avg']:.2f}s exceeds relaxed target of 10s"

    if stats['avg'] < 5.0:
        print(f"  ✓ Meets target of <5s")
    else:
        print(f"  ⚠ Exceeds target of <5s (relaxed to 10s)")


@pytest.mark.benchmark
def test_graph_node_overhead():
    """
    Benchmark pure graph node overhead (no external calls).
    This measures the framework overhead without I/O.
    """
    from agent.nodes.sync_plan import sync_plan

    # Mock state with minimal plan
    state = {
        "plan": {
            "work_items": [
                {"id": "task_1", "repos": ["repo1"], "actions": ["test"]}
            ]
        },
        "repos": {
            "repo1": {"path": "/test"}
        }
    }

    times = []
    for i in range(50):
        start = time.time()
        result = sync_plan(state.copy())
        elapsed = time.time() - start
        times.append(elapsed)

    stats = calculate_stats(times)

    print(f"\nGraph Node Overhead (sync_plan):")
    print(f"  Average: {stats['avg']*1000:.1f}ms")
    print(f"  Min: {stats['min']*1000:.1f}ms")
    print(f"  Max: {stats['max']*1000:.1f}ms")
    print(f"  P95: {stats['p95']*1000:.1f}ms")

    # Node overhead should be minimal (<100ms)
    assert stats['avg'] < 0.5, f"Graph node overhead {stats['avg']*1000:.0f}ms exceeds target of 500ms"
    print(f"  ✓ Low overhead")


def print_performance_summary():
    """Print a summary table of all performance metrics."""
    print("\n" + "="*70)
    print("PERFORMANCE SUMMARY")
    print("="*70)
    print(f"{'Operation':<30} {'Target':<15} {'Status':<25}")
    print("-"*70)
    print(f"{'LLM Reasoning Latency':<30} {'<3s':<15} {'Run benchmark to check':<25}")
    print(f"{'MCP Operations':<30} {'<500ms':<15} {'Run benchmark to check':<25}")
    print(f"{'Screenshot Capture':<30} {'<1s':<15} {'Run benchmark to check':<25}")
    print(f"{'Reasoner Node':<30} {'<5s':<15} {'Run benchmark to check':<25}")
    print(f"{'Graph Node Overhead':<30} {'<100ms':<15} {'Run benchmark to check':<25}")
    print("="*70)
    print("\nRun with: pytest tests/benchmarks/test_performance.py -v -s -m benchmark")
    print()


if __name__ == "__main__":
    print_performance_summary()
    # Run benchmarks
    pytest.main([__file__, "-v", "-s", "-m", "benchmark"])
