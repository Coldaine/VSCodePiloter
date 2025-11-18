# Testing Guide

This guide covers all testing procedures for VSCodePiloter, including unit tests, integration tests, acceptance tests, and performance benchmarks.

## Table of Contents

- [Testing Philosophy](#testing-philosophy)
- [Test Types](#test-types)
- [Running Tests](#running-tests)
- [Test Structure](#test-structure)
- [Writing Tests](#writing-tests)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)

---

## Testing Philosophy

**CRITICAL PROJECT REQUIREMENT**:

> **NO MOCKS for acceptance testing.**

This project explicitly prohibits mocked components for acceptance/integration tests:

- ❌ NO mocked VS Code windows
- ❌ NO mocked LLM responses
- ❌ NO mocked git repositories
- ❌ NO mocked API calls for acceptance tests

- ✅ YES real VS Code instances
- ✅ YES real Z.ai API calls
- ✅ YES real git repositories
- ✅ YES real MCP server or fallback adapter

**Exception**: Unit tests MAY use mocks to isolate individual functions, but integration and acceptance tests MUST use real components.

---

## Test Types

### 1. Unit Tests

**Location**: `tests/test_*.py`

**Purpose**: Test individual functions and modules in isolation.

**Mocking**: Allowed and encouraged for unit tests.

**Examples**:
- `tests/test_llm_client.py` - LLM client initialization
- `tests/test_secret_providers.py` - Secret provider functionality
- `tests/test_vscode_monitor.py` - VS Code monitoring logic

**Run with**:
```bash
pytest tests/ -v
```

### 2. Integration Tests

**Location**: `tests/integration/test_*.py`

**Purpose**: Test interactions between components with real dependencies.

**Mocking**: NOT ALLOWED (per project requirements).

**Markers**: `@pytest.mark.integration`

**Examples**:
- `tests/integration/test_reasoner_with_llm.py` - Reasoner with real Z.ai API
- `tests/integration/test_vscode_integration.py` - VS Code automation with real MCP

**Requirements**:
- Z.ai API key (`ZAI_API_KEY` environment variable)
- VS Code running (for VS Code tests)
- Windows-MCP available via npx

**Run with**:
```bash
pytest tests/integration/ -v -s -m integration
```

### 3. Performance Benchmarks

**Location**: `tests/benchmarks/test_performance.py`

**Purpose**: Measure and validate performance of critical operations.

**Markers**: `@pytest.mark.benchmark`

**Metrics**:
- LLM reasoning latency: <3s target
- MCP operations: <500ms target
- Screenshot capture: <1s target
- Reasoner node execution: <5s target
- Graph node overhead: <100ms target

**Run with**:
```bash
pytest tests/benchmarks/ -v -s -m benchmark
```

---

## Running Tests

### Quick Start

```bash
# Run all unit tests
pytest tests/ -v

# Run all integration tests (requires API key and VS Code)
pytest tests/integration/ -v -s -m integration

# Run specific test file
pytest tests/test_llm_client.py -v

# Run with coverage
pytest --cov=agent --cov-report=html tests/
```

### Test Markers

Tests are marked with pytest markers for conditional execution:

```bash
# Run only integration tests
pytest -m integration

# Run only tests requiring API key
pytest -m requires_api_key

# Run only tests requiring VS Code
pytest -m requires_vscode

# Run benchmarks
pytest -m benchmark

# Skip integration tests
pytest -m "not integration"
```

### Environment Setup

#### Required for Unit Tests
```bash
# Install dependencies
pip install -e .
pip install pytest pytest-cov
```

#### Required for Integration Tests
```bash
# 1. Set Z.ai API key
export ZAI_API_KEY="your_api_key_here"

# Or retrieve from Bitwarden
export ZAI_API_KEY=$(bws secret get Z_AI_API_KEY | jq -r '.value')

# 2. Install Windows-MCP (if testing VS Code automation)
npx -y @curtsortouch/windows-mcp

# 3. Ensure VS Code is running (for VS Code tests)
```

#### Optional: Skip Tests Without Dependencies
Tests automatically skip if dependencies are unavailable:

```python
if not os.getenv("ZAI_API_KEY"):
    pytest.skip("ZAI_API_KEY not available")
```

---

## Test Structure

### Directory Layout

```
tests/
├── __init__.py
├── test_llm_client.py           # Unit tests for LLM client
├── test_secret_providers.py     # Unit tests for secrets
├── test_vscode_monitor.py       # Unit tests for monitoring
├── test_sanity.py               # Basic sanity checks
├── fixtures/
│   └── mock_repos.json          # Mock repository data
├── integration/
│   ├── __init__.py
│   ├── conftest.py              # Integration test fixtures
│   ├── test_reasoner_with_llm.py    # Reasoner integration tests
│   └── test_vscode_integration.py   # VS Code integration tests
└── benchmarks/
    ├── __init__.py
    └── test_performance.py      # Performance benchmarks
```

### Fixtures (`tests/integration/conftest.py`)

Common fixtures for integration tests:

```python
@pytest.fixture
def mock_repos():
    """Load mock repository data"""

@pytest.fixture
def mock_work_items():
    """Create mock work items"""

@pytest.fixture
def test_llm_config():
    """Create test LLM configuration"""

@pytest.fixture
def has_api_key():
    """Check if API key is available"""
```

---

## Writing Tests

### Unit Test Example

```python
import pytest
from agent.llm_client import create_llm_client
from agent.config import LLMConfig

def test_create_llm_client_success():
    """Test LLM client creation with valid config."""
    config = LLMConfig(
        provider="z.ai",
        model="glm-4.6",
        api_key_env="TEST_KEY",
        api_base_coding="https://api.z.ai/api/coding/paas/v4/",
        temperature=0.7,
        max_tokens=200000
    )

    # Use mock for unit test
    with patch.dict(os.environ, {"TEST_KEY": "fake_key"}):
        llm = create_llm_client(config)
        assert llm is not None
        assert llm.model_name == "glm-4.6"
```

### Integration Test Example

```python
@pytest.mark.integration
@pytest.mark.requires_api_key
def test_reasoner_with_real_llm(test_settings, has_api_key):
    """Test Reasoner with REAL Z.ai API (NO MOCKS)."""
    if not has_api_key:
        pytest.skip("ZAI_API_KEY not available")

    # Use REAL components
    state = {
        "repos": {"test": {"path": "/test", "prs": []}},
        "work_items": [{"id": "1", "repo_name": "test"}],
        "_settings": test_settings
    }

    result = reason_step(state)

    # Validate REAL LLM response
    assert result.get("task_envelope") is not None
    assert "reasoning" in result["task_envelope"]["meta"]
```

### Performance Test Example

```python
@pytest.mark.benchmark
def test_llm_latency():
    """Benchmark LLM latency."""
    times = []
    for i in range(10):
        start = time.time()
        response = llm.invoke([message])
        times.append(time.time() - start)

    avg_time = statistics.mean(times)
    assert avg_time < 3.0, f"LLM latency {avg_time:.2f}s exceeds 3s target"
```

---

## CI/CD Integration

### GitHub Actions Configuration

```yaml
name: Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -e .
      - run: pytest tests/ -v -m "not integration"

  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install -e .
      - run: pytest tests/integration/ -v -m integration
        env:
          ZAI_API_KEY: ${{ secrets.ZAI_API_KEY }}
        continue-on-error: true  # Optional tests
```

### Pre-commit Hooks

```bash
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest-unit
        name: pytest-unit
        entry: pytest tests/ -m "not integration"
        language: system
        pass_filenames: false
        always_run: true
```

---

## Troubleshooting

### Common Issues

#### Issue: "ZAI_API_KEY not available"

**Solution**:
```bash
# Set API key from Bitwarden
export ZAI_API_KEY=$(bws secret get Z_AI_API_KEY | jq -r '.value')

# Or set directly
export ZAI_API_KEY="your_key_here"

# Verify
echo $ZAI_API_KEY
```

#### Issue: "MCP adapter not available"

**Solution**:
```bash
# Install Windows-MCP
npm install -g @curtsortouch/windows-mcp

# Or use npx (no install required)
npx -y @curtsortouch/windows-mcp
```

#### Issue: "No VS Code window found"

**Solution**:
- Ensure VS Code is running
- Check window title matches regex: `.*Visual Studio Code.*`
- Open at least one VS Code window

#### Issue: Tests are slow

**Solution**:
```bash
# Run only fast unit tests
pytest tests/ -m "not integration and not benchmark"

# Run integration tests in parallel (if pytest-xdist installed)
pytest tests/integration/ -n auto
```

#### Issue: LLM tests fail with 401 Unauthorized

**Solution**:
1. Verify API key is correct
2. Check Z.ai subscription is active ($3/month)
3. Test endpoint with curl:
```bash
curl -X POST https://api.z.ai/api/coding/paas/v4/chat/completions \
  -H "Authorization: Bearer $ZAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "glm-4.6", "messages": [{"role": "user", "content": "test"}]}'
```

#### Issue: Screenshot tests fail

**Solution**:
- Ensure VS Code window is visible (not minimized)
- Check MCP server has screen capture permissions
- Verify hwnd is valid

---

## Coverage Requirements

### Targets
- Unit tests: >80% code coverage
- Integration tests: Cover all critical paths
- Benchmarks: All major operations

### Generating Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=agent --cov-report=html tests/

# Open report
open htmlcov/index.html
```

### Checking Coverage

```bash
# Check coverage percentage
pytest --cov=agent --cov-report=term-missing tests/

# Fail if coverage below threshold
pytest --cov=agent --cov-fail-under=80 tests/
```

---

## Best Practices

### DO:
✅ Write integration tests for all critical user flows
✅ Use real components for acceptance tests
✅ Add pytest markers for conditional tests
✅ Document test requirements in docstrings
✅ Measure performance of critical operations
✅ Test error handling and edge cases

### DON'T:
❌ Mock external services in integration tests
❌ Skip test documentation
❌ Leave failing tests in the codebase
❌ Test implementation details (test behavior)
❌ Write tests that depend on execution order
❌ Hardcode secrets in test files

---

## Test Reporting

### Running Tests with Detailed Output

```bash
# Verbose output
pytest -v

# Show print statements
pytest -s

# Both verbose and stdout
pytest -v -s

# Detailed failure info
pytest --tb=long

# Show slowest tests
pytest --durations=10
```

### Generating Test Reports

```bash
# JUnit XML (for CI)
pytest --junitxml=test-results.xml

# HTML report
pytest --html=report.html --self-contained-html

# JSON report
pytest --json-report --json-report-file=report.json
```

---

## Continuous Improvement

### Adding New Tests

1. Identify the component/feature to test
2. Choose appropriate test type (unit/integration/benchmark)
3. Add test file in correct location
4. Use appropriate markers
5. Document requirements and expectations
6. Run test locally
7. Update this guide if needed

### Maintaining Tests

- Review test failures immediately
- Update tests when behavior changes
- Remove obsolete tests
- Refactor brittle tests
- Keep fixtures DRY (Don't Repeat Yourself)

---

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest markers](https://docs.pytest.org/en/stable/how-to/mark.html)
- [pytest fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html)
- [Project CLAUDE.md](../CLAUDE.md) - Sprint workflow
- [ARCHITECTURE.md](../ARCHITECTURE.md) - System design

---

**Last Updated**: 2025-11-18
**Maintained By**: VSCodePiloter team
