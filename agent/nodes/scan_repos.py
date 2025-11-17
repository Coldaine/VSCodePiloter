
from __future__ import annotations
import os, time
from typing import Dict, Any
from agent.tools.git_ops import get_branches, get_default_branch
from agent.tools.gh_ops import list_prs
from agent.observability import span

def scan_repos(state: Dict[str, Any]) -> Dict[str, Any]:
    repos_root = state.get("repos_root")
    repos = {}
    with span("ScanRepos"):
        if not repos_root or not os.path.isdir(repos_root):
            return {**state, "repos": {}, "scan_error": f"Invalid repos_root: {repos_root}"}
        for name in os.listdir(repos_root):
            path = os.path.join(repos_root, name)
            if not os.path.isdir(path):
                continue
            # Heuristic: treat as repo if .git exists
            if not os.path.isdir(os.path.join(path, ".git")):
                continue
            branches = get_branches(path)
            default_branch = get_default_branch(path) or "main"
            prs = list_prs(path)
            repos[name] = {
                "path": path,
                "default_branch": default_branch,
                "branches": branches,
                "open_prs": len([p for p in prs if p.get("state") == "OPEN"]),
                "prs": prs,
                "last_scan": int(time.time())
            }
    return {**state, "repos": repos}
