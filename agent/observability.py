
from __future__ import annotations
import os, json, time, uuid
from contextlib import contextmanager
from typing import Dict, Any

EPISODES_DIR = "state/episodes"

def _episode_dir() -> str:
    ts = time.strftime("%Y%m%d")
    d = os.path.join(EPISODES_DIR, ts)
    os.makedirs(d, exist_ok=True)
    return d

def log_event(event: str, payload: Dict[str, Any] | None = None) -> None:
    entry = {
        "ts": int(time.time()),
        "event": event,
        "payload": payload or {}
    }
    path = os.path.join(_episode_dir(), "events.jsonl")
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

@contextmanager
def span(name: str, attrs: Dict[str, Any] | None = None):
    sid = str(uuid.uuid4())
    start = time.time()
    log_event("span.start", {"id": sid, "name": name, "attrs": attrs or {}})
    try:
        yield sid
        dur = time.time() - start
        log_event("span.end", {"id": sid, "name": name, "duration_s": dur})
    except Exception as e:
        dur = time.time() - start
        log_event("span.error", {"id": sid, "name": name, "duration_s": dur, "error": str(e)})
        raise
