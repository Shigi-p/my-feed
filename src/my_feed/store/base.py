"""Persistence contracts (Protocol only).

In-memory fakes: ``store.memory``. SQLite backends: ``store.sqlite``.

``FavoriteStore.remove`` takes a *favorite* id (returned by ``add``), not
``Item.id``. Callers that only have ``Item.id`` should use
``favorite_id_for`` first — Web/UI must not invent a second mapping via
write-on-read side effects.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from my_feed.models import Item, PipelineResult


@runtime_checkable
class RunStore(Protocol):
    def save_run(self, result: PipelineResult) -> str:
        """Persist a run snapshot; return run id."""
        ...

    def get_run(self, run_id: str) -> PipelineResult | None: ...

    def list_runs(self) -> list[str]:
        """Return run ids, newest first preferred."""
        ...


@runtime_checkable
class FavoriteStore(Protocol):
    def add(self, item: Item) -> str:
        """Save favorite; return favorite id."""
        ...

    def list(self) -> list[Item]: ...

    def remove(self, favorite_id: str) -> None: ...

    def favorite_id_for(self, item_id: str) -> str | None:
        """Read-only lookup of favorite id by ``Item.id`` (no writes)."""
        ...
