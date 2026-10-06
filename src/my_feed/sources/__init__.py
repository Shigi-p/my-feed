"""Source adapter registry."""

from __future__ import annotations

from my_feed.models import SourceName
from my_feed.sources.base import SourceAdapter
from my_feed.sources.fake import FakeSourceAdapter

_REGISTRY: dict[SourceName, SourceAdapter] = {
    SourceName.FAKE: FakeSourceAdapter(),
}


def register_source(adapter: SourceAdapter) -> None:
    _REGISTRY[adapter.name] = adapter


def get_source(name: SourceName) -> SourceAdapter:
    try:
        return _REGISTRY[name]
    except KeyError as exc:
        raise KeyError(f"unknown source: {name}") from exc


def list_sources() -> list[SourceName]:
    return sorted(_REGISTRY.keys(), key=lambda s: s.value)
