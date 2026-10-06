"""ScoreStrategy contract.

Strategies must not compare raw like/star counts across sources. Normalize
within each source first (rank or min-max), then combine. Missing metrics
should use a neutral value or rely on recency (T-Score).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from my_feed.models import Item, ScoredItem


@runtime_checkable
class ScoreStrategy(Protocol):
    """Rank items for cross-source selection."""

    @property
    def name(self) -> str: ...

    def score(self, items: list[Item]) -> list[ScoredItem]:
        """Return scored items sorted by score descending."""
        ...
