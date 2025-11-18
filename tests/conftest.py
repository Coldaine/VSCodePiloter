import os
import pytest

ACCEPTANCE_ENV = "RUN_ACCEPTANCE"
INTEGRATION_ENV = "RUN_INTEGRATION"


def pytest_collection_modifyitems(config, items):
    acceptance = pytest.mark.acceptance
    integration = pytest.mark.integration
    unit = pytest.mark.unit
    mcp = pytest.mark.mcp

    for item in items:
        nodeid = item.nodeid.replace("\\", "/").lower()

        # Heuristic labeling by path/name
        if "/acceptance/" in nodeid or "test_windows_mcp.py" in nodeid:
            item.add_marker(acceptance)
            item.add_marker(mcp)
        elif "/integration/" in nodeid:
            item.add_marker(integration)
        else:
            item.add_marker(unit)

    # Apply environment-gated skips
    run_acceptance = os.environ.get(ACCEPTANCE_ENV) == "1"
    run_integration = os.environ.get(INTEGRATION_ENV) == "1"

    skip_acceptance = pytest.mark.skip(reason=f"acceptance tests require {ACCEPTANCE_ENV}=1")
    skip_integration = pytest.mark.skip(reason=f"integration tests require {INTEGRATION_ENV}=1")

    for item in items:
        if item.get_closest_marker("acceptance") and not run_acceptance:
            item.add_marker(skip_acceptance)
        if item.get_closest_marker("integration") and not run_integration:
            item.add_marker(skip_integration)
