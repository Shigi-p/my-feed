"""Load ``config.toml`` (C0 minimal settings + optional scoring knobs)."""

from __future__ import annotations

import os
import tomllib
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from my_feed.models import SourceName

# Load .env file from current directory or parent directories
load_dotenv()

DEFAULT_CONFIG_PATH = Path("config.toml")
LOCAL_CONFIG_PATH = Path("config.local.toml")


class HybridScoringConfig(BaseModel):
    """Parameters for the hybrid (and related) scorers."""

    recency_half_life_hours: float = 36.0
    neutral_popularity_when_missing: float = 0.5


class ScoringConfig(BaseModel):
    """Optional scoring section; deep tuning is M3."""

    hybrid: HybridScoringConfig = Field(default_factory=HybridScoringConfig)


class SummarizerConfig(BaseModel):
    """AI summarization settings (M4-D).
    
    Technical parameters (temperature, max_output_tokens, thinking_level) are
    hardcoded in the implementation. Users only need to toggle enabled and
    optionally choose a different model.
    """

    enabled: bool = False
    model: str = "gemini-3.5-flash-lite"
    api_key_env: str = "GEMINI_API_KEY"

    def get_api_key(self) -> str | None:
        """Read API key from environment variable."""
        return os.getenv(self.api_key_env)


class AppConfig(BaseModel):
    top_n: int = 10
    default_scorer: str = "fake"
    enabled_sources: list[SourceName] = Field(default_factory=lambda: [SourceName.FAKE])
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)
    summarizer: SummarizerConfig = Field(default_factory=SummarizerConfig)


def resolve_config_path(base_dir: Path | None = None) -> Path:
    """Prefer ``config.local.toml`` when present; otherwise ``config.toml``.

    Keeps the repo root offline-safe while letting M1/M2 real-source runs use a
    local override without editing the committed default.
    """
    root = base_dir if base_dir is not None else Path.cwd()
    local = root / LOCAL_CONFIG_PATH.name
    if local.is_file():
        return local
    return root / DEFAULT_CONFIG_PATH.name


def load_config(path: Path | None = None) -> AppConfig:
    config_path = path if path is not None else resolve_config_path()
    if not config_path.exists():
        return AppConfig()
    with config_path.open("rb") as fh:
        raw = tomllib.load(fh)
    return AppConfig.model_validate(raw)
