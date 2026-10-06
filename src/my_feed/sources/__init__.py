"""Source adapter registry."""

from __future__ import annotations

from my_feed.models import SourceName
from my_feed.sources.base import SourceAdapter
from my_feed.sources.fake import FakeSourceAdapter
from my_feed.sources.gigazine import GigazineSourceAdapter
from my_feed.sources.github_trending import GitHubTrendingSourceAdapter
from my_feed.sources.qiita import QiitaSourceAdapter
from my_feed.sources.zenn import ZennSourceAdapter

_REGISTRY: dict[SourceName, SourceAdapter] = {
    SourceName.FAKE: FakeSourceAdapter(),
    SourceName.ZENN: ZennSourceAdapter(),
    SourceName.QIITA: QiitaSourceAdapter(),
    SourceName.GIGAZINE: GigazineSourceAdapter(),
    SourceName.GITHUB_TRENDING: GitHubTrendingSourceAdapter(),
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
