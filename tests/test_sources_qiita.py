"""Fixture-based tests for Qiita adapter."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime

import pytest

from my_feed.models import SourceName
from my_feed.sources import get_source, list_sources
from my_feed.sources.base import SourceAdapter
from my_feed.sources.qiita import QiitaSourceAdapter, parse_qiita_items
from tests.helpers import fixture_text


def test_qiita_registered():
    assert SourceName.QIITA in list_sources()
    adapter = get_source(SourceName.QIITA)
    assert isinstance(adapter, SourceAdapter)
    assert adapter.name == SourceName.QIITA


def test_parse_qiita_items_skips_bad_entries():
    payload = json.loads(fixture_text("qiita_items.json"))
    fetched_at = datetime(2026, 10, 6, tzinfo=UTC)
    items = parse_qiita_items(payload, fetched_at=fetched_at)
    assert len(items) == 2
    assert items[0].id.startswith("qiita:")
    assert items[0].url.startswith("https://qiita.com/")
    assert "likes" in items[0].metrics
    assert "stocks" in items[0].metrics
    assert items[0].tags


def test_qiita_fetch_uses_fetcher():
    payload = fixture_text("qiita_items.json")

    def fake_fetch(url: str, **kwargs):
        assert "qiita.com" in url
        return payload

    items = QiitaSourceAdapter(fetcher=fake_fetch).fetch()
    assert len(items) == 2


def test_qiita_invalid_json_raises():
    def bad_json(url: str, **kwargs):
        return "not-json"

    with pytest.raises(RuntimeError, match="invalid JSON"):
        QiitaSourceAdapter(fetcher=bad_json).fetch()


@pytest.mark.network
@pytest.mark.skipif(os.environ.get("MY_FEED_LIVE") != "1", reason="set MY_FEED_LIVE=1")
def test_qiita_live_fetch():
    items = QiitaSourceAdapter().fetch()
    assert len(items) >= 1
