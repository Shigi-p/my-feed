"""Fake scorer used by C0 and tests."""

from __future__ import annotations

from my_feed.models import Item, ScoredItem


class FakeScoreStrategy:
    """Order by likes metric (or title) — fine for Fake-only runs."""

    @property
    def name(self) -> str:
        return "fake"

    def score(self, items: list[Item]) -> list[ScoredItem]:
        scored: list[ScoredItem] = []
        for item in items:
            likes = float(item.metrics.get("likes", 0))
            scored.append(
                ScoredItem(
                    item=item,
                    score=likes,
                    score_breakdown={"likes": likes},
                )
            )
        scored.sort(key=lambda s: (-s.score, s.item.id))
        return scored
