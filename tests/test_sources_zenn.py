"""Fixture-based tests for Zenn adapter."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime

import pytest

from my_feed.models import SourceName
from my_feed.sources import get_source, list_sources
from my_feed.sources.base import SourceAdapter
from my_feed.sources.zenn import ZennSourceAdapter, parse_zenn_articles
from tests.helpers import fixture_text


def test_zenn_registered():
    assert SourceName.ZENN in list_sources()
    adapter = get_source(SourceName.ZENN)
    assert isinstance(adapter, SourceAdapter)
    assert adapter.name == SourceName.ZENN


def test_parse_zenn_articles_skips_bad_entries():
    payload = json.loads(fixture_text("zenn_articles.json"))
    fetched_at = datetime(2026, 10, 6, tzinfo=UTC)
    items = parse_zenn_articles(payload, fetched_at=fetched_at)
    assert len(items) == 2
    assert all(i.source == SourceName.ZENN for i in items)
    assert items[0].id.startswith("zenn:")
    assert items[0].url.startswith("https://zenn.dev/")
    assert "likes" in items[0].metrics
    assert items[0].fetched_at == fetched_at


def test_zenn_fetch_uses_fetcher():
    payload = fixture_text("zenn_articles.json")

    def fake_fetch(url: str, **kwargs):
        assert "zenn.dev" in url
        return payload

    items = ZennSourceAdapter(fetcher=fake_fetch).fetch()
    assert len(items) == 2


def test_zenn_transport_failure_raises():
    def boom(url: str, **kwargs):
        raise RuntimeError("fetch failed for https://zenn.dev/api/articles: boom")

    with pytest.raises(RuntimeError, match="fetch failed"):
        ZennSourceAdapter(fetcher=boom).fetch()


@pytest.mark.network
@pytest.mark.skipif(os.environ.get("MY_FEED_LIVE") != "1", reason="set MY_FEED_LIVE=1")
def test_zenn_live_fetch():
    items = ZennSourceAdapter().fetch()
    assert len(items) >= 1
