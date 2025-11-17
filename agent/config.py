
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

class VisionConfig(BaseModel):
    enabled: bool = Field(True, description="Enable vision capabilities")
    max_image_size: int = Field(2048, description="Max image dimension before resizing")
    detail: str = Field("high", description="Vision detail level: low, high, auto")

class LLMConfig(BaseModel):
    provider: str = Field("z.ai", description="LLM provider: z.ai, openai, anthropic")
    model: str = Field("glm-4.6", description="Text model name for reasoning")
    vision_model: str = Field("glm-4.5v", description="Vision model name for screenshot analysis")
    api_key_env: str = Field("ZAI_API_KEY", description="Environment variable for API key")

    # Z.ai has separate endpoints for coding plan vs standard API
    api_base_coding: str = Field(
        "https://api.z.ai/api/coding/paas/v4/",
        description="Coding endpoint for GLM-4.6 (subscription-based)"
    )
    api_base_standard: str = Field(
        "https://api.z.ai/api/paas/v4/",
        description="Standard endpoint for GLM-4.5V vision model (pay-as-you-go)"
    )

    # Legacy field for backwards compatibility
    api_base: str = Field(
        default="",
        description="Deprecated: Use api_base_coding or api_base_standard instead"
    )

    temperature: float = Field(0.95, description="Temperature for sampling")
    max_tokens: int = Field(131072, description="Maximum context tokens")
    vision: VisionConfig = Field(default_factory=VisionConfig, description="Vision-specific settings")

    def __init__(self, **data):
        """Initialize with backwards compatibility for api_base field."""
        super().__init__(**data)
        # If api_base is provided but not the specific ones, use it for both
        if self.api_base and (not data.get("api_base_coding") or not data.get("api_base_standard")):
            if not data.get("api_base_coding"):
                self.api_base_coding = self.api_base
            if not data.get("api_base_standard"):
                self.api_base_standard = self.api_base

class Settings(BaseModel):
    repos_root: str
    write_mode: bool = False
    window_title_regex: str = ".*Visual Studio Code.*"
    checkpoint_db: str = "state/checkpoints/graph.sqlite"
    watchdog_interval_minutes: int = 30
    adapters: AdaptersConfig
    copilot: CopilotConfig
    llm: LLMConfig

def load_settings(path: str | os.PathLike = "config/config.yaml") -> Settings:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    # allow override via env vars if desired later
    return Settings(**data)
