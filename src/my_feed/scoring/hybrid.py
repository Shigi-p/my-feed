"""Hybrid score strategy: normalized popularity × recency."""

from __future__ import annotations

from datetime import UTC, datetime

from my_feed.models import Item, ScoredItem
from my_feed.scoring.normalize import (
    DEFAULT_NEUTRAL,
    NormalizeMethod,
    normalize_popularity_by_source,
)
from my_feed.scoring.recency_math import (
    DEFAULT_HALF_LIFE_HOURS,
    DEFAULT_NEUTRAL_RECENCY,
    recency_factor,
)


class HybridScoreStrategy:
    """Score = ``norm_popularity * recency_factor`` (default candidate strategy)."""

    def __init__(
        self,
        *,
        method: NormalizeMethod = "minmax",
        neutral_popularity: float = DEFAULT_NEUTRAL,
        half_life_hours: float = DEFAULT_HALF_LIFE_HOURS,
        missing_recency: float = DEFAULT_NEUTRAL_RECENCY,
        now: datetime | None = None,
    ) -> None:
        self._method = method
        self._neutral_popularity = neutral_popularity
        self._half_life_hours = half_life_hours
        self._missing_recency = missing_recency
        self._now = now

    @property
    def name(self) -> str:
        return "hybrid"

    def score(self, items: list[Item]) -> list[ScoredItem]:
        now = self._now or datetime.now(UTC)
        norms = normalize_popularity_by_source(
            items, method=self._method, neutral=self._neutral_popularity
        )
        scored: list[ScoredItem] = []
        for item in items:
            pop = norms[item.id]
            rec = recency_factor(
                item.published_at,
                now=now,
                half_life_hours=self._half_life_hours,
                missing=self._missing_recency,
            )
            total = pop * rec
            scored.append(
                ScoredItem(
                    item=item,
                    score=total,
                    score_breakdown={
                        "norm_popularity": pop,
                        "recency_factor": rec,
                        "hybrid": total,
                    },
                )
            )
        scored.sort(key=lambda s: (-s.score, s.item.id))
        return scored
