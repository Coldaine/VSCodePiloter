
from __future__ import annotations
import time, os, json, subprocess
from agent.config import load_settings
from agent.state_store import read_world_state
from agent.observability import log_event

def main():
    settings = load_settings()
    interval = int(settings.watchdog_interval_minutes) * 60
    while True:
        try:
            ws = read_world_state()
            last = ws.get("last_heartbeat") or 0
            now = int(time.time())
            if now - last > interval:
                log_event("watchdog.resume", {"since_s": now - last})
                subprocess.run(["agent-cli", "run-once"], check=False)
            else:
                log_event("watchdog.ok", {"age_s": now - last})
        except Exception as e:
            log_event("watchdog.error", {"error": str(e)})
        time.sleep(interval)

if __name__ == "__main__":
    main()
