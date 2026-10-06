"""SourceAdapter contract.

Implementations (T-Src) fetch external content and normalize to ``Item``.
Do not compare raw popularity metrics across sources here — that belongs to
scoring after per-source normalization.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from my_feed.models import Item, SourceName


@runtime_checkable
class SourceAdapter(Protocol):
    """Fetch items from one upstream source."""

    @property
    def name(self) -> SourceName: ...

    def fetch(self) -> list[Item]:
        """Return items on success.

        Raise on temporary transport/parse failure of the whole source so the
        pipeline can record ``source_errors`` and continue other sources.
        Return an empty list when the source genuinely has zero items.
        """
        ...
