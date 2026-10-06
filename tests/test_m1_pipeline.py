"""M1 integration: real source names + scorers without live network."""

from __future__ import annotations

import os
from datetime import UTC, datetime

import pytest

from my_feed.config import AppConfig
from my_feed.models import Item, PipelineStatus, SourceName
from my_feed.pipeline import run_pipeline
from my_feed.sources import register_source
from my_feed.sources.fake import FakeSourceAdapter
from my_feed.sources.gigazine import GigazineSourceAdapter
from my_feed.sources.github_trending import GitHubTrendingSourceAdapter
from my_feed.sources.qiita import QiitaSourceAdapter
from my_feed.sources.zenn import ZennSourceAdapter


def _item(source: SourceName, n: int, *, likes: float = 10.0) -> Item:
    return Item(
        id=f"{source.value}:m1-{n}",
        source=source,
        title=f"{source.value} item {n}",
        url=f"https://example.com/{source.value}/{n}",
        published_at=datetime(2026, 10, 6, tzinfo=UTC),
        excerpt="m1 fixture",
        tags=["m1"],
        metrics={"likes": likes, "stars_today": likes},
        fetched_at=datetime(2026, 10, 6, tzinfo=UTC),
    )


class _FixedAdapter:
    def __init__(self, source: SourceName, items: list[Item]) -> None:
        self._name = source
        self._items = items

    @property
    def name(self) -> SourceName:
        return self._name

    def fetch(self) -> list[Item]:
        return list(self._items)


class _BoomAdapter:
    def __init__(self, source: SourceName) -> None:
        self._name = source

    @property
    def name(self) -> SourceName:
        return self._name

    def fetch(self) -> list[Item]:
        raise RuntimeError(f"simulated {self._name.value} outage")


@pytest.fixture
def restore_real_sources():
    """Ensure session registry is restored after M1 register_source swaps."""
    yield
    register_source(FakeSourceAdapter())
    register_source(ZennSourceAdapter())
    register_source(QiitaSourceAdapter())
    register_source(GigazineSourceAdapter())
    register_source(GitHubTrendingSourceAdapter())


def test_m1_pipeline_top_n_with_hybrid(restore_real_sources):
    register_source(_FixedAdapter(SourceName.ZENN, [_item(SourceName.ZENN, 1, likes=100)]))
    register_source(_FixedAdapter(SourceName.QIITA, [_item(SourceName.QIITA, 1, likes=50)]))
    register_source(_FixedAdapter(SourceName.GIGAZINE, [_item(SourceName.GIGAZINE, 1, likes=1)]))
    register_source(
        _FixedAdapter(SourceName.GITHUB_TRENDING, [_item(SourceName.GITHUB_TRENDING, 1, likes=80)])
    )

    result = run_pipeline(
        AppConfig(
            top_n=3,
            default_scorer="hybrid",
            enabled_sources=[
                SourceName.ZENN,
                SourceName.QIITA,
                SourceName.GIGAZINE,
                SourceName.GITHUB_TRENDING,
            ],
        )
    )

    assert result.status == PipelineStatus.OK
    assert result.scorer == "hybrid"
    assert len(result.items) == 3
    assert result.source_errors == {}
    assert result.items[0].score >= result.items[-1].score


def test_m1_pipeline_scorer_switch(restore_real_sources):
    register_source(_FixedAdapter(SourceName.ZENN, [_item(SourceName.ZENN, 1, likes=10)]))

    hybrid = run_pipeline(
        AppConfig(top_n=1, default_scorer="hybrid", enabled_sources=[SourceName.ZENN])
    )
    popularity = run_pipeline(
        AppConfig(top_n=1, default_scorer="popularity", enabled_sources=[SourceName.ZENN])
    )
    recency = run_pipeline(
        AppConfig(top_n=1, default_scorer="recency", enabled_sources=[SourceName.ZENN])
    )

    assert hybrid.scorer == "hybrid"
    assert popularity.scorer == "popularity"
    assert recency.scorer == "recency"
    assert len(hybrid.items) == len(popularity.items) == len(recency.items) == 1


def test_m1_pipeline_partial_when_one_source_fails(restore_real_sources):
    register_source(_FixedAdapter(SourceName.ZENN, [_item(SourceName.ZENN, i) for i in range(5)]))
    register_source(_BoomAdapter(SourceName.GITHUB_TRENDING))

    result = run_pipeline(
        AppConfig(
            top_n=5,
            default_scorer="hybrid",
            enabled_sources=[SourceName.ZENN, SourceName.GITHUB_TRENDING],
        )
    )

    assert result.status == PipelineStatus.PARTIAL
    assert "github_trending" in result.source_errors
    assert len(result.items) == 5
    assert all(s.item.source == SourceName.ZENN for s in result.items)


def test_m1_pipeline_error_when_all_sources_fail(restore_real_sources):
    register_source(_BoomAdapter(SourceName.ZENN))
    register_source(_BoomAdapter(SourceName.QIITA))

    result = run_pipeline(
        AppConfig(
            top_n=10,
            default_scorer="hybrid",
            enabled_sources=[SourceName.ZENN, SourceName.QIITA],
        )
    )

    assert result.status == PipelineStatus.ERROR
    assert set(result.source_errors) == {"zenn", "qiita"}
    assert result.items == []


@pytest.mark.network
@pytest.mark.skipif(os.environ.get("MY_FEED_LIVE") != "1", reason="set MY_FEED_LIVE=1")
def test_m1_live_pipeline_top_n():
    """Opt-in smoke: real adapters + hybrid produce a non-empty Top N."""
    # Ensure live adapters (not leftover test doubles) are registered.
    register_source(ZennSourceAdapter())
    register_source(QiitaSourceAdapter())
    register_source(GigazineSourceAdapter())
    register_source(GitHubTrendingSourceAdapter())

    result = run_pipeline(
        AppConfig(
            top_n=10,
            default_scorer="hybrid",
            enabled_sources=[
                SourceName.ZENN,
                SourceName.QIITA,
                SourceName.GIGAZINE,
                SourceName.GITHUB_TRENDING,
            ],
        )
    )

    assert result.status in {PipelineStatus.OK, PipelineStatus.PARTIAL}
    assert result.scorer == "hybrid"
    assert 1 <= len(result.items) <= 10
    # At least one real upstream should succeed for M1 to be meaningful.
    assert len(result.source_errors) < 4
