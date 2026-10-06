"""Recency-only score strategy."""

from __future__ import annotations

from datetime import UTC, datetime

from my_feed.models import Item, ScoredItem
from my_feed.scoring.recency_math import (
    DEFAULT_HALF_LIFE_HOURS,
    DEFAULT_NEUTRAL_RECENCY,
    recency_factor,
)


class RecencyScoreStrategy:
    """Score = time decay from ``published_at`` (half-life exponential)."""

    def __init__(
        self,
        *,
        half_life_hours: float = DEFAULT_HALF_LIFE_HOURS,
        missing_recency: float = DEFAULT_NEUTRAL_RECENCY,
        now: datetime | None = None,
    ) -> None:
        self._half_life_hours = half_life_hours
        self._missing_recency = missing_recency
        self._now = now

    @property
    def name(self) -> str:
        return "recency"

    def score(self, items: list[Item]) -> list[ScoredItem]:
        now = self._now or datetime.now(UTC)
        scored: list[ScoredItem] = []
        for item in items:
            factor = recency_factor(
                item.published_at,
                now=now,
                half_life_hours=self._half_life_hours,
                missing=self._missing_recency,
            )
            scored.append(
                ScoredItem(
                    item=item,
                    score=factor,
                    score_breakdown={"recency_factor": factor},
                )
            )
        scored.sort(key=lambda s: (-s.score, s.item.id))
        return scored
