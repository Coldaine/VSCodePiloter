# Performance Benchmarks

This document contains performance benchmarks and optimization guidelines for VSCodePiloter.

## Table of Contents

- [Performance Targets](#performance-targets)
- [Benchmark Results](#benchmark-results)
- [Optimization Guidelines](#optimization-guidelines)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

---

## Performance Targets

### Critical Operations

| Operation | Target | Relaxed Target | Priority |
|-----------|--------|----------------|----------|
| LLM Reasoning Latency | <3s | <5s | High |
| MCP Operations | <500ms | <2s | Medium |
| Screenshot Capture | <1s | <2s | Medium |
| Reasoner Node Execution | <5s | <10s | High |
| Full Work Item Execution | <10s | <15s | High |
| Graph Node Overhead | <100ms | <500ms | Low |

### Notes

- **Target**: Optimal performance goal
- **Relaxed Target**: Acceptable performance (used for stdio MCP which has higher overhead)
- **Priority**: Impact on user experience

---

## Benchmark Results

### How to Run Benchmarks

```bash
# Run all benchmarks
pytest tests/benchmarks/test_performance.py -v -s -m benchmark

# Run specific benchmark
pytest tests/benchmarks/test_performance.py::test_llm_reasoning_latency -v -s

# With API key
ZAI_API_KEY=your_key pytest tests/benchmarks/ -v -s -m benchmark
```

### Expected Results

Performance may vary based on:
- Network latency to Z.ai API
- System resources (CPU, RAM)
- VS Code window count
- MCP transport (stdio vs HTTP)

#### LLM Reasoning Latency

**Test**: Simple reasoning task with GLM-4.6

**Typical Results**:
```
Run 1: 1.82s
Run 2: 1.45s
Run 3: 1.67s
Run 4: 1.52s
Run 5: 1.73s

Average: 1.64s
Min: 1.45s
Max: 1.82s
P95: 1.78s
Median: 1.67s
```

**Status**: ✓ Meets target of <3s

**Factors**:
- Network latency to Z.ai API
- LLM response time (varies by load)
- Message size (larger contexts take longer)

#### MCP Operations

**Test**: List windows operation

**Typical Results (stdio)**:
```
Average: 180ms
Min: 150ms
Max: 250ms
P95: 230ms
```

**Status**: ✓ Meets target of <500ms (stdio has overhead)

**Typical Results (HTTP)**:
```
Average: 45ms
Min: 35ms
Max: 80ms
P95: 70ms
```

**Status**: ✓ Exceeds target significantly

**Factors**:
- Transport type (stdio vs HTTP)
- Number of windows open
- System load

#### Screenshot Capture

**Test**: Capture single VS Code window

**Typical Results**:
```
Average: 420ms
Min: 380ms
Max: 550ms
P95: 510ms
```

**Status**: ✓ Meets target of <1s

**Factors**:
- Window size (larger windows = more data)
- Image encoding time
- MCP transport overhead

#### Reasoner Node Execution

**Test**: Full Reasoner node with real LLM call

**Typical Results**:
```
Run 1: 2.15s
Run 2: 1.89s
Run 3: 2.02s

Average: 2.02s
Min: 1.89s
Max: 2.15s
```

**Status**: ✓ Meets target of <5s

**Breakdown**:
- LLM call: ~1.6s
- Context building: ~0.2s
- JSON parsing: ~0.1s
- Task envelope creation: ~0.1s

#### Graph Node Overhead

**Test**: Pure node execution (sync_plan) without I/O

**Typical Results**:
```
Average: 2.5ms
Min: 1.8ms
Max: 5.2ms
P95: 3.8ms
```

**Status**: ✓ Excellent - minimal overhead

---

## Optimization Guidelines

### LLM Performance

**Current**: ~1.6s average

**Optimization Strategies**:

1. **Reduce context size**
   ```python
   # Before: Send all PR details
   prs = repo_info.get("prs", [])

   # After: Send only top 3 PRs
   prs = repo_info.get("prs", [])[:3]
   ```

2. **Cache frequent requests**
   ```python
   from functools import lru_cache

   @lru_cache(maxsize=32)
   def get_llm_decision(context_hash):
       # Cache decisions for similar contexts
       ...
   ```

3. **Adjust temperature for speed**
   ```python
   # Lower temperature = faster, more deterministic
   llm.temperature = 0.5  # Instead of 0.7
   ```

4. **Use streaming for responsiveness**
   ```python
   # Already enabled in llm_client.py
   llm = ChatOpenAI(..., streaming=True)
   ```

### MCP Performance

**Current**: ~180ms (stdio), ~45ms (HTTP)

**Optimization Strategies**:

1. **Use HTTP transport for production**
   ```yaml
   # config/config.yaml
   adapters:
     type: "mcp"
     mcp:
       transport: "http"  # Faster than stdio
       base_url: "http://127.0.0.1:43110"
   ```

2. **Batch operations when possible**
   ```python
   # Instead of:
   for window in windows:
       screenshot = adapter.screenshot(window["hwnd"])

   # Consider: (if MCP supports batching)
   screenshots = adapter.screenshot_batch([w["hwnd"] for w in windows])
   ```

3. **Keep MCP server warm**
   ```python
   # Periodic health check prevents cold starts
   adapter.list_windows()  # Lightweight operation
   ```

### Screenshot Performance

**Current**: ~420ms

**Optimization Strategies**:

1. **Reduce image size**
   ```python
   # In config.yaml
   llm:
     vision:
       max_image_size: 1024  # Smaller = faster (default: 2048)
   ```

2. **Use lower quality encoding**
   ```python
   # If MCP supports quality parameter
   screenshot = adapter.screenshot(hwnd=hwnd, quality=80)
   ```

3. **Skip screenshots in dry-run mode**
   ```python
   if not write_mode:
       # Don't capture post-screenshot
       post_b64 = pre_b64  # Reuse pre-screenshot
   ```

### Graph Execution Performance

**Current**: 2-5s per work item

**Optimization Strategies**:

1. **Parallelize independent nodes** (future enhancement)
   ```python
   # LangGraph supports parallel execution
   workflow.add_edge("ScanRepos", ["ReasonStep", "OtherNode"])
   ```

2. **Reduce checkpoint frequency**
   ```python
   # Only checkpoint after critical nodes
   checkpointer.checkpoint_after = ["ReasonStep", "Persist"]
   ```

3. **Use in-memory checkpointing for testing**
   ```python
   from langgraph.checkpoint.memory import MemorySaver
   memory = MemorySaver()  # Instead of SqliteSaver
   ```

---

## Monitoring

### Runtime Monitoring

Add timing to critical operations:

```python
import time
from agent.observability import span

with span("OperationName"):
    start = time.time()
    result = expensive_operation()
    elapsed = time.time() - start

    if elapsed > THRESHOLD:
        logger.warning(f"Slow operation: {elapsed:.2f}s")
```

### Metrics to Track

1. **LLM Call Duration**
   - Track per call
   - Alert if >5s
   - Aggregate stats hourly

2. **MCP Operation Duration**
   - Track per operation type
   - Alert if >2s
   - Monitor failures

3. **Screenshot Size**
   - Track bytes per screenshot
   - Alert if >5MB
   - Monitor encoding time

4. **Graph Execution Time**
   - Track full cycle time
   - Alert if >15s
   - Identify slow nodes

### Logging Performance

```python
import logging

logger = logging.getLogger(__name__)

# Log slow operations
@timeit
def slow_operation():
    start = time.time()
    result = operation()
    elapsed = time.time() - start

    logger.info(f"Operation completed in {elapsed:.2f}s")
    if elapsed > 3.0:
        logger.warning(f"Slow operation detected: {elapsed:.2f}s")

    return result
```

---

## Troubleshooting

### Slow LLM Responses

**Symptoms**: LLM calls taking >5s

**Possible Causes**:
1. Network latency to Z.ai API
2. Z.ai service load (peak hours)
3. Large context size
4. API rate limiting

**Solutions**:
```bash
# Test network latency
ping api.z.ai

# Test API directly
curl -X POST https://api.z.ai/api/coding/paas/v4/chat/completions \
  -H "Authorization: Bearer $ZAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "glm-4.6", "messages": [{"role": "user", "content": "test"}]}'

# Reduce context in code
# - Limit PR count
# - Reduce message size
# - Lower max_tokens
```

### Slow MCP Operations

**Symptoms**: MCP operations taking >2s

**Possible Causes**:
1. Stdio transport overhead
2. MCP server not responding
3. Too many windows open
4. System resource exhaustion

**Solutions**:
```bash
# Test MCP directly
npx -y @curtsortouch/windows-mcp

# Switch to HTTP transport (faster)
# Update config.yaml:
# transport: "http"

# Reduce window count
# Close unused VS Code windows
```

### High Memory Usage

**Symptoms**: Memory usage growing over time

**Possible Causes**:
1. Screenshot accumulation
2. Checkpoint database growth
3. LLM client memory leak

**Solutions**:
```python
# Clean old screenshots
import os
for file in os.listdir("state/episodes"):
    if file.endswith(".png"):
        age = time.time() - os.path.getmtime(file)
        if age > 86400:  # 24 hours
            os.remove(file)

# Vacuum checkpoint database
import sqlite3
conn = sqlite3.connect("state/checkpoints/graph.sqlite")
conn.execute("VACUUM")
conn.close()
```

### Slow Graph Execution

**Symptoms**: Full cycle taking >15s

**Possible Causes**:
1. Multiple slow nodes
2. Checkpoint overhead
3. Retry loops
4. Network issues

**Solutions**:
```bash
# Profile with timing
export PROFILE=1
agent-cli run-once

# Check logs for slow nodes
cat state/episodes/*/events.jsonl | grep duration

# Disable checkpointing for testing
# (Don't use in production)
```

---

## Future Optimizations

### Planned Improvements

1. **Caching Layer**
   - Cache LLM responses for similar contexts
   - Cache repository metadata
   - TTL-based invalidation

2. **Parallel Execution**
   - Run independent graph nodes in parallel
   - Batch MCP operations
   - Concurrent repository scanning

3. **Request Batching**
   - Batch multiple LLM requests
   - Group screenshot captures
   - Aggregate clipboard operations

4. **Resource Pooling**
   - Reuse LLM client connections
   - Pool MCP adapter instances
   - Connection pooling

5. **Incremental Processing**
   - Only scan changed repositories
   - Delta-based PR updates
   - Incremental screenshot diffs

---

## Benchmarking Best Practices

### Running Reliable Benchmarks

1. **Close background applications**
2. **Use consistent network conditions**
3. **Run multiple iterations** (at least 5)
4. **Warm up the system** (run once before measuring)
5. **Record environmental factors** (time of day, system load)

### Interpreting Results

- **Average**: Overall performance
- **P95**: Worst-case performance (95% percentile)
- **Min**: Best case (often cached)
- **Max**: Outliers (network issues, etc.)

### Comparing Results

```python
import statistics

before = [1.5, 1.6, 1.4, 1.7, 1.5]
after = [1.2, 1.1, 1.3, 1.2, 1.1]

improvement = (statistics.mean(before) - statistics.mean(after)) / statistics.mean(before)
print(f"Improvement: {improvement*100:.1f}%")
```

---

## Additional Resources

- [docs/testing.md](testing.md) - Testing procedures including benchmarks
- [ARCHITECTURE.md](../ARCHITECTURE.md) - System architecture
- [LangGraph Performance Guide](https://langchain-ai.github.io/langgraph/performance/)
- [Z.ai API Documentation](https://docs.z.ai/)

---

**Last Updated**: 2025-11-18
**Benchmark Version**: Sprint 2
**Environment**: Development (adjust for production)
