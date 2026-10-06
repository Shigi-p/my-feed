"""Fake source used by C0 and tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from my_feed.ids import make_item_id
from my_feed.models import Item, SourceName


class FakeSourceAdapter:
    """Deterministic in-memory source (no network)."""

    def __init__(self, count: int = 12) -> None:
        self._count = count

    @property
    def name(self) -> SourceName:
        return SourceName.FAKE

    def fetch(self) -> list[Item]:
        now = datetime.now(UTC)
        items: list[Item] = []
        for i in range(1, self._count + 1):
            url = f"https://example.com/fake/{i}"
            items.append(
                Item(
                    id=make_item_id(SourceName.FAKE, official_id=str(i)),
                    source=SourceName.FAKE,
                    title=f"Fake article {i}",
                    url=url,
                    published_at=now - timedelta(hours=i),
                    excerpt=f"Short excerpt for fake article {i}.",
                    tags=["fake", "c0"],
                    metrics={"likes": 100 - i, "stocks": i},
                    fetched_at=now,
                )
            )
        return items
