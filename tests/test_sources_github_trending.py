"""Fixture-based tests for GitHub Trending (isolated scrape)."""

from __future__ import annotations

import os
from datetime import UTC, datetime

import pytest

from my_feed.config import AppConfig
from my_feed.models import PipelineStatus, SourceName
from my_feed.pipeline import run_pipeline
from my_feed.sources import get_source, list_sources, register_source
from my_feed.sources.base import SourceAdapter
from my_feed.sources.github_trending import (
    GitHubTrendingSourceAdapter,
    parse_github_trending_html,
)
from tests.helpers import fixture_text


def test_github_trending_registered():
    assert SourceName.GITHUB_TRENDING in list_sources()
    adapter = get_source(SourceName.GITHUB_TRENDING)
    assert isinstance(adapter, SourceAdapter)
    assert adapter.name == SourceName.GITHUB_TRENDING


def test_parse_github_trending_html():
    html = fixture_text("github_trending.html")
    fetched_at = datetime(2026, 10, 6, tzinfo=UTC)
    items = parse_github_trending_html(html, fetched_at=fetched_at)
    assert len(items) == 2
    assert items[0].source == SourceName.GITHUB_TRENDING
    assert items[0].url.startswith("https://github.com/")
    assert "/" in items[0].title
    assert "stars" in items[0].metrics
    assert "forks" in items[0].metrics
    assert "stars_today" in items[0].metrics


def test_parse_github_trending_empty_page_returns_empty():
    html = fixture_text("github_trending_empty.html")
    assert parse_github_trending_html(html) == []


def test_github_trending_fetch_uses_fetcher():
    html = fixture_text("github_trending.html")

    def fake_fetch(url: str, **kwargs):
        assert "github.com/trending" in url
        return html

    items = GitHubTrendingSourceAdapter(fetcher=fake_fetch).fetch()
    assert len(items) == 2


def test_github_trending_failure_isolated_from_other_sources():
    """T6: trending transport failure must not kill other sources."""

    class BoomTrending:
        @property
        def name(self) -> SourceName:
            return SourceName.GITHUB_TRENDING

        def fetch(self) -> list:
            raise RuntimeError("simulated trending outage")

    register_source(BoomTrending())
    try:
        result = run_pipeline(
            AppConfig(
                top_n=5,
                default_scorer="fake",
                enabled_sources=[SourceName.FAKE, SourceName.GITHUB_TRENDING],
            )
        )
        assert result.status == PipelineStatus.PARTIAL
        assert "github_trending" in result.source_errors
        assert len(result.items) == 5
        assert all(s.item.source == SourceName.FAKE for s in result.items)
    finally:
        # Restore the real adapter for later tests in the same session.
        register_source(GitHubTrendingSourceAdapter())


@pytest.mark.network
@pytest.mark.skipif(os.environ.get("MY_FEED_LIVE") != "1", reason="set MY_FEED_LIVE=1")
def test_github_trending_live_fetch():
    items = GitHubTrendingSourceAdapter().fetch()
    assert len(items) >= 1
