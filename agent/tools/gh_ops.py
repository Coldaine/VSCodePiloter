
from __future__ import annotations
import json, subprocess
from typing import List, Dict, Any, Tuple

def run_gh(args: List[str], cwd: str | None = None, timeout: int = 60) -> Tuple[int, str, str]:
    p = subprocess.Popen(["gh"] + args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=False)
    try:
        out, err = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        p.kill()
        out, err = p.communicate()
    return p.returncode, out, err

def list_prs(repo_path: str) -> List[Dict[str, Any]]:
    code, out, err = run_gh(["pr", "list", "--json", "title,number,state,createdAt,updatedAt,labels"], cwd=repo_path, timeout=120)
    if code != 0:
        return []
    try:
        return json.loads(out)
    except Exception:
        return []

def pr_summary(prs: List[Dict[str, Any]]) -> str:
    lines = []
    for pr in prs:
        labels = ",".join([l.get("name","") for l in pr.get("labels", [])])
        lines.append(f"PR #{pr['number']} [{pr['state']}] - {pr['title']} (labels: {labels})")
    return "\n".join(lines)
