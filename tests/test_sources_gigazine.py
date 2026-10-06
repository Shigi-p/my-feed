"""Fixture-based tests for GIGAZINE adapter."""

from __future__ import annotations

import os
from datetime import UTC, datetime

import pytest

from my_feed.models import SourceName
from my_feed.sources import get_source, list_sources
from my_feed.sources.base import SourceAdapter
from my_feed.sources.gigazine import GigazineSourceAdapter, parse_gigazine_rss
from tests.helpers import fixture_text


def test_gigazine_registered():
    assert SourceName.GIGAZINE in list_sources()
    adapter = get_source(SourceName.GIGAZINE)
    assert isinstance(adapter, SourceAdapter)
    assert adapter.name == SourceName.GIGAZINE


def test_parse_gigazine_rss_skips_bad_entries():
    xml = fixture_text("gigazine_rss.xml")
    fetched_at = datetime(2026, 10, 6, tzinfo=UTC)
    items = parse_gigazine_rss(xml, fetched_at=fetched_at)
    assert len(items) == 2
    assert all(i.source == SourceName.GIGAZINE for i in items)
    assert items[0].id.startswith("gigazine:")
    assert "gigazine.net" in items[0].url
    assert items[0].published_at is not None
    assert items[0].excerpt


def test_gigazine_fetch_uses_fetcher():
    xml = fixture_text("gigazine_rss.xml")

    def fake_fetch(url: str, **kwargs):
        assert "gigazine" in url
        return xml

    items = GigazineSourceAdapter(fetcher=fake_fetch).fetch()
    assert len(items) == 2


def test_gigazine_garbage_raises():
    with pytest.raises(RuntimeError, match="RSS parse failed"):
        parse_gigazine_rss("this is not xml at all {{{")


@pytest.mark.network
@pytest.mark.skipif(os.environ.get("MY_FEED_LIVE") != "1", reason="set MY_FEED_LIVE=1")
def test_gigazine_live_fetch():
    items = GigazineSourceAdapter().fetch()
    assert len(items) >= 1
