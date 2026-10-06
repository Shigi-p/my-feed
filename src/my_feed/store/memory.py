"""In-memory RunStore / FavoriteStore (C0 Fake, T-Web default)."""

from __future__ import annotations

from my_feed.models import Item, PipelineResult


class InMemoryRunStore:
    """C0 / T-Web Fake store."""

    def __init__(self) -> None:
        self._runs: dict[str, PipelineResult] = {}
        self._order: list[str] = []

    def save_run(self, result: PipelineResult) -> str:
        run_id = f"run-{len(self._order) + 1}"
        self._runs[run_id] = result
        self._order.insert(0, run_id)
        return run_id

    def get_run(self, run_id: str) -> PipelineResult | None:
        return self._runs.get(run_id)

    def list_runs(self) -> list[str]:
        return list(self._order)


class InMemoryFavoriteStore:
    """C0 / T-Web Fake store."""

    def __init__(self) -> None:
        self._items: dict[str, Item] = {}
        self._ids_by_item: dict[str, str] = {}
        self._seq = 0

    def add(self, item: Item) -> str:
        existing = self._ids_by_item.get(item.id)
        if existing:
            self._items[existing] = item
            return existing
        self._seq += 1
        fav_id = f"fav-{self._seq}"
        self._items[fav_id] = item
        self._ids_by_item[item.id] = fav_id
        return fav_id

    def list(self) -> list[Item]:
        return list(self._items.values())

    def remove(self, favorite_id: str) -> None:
        item = self._items.pop(favorite_id, None)
        if item is not None:
            self._ids_by_item.pop(item.id, None)
