"""Score strategy registry."""

from __future__ import annotations

from my_feed.scoring.base import ScoreStrategy
from my_feed.scoring.fake import FakeScoreStrategy

_REGISTRY: dict[str, ScoreStrategy] = {
    "fake": FakeScoreStrategy(),
}


def register_scorer(strategy: ScoreStrategy) -> None:
    _REGISTRY[strategy.name] = strategy


def get_scorer(name: str) -> ScoreStrategy:
    try:
        return _REGISTRY[name]
    except KeyError as exc:
        raise KeyError(f"unknown scorer: {name}") from exc


def list_scorers() -> list[str]:
    return sorted(_REGISTRY.keys())
