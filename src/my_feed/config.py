"""Load ``config.toml`` (C0 minimal settings + optional scoring knobs)."""

from __future__ import annotations

import tomllib
from pathlib import Path

from pydantic import BaseModel, Field

from my_feed.models import SourceName

DEFAULT_CONFIG_PATH = Path("config.toml")


class HybridScoringConfig(BaseModel):
    """Parameters for the hybrid (and related) scorers."""

    recency_half_life_hours: float = 36.0
    neutral_popularity_when_missing: float = 0.5


class ScoringConfig(BaseModel):
    """Optional scoring section; deep tuning is M3."""

    hybrid: HybridScoringConfig = Field(default_factory=HybridScoringConfig)


class AppConfig(BaseModel):
    top_n: int = 10
    default_scorer: str = "fake"
    enabled_sources: list[SourceName] = Field(default_factory=lambda: [SourceName.FAKE])
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)


def load_config(path: Path | None = None) -> AppConfig:
    config_path = path or DEFAULT_CONFIG_PATH
    if not config_path.exists():
        return AppConfig()
    with config_path.open("rb") as fh:
        raw = tomllib.load(fh)
    return AppConfig.model_validate(raw)
