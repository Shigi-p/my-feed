"""Popularity-only score strategy (per-source normalized)."""

from __future__ import annotations

from my_feed.models import Item, ScoredItem
from my_feed.scoring.normalize import (
    DEFAULT_NEUTRAL,
    NormalizeMethod,
    normalize_popularity_by_source,
)


class PopularityScoreStrategy:
    """Score = source-internal normalized popularity (0..1)."""

    def __init__(
        self,
        *,
        method: NormalizeMethod = "minmax",
        neutral: float = DEFAULT_NEUTRAL,
    ) -> None:
        self._method = method
        self._neutral = neutral

    @property
    def name(self) -> str:
        return "popularity"

    def score(self, items: list[Item]) -> list[ScoredItem]:
        norms = normalize_popularity_by_source(
            items, method=self._method, neutral=self._neutral
        )
        scored: list[ScoredItem] = []
        for item in items:
            pop = norms[item.id]
            scored.append(
                ScoredItem(
                    item=item,
                    score=pop,
                    score_breakdown={"norm_popularity": pop},
                )
            )
        scored.sort(key=lambda s: (-s.score, s.item.id))
        return scored
