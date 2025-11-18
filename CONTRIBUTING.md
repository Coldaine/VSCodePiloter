# Contributing to VSCodePiloter

Thank you for your interest in contributing to VSCodePiloter! This guide will help you understand our development workflow and contribution requirements.

## Table of Contents

- [Sprint-Based Workflow](#sprint-based-workflow)
- [Getting Started](#getting-started)
- [Development Process](#development-process)
- [Code Standards](#code-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Guidelines](#pull-request-guidelines)
- [Communication](#communication)

---

## Sprint-Based Workflow

**CRITICAL**: VSCodePiloter uses a **sprint-based relay system** where Claude Code instances collaborate via sprint plans.

### The Relay Race Metaphor

Think of development as a relay race:
- **The baton**: Sprint plan (e.g., `docs/plans/Sprint2.md`)
- **Your job**:
  1. Pick up where the last developer left off
  2. Complete your portion of work
  3. Pass the baton cleanly to the next developer

### Before You Start ANY Work

1. ✅ **Read CLAUDE.md** - Comprehensive project instructions
2. ✅ **Read current sprint plan** - Check `docs/plans/Sprint1.md` or `Sprint2.md`
3. ✅ **Review recent commits** - Understand context with `git log --oneline -10`
4. ✅ **Check uncompleted tasks** - Look for `[ ]` checkboxes in sprint plan
5. ✅ **Understand priorities** - BLOCKER > IMMEDIATE > HIGH > MEDIUM > LOW

**DO NOT skip these steps.** Future contributors depend on you following this workflow.

### Sprint Workflow

```bash
# 1. Context gathering (5 minutes)
cat docs/plans/Sprint2.md
git log --oneline -10
git status
grep "\[ \]" docs/plans/Sprint2.md

# 2. Select task (2 minutes)
# - Choose BLOCKER tasks first
# - Then IMMEDIATE tasks
# - Then HIGH PRIORITY tasks
# Ask maintainers if unclear

# 3. Execute task (variable time)
# - Follow task steps in sprint plan
# - Test as you go
# - Commit frequently
# - Log issues

# 4. Update sprint plan (MANDATORY - 2 minutes)
# - Change [ ] to [x] for completed tasks
# - Add notes about issues discovered
# - Save the file

# 5. Commit progress (1 minute)
git add .
git commit -m "Complete Task X.Y: Brief description

- Specific change 1
- Specific change 2
- Updated Sprint2.md task checklist"

# 6. Report (1 minute)
# - What you completed
# - What you tested
# - What you updated
# - Any blockers
# - What's next
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Windows 11 (for full testing)
- VS Code with GitHub Copilot
- Git with `gh` CLI
- Z.ai API key (for integration tests)
- Node.js (for Windows-MCP)

### Development Setup

1. **Clone and Setup**
```bash
git clone https://github.com/your-org/VSCodePiloter.git
cd VSCodePiloter

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install dependencies
pip install -e .
pip install -e .[dev]      # Development dependencies
pip install -e .[fallback] # Fallback adapter (optional)
```

2. **Configure Environment**
```bash
# Set Z.ai API key (required for integration tests)
export ZAI_API_KEY="your-api-key"

# Or use Bitwarden
export BWS_ACCESS_TOKEN="your-bws-token"
source ./scripts/get_api_key.sh
```

3. **Verify Setup**
```bash
# Run unit tests
pytest tests/ -v

# Verify MCP
npx -y @curtsortouch/windows-mcp

# Scan repos
agent-cli scan
```

---

## Development Process

### 1. Create a Branch

```bash
# Branch naming convention
git checkout -b feature/task-description   # For features
git checkout -b fix/bug-description        # For bug fixes
git checkout -b docs/documentation-update  # For documentation
git checkout -b test/test-improvements     # For testing
```

### 2. Make Changes

- Follow task steps in sprint plan exactly
- Test each change before moving to next task
- Commit frequently with clear messages
- Update documentation as you go

### 3. Update Sprint Plan

**MANDATORY**: Update the sprint plan after each completed task:

```markdown
Before:
- [ ] Create integration tests for Reasoner

After:
- [x] Create integration tests for Reasoner
  - **Note**: Created 7 tests in test_reasoner_with_llm.py
  - **Issue**: None
  - **Tested**: All tests pass with real API key
```

### 4. Run Tests

```bash
# Before committing, run appropriate tests
pytest tests/ -v                    # Unit tests (always)
pytest tests/integration/ -v -m integration  # Integration tests (if relevant)
pytest --cov=agent tests/           # Coverage check
```

### 5. Commit and Push

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: Add Reasoner integration tests

- Created test_reasoner_with_llm.py with 7 tests
- Tests validate real LLM reasoning
- Updated Sprint2.md with task completion
- All tests pass with real API key"

# Push to your branch
git push origin your-branch-name
```

---

## Code Standards

### Python Style

- Follow PEP 8
- Use type hints where possible
- Maximum line length: 100 characters
- Use meaningful variable names

```python
# Good
def create_reasoner_llm(config: LLMConfig) -> ChatOpenAI:
    """Create an LLM for Reasoner agent."""
    ...

# Bad
def create_llm(c):
    ...
```

### Documentation

- Docstrings for all public functions
- Comments for complex logic
- Update relevant `.md` files when behavior changes

```python
def reason_step(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reasoner node: Use LLM to intelligently select next work item.

    This replaces naive round-robin with GLM-4.6 powered reasoning
    that considers repo health, PR status, and plan priorities.

    Args:
        state: Current agent state containing repos, work_items, plan

    Returns:
        Updated state with task_envelope set
    """
```

### Error Handling

- Handle exceptions gracefully
- Provide clear error messages
- Log errors appropriately

```python
try:
    llm = create_reasoner_llm(config)
except Exception as e:
    logger.error(f"Failed to create LLM: {e}")
    state["task_envelope"] = None
    return state
```

---

## Testing Requirements

### Critical Rule: NO MOCKS for Acceptance Testing

**From project requirements:**

> Can you go ahead and make sure we write in our architecture that no mocks or live tests are suitable for acceptance testing?

This means:

✅ **Unit tests MAY use mocks**
```python
@patch('agent.llm_client.ChatOpenAI')
def test_create_llm_client(mock_openai):
    # Unit test with mock is OK
    ...
```

❌ **Integration/acceptance tests MUST use real components**
```python
@pytest.mark.integration
@pytest.mark.requires_api_key
def test_reasoner_with_real_llm(test_settings, has_api_key):
    # Must use REAL LLM, no mocks
    if not has_api_key:
        pytest.skip("API key not available")

    result = reason_step(state)  # Real LLM call
    assert result["task_envelope"] is not None
```

### Test Requirements

1. **All new features require tests**
   - Unit tests for individual functions
   - Integration tests for end-to-end flows

2. **Tests must pass before PR**
   ```bash
   pytest tests/ -v
   ```

3. **Coverage targets**
   - Maintain >70% code coverage
   - Critical paths must have 100% coverage

4. **Integration test markers**
   ```python
   @pytest.mark.integration          # Requires real dependencies
   @pytest.mark.requires_api_key     # Requires Z.ai API key
   @pytest.mark.requires_vscode      # Requires VS Code running
   @pytest.mark.benchmark            # Performance benchmark
   ```

5. **Tests should be self-documenting**
   ```python
   def test_reasoner_selects_high_priority_repo():
       """
       Test that Reasoner selects high-priority repo (with 3 open PRs)
       over others >80% of the time.
       """
   ```

See [docs/testing.md](docs/testing.md) for comprehensive testing guide.

---

## Pull Request Guidelines

### PR Checklist

Before submitting a PR, ensure:

- [ ] All tasks in sprint plan are checked off
- [ ] Sprint plan updated with completion notes
- [ ] All tests pass (`pytest tests/ -v`)
- [ ] Code coverage maintained or improved
- [ ] Documentation updated (if applicable)
- [ ] Commit messages are clear and descriptive
- [ ] No hardcoded secrets or API keys
- [ ] `CLAUDE.md` followed (if working with Claude Code)

### PR Template

```markdown
## Description
Brief description of changes made.

## Sprint Task
Completes Task X.Y in Sprint2.md: [Task Name]

## Changes Made
- Change 1
- Change 2
- Change 3

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass (if applicable)
- [ ] Manual testing completed

## Sprint Plan Updates
- [x] Updated Sprint2.md with task completion
- [x] Added notes about issues discovered (if any)

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Sprint plan updated
- [ ] No secrets in code
```

### PR Review Process

1. **Submit PR** against `main` branch
2. **Automated checks** run (tests, linting)
3. **Code review** by maintainer
4. **Address feedback** if requested
5. **Merge** after approval

---

## Communication

### Asking Questions

- **GitHub Issues**: For bugs, feature requests, discussions
- **PR Comments**: For code-specific questions
- **Sprint Plan**: Document blockers and issues

### Reporting Issues

Use GitHub Issues with this template:

```markdown
## Description
Clear description of the issue

## Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: Windows 11
- Python: 3.11
- VSCodePiloter version: vX.Y.Z

## Sprint Context
Related to Sprint2.md Task X.Y (if applicable)
```

### Blockers

If you encounter a blocker:

1. **Document it in sprint plan**:
   ```markdown
   - [ ] Task X: Description
     - **BLOCKER**: Cannot proceed because...
   ```

2. **Create GitHub issue** with `blocker` label

3. **Notify maintainers** in PR or issue

---

## Best Practices

### DO:
✅ Read sprint plan before starting work
✅ Update sprint plan as you complete tasks
✅ Write tests for all new code
✅ Use real components in integration tests
✅ Commit frequently with clear messages
✅ Document as you go
✅ Ask questions when blocked

### DON'T:
❌ Skip reading sprint plan
❌ Leave sprint plan unchecked
❌ Mock external services in integration tests
❌ Commit without running tests
❌ Hardcode secrets
❌ Make large PRs (>500 lines)
❌ Work on multiple tasks simultaneously

---

## Code Review Guidelines

### As a Reviewer

- **Be constructive**: Suggest improvements, don't just criticize
- **Check sprint plan**: Verify task was completed correctly
- **Run tests**: Ensure tests pass locally
- **Review documentation**: Check docs are updated
- **Verify no secrets**: Ensure no API keys committed

### As a Contributor

- **Respond promptly**: Address feedback within 48 hours
- **Ask for clarification**: If feedback is unclear, ask
- **Don't take it personally**: Code review improves code quality
- **Update sprint plan**: If changes affect other tasks

---

## License

By contributing to VSCodePiloter, you agree that your contributions will be licensed under the same license as the project.

---

## Additional Resources

- [CLAUDE.md](CLAUDE.md) - Claude Code workflow instructions
- [docs/plans/Sprint2.md](docs/plans/Sprint2.md) - Current sprint plan
- [docs/testing.md](docs/testing.md) - Comprehensive testing guide
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [SETUP.md](SETUP.md) - Setup instructions

---

**Thank you for contributing to VSCodePiloter!** 🚀

Your contributions help make this project better for everyone. If you have questions, don't hesitate to ask.
