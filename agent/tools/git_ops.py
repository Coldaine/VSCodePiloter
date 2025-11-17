
from __future__ import annotations
import subprocess, os
from typing import List, Tuple

def run(cmd: List[str], cwd: str | None = None, timeout: int = 60) -> Tuple[int, str, str]:
    p = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=False)
    try:
        out, err = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        p.kill()
        out, err = p.communicate()
    return p.returncode, out, err

def get_branches(repo_path: str) -> List[str]:
    code, out, _ = run(["git", "branch", "--list"], cwd=repo_path)
    if code != 0:
        return []
    return [line.strip().lstrip("* ").strip() for line in out.splitlines() if line.strip()]

def get_default_branch(repo_path: str) -> str | None:
    code, out, _ = run(["git", "symbolic-ref", "refs/remotes/origin/HEAD"], cwd=repo_path)
    if code != 0 or "refs/remotes/origin/" not in out:
        return None
    return out.strip().split("/")[-1]

def list_remotes(repo_path: str) -> List[str]:
    code, out, _ = run(["git", "remote", "-v"], cwd=repo_path)
    if code != 0:
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]
