
from __future__ import annotations
import os, yaml, pathlib
from pydantic import BaseModel, Field

class MCPConfig(BaseModel):
    base_url: str
    jsonrpc: bool = False
    endpoints: dict

class AdaptersConfig(BaseModel):
    type: str = Field("mcp", description="mcp or fallback")
    mcp: MCPConfig | None = None

class CopilotConfig(BaseModel):
    command_palette_action: str = "GitHub Copilot Chat: Focus on Chat View"
    busy_min_age_sec: int = 10

class Settings(BaseModel):
    repos_root: str
    write_mode: bool = False
    window_title_regex: str = ".*Visual Studio Code.*"
    checkpoint_db: str = "state/checkpoints/graph.sqlite"
    watchdog_interval_minutes: int = 30
    adapters: AdaptersConfig
    copilot: CopilotConfig

def load_settings(path: str | os.PathLike = "config/config.yaml") -> Settings:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    # allow override via env vars if desired later
    return Settings(**data)
