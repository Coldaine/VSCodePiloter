
def test_repo_layout():
    import os
    assert os.path.exists("plans/plan.yaml")
    assert os.path.exists("config/config.yaml")
    assert os.path.exists("agent/main.py")
