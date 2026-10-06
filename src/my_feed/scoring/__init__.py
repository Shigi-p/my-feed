"""Score strategy registry and config-aware factories."""

from __future__ import annotations

from my_feed.config import AppConfig, HybridScoringConfig
from my_feed.scoring.base import ScoreStrategy
from my_feed.scoring.fake import FakeScoreStrategy
from my_feed.scoring.hybrid import HybridScoreStrategy
from my_feed.scoring.popularity import PopularityScoreStrategy
from my_feed.scoring.recency import RecencyScoreStrategy

# Default instances for list_scorers() / simple lookups without AppConfig.
# Prefer ``build_scorer(name, config)`` in the pipeline so config.toml knobs apply.
_REGISTRY: dict[str, ScoreStrategy] = {
    "fake": FakeScoreStrategy(),
    "popularity": PopularityScoreStrategy(),
    "recency": RecencyScoreStrategy(),
    "hybrid": HybridScoreStrategy(),
}


def register_scorer(strategy: ScoreStrategy) -> None:
    _REGISTRY[strategy.name] = strategy


def get_scorer(name: str) -> ScoreStrategy:
    """Return a registered default instance (ignores AppConfig scoring knobs).

    Use ``build_scorer`` when running the real pipeline so ``[scoring.hybrid]``
    from config.toml is applied.
    """
    try:
        return _REGISTRY[name]
    except KeyError as exc:
        raise KeyError(f"unknown scorer: {name}") from exc


def build_scorer(name: str, config: AppConfig) -> ScoreStrategy:
    """Construct a scorer with parameters from ``config.scoring``.

    Without this factory, editing ``config.toml`` would appear to work (values
    load into AppConfig) but registry singletons would keep constructor defaults.
    """
    hybrid_cfg: HybridScoringConfig = config.scoring.hybrid
    if name == "fake":
        return FakeScoreStrategy()
    if name == "popularity":
        return PopularityScoreStrategy(neutral=hybrid_cfg.neutral_popularity_when_missing)
    if name == "recency":
        return RecencyScoreStrategy(half_life_hours=hybrid_cfg.recency_half_life_hours)
    if name == "hybrid":
        return HybridScoreStrategy(
            half_life_hours=hybrid_cfg.recency_half_life_hours,
            neutral_popularity=hybrid_cfg.neutral_popularity_when_missing,
        )
    raise KeyError(f"unknown scorer: {name}")


def list_scorers() -> list[str]:
    return sorted(_REGISTRY.keys())
