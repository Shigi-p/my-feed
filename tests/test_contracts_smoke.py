"""Smoke tests for C0 contracts."""

from __future__ import annotations

from datetime import UTC, datetime

from my_feed.config import AppConfig, load_config
from my_feed.ids import make_item_id, normalize_url
from my_feed.models import Item, PipelineStatus, RenderMeta, SourceName
from my_feed.output import render_bundle, render_single
from my_feed.pipeline import run_pipeline
from my_feed.scoring import get_scorer, list_scorers
from my_feed.scoring.base import ScoreStrategy
from my_feed.sources import get_source, list_sources
from my_feed.sources.base import SourceAdapter
from my_feed.store import InMemoryFavoriteStore, InMemoryRunStore


def test_load_default_config(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text(
        'top_n = 5\ndefault_scorer = "fake"\nenabled_sources = ["fake"]\n',
        encoding="utf-8",
    )
    config = load_config(path)
    assert config.top_n == 5
    assert config.default_scorer == "fake"
    assert config.enabled_sources == [SourceName.FAKE]


def test_make_item_id_official_and_url():
    assert make_item_id(SourceName.ZENN, official_id="abc") == "zenn:abc"
    a = make_item_id(SourceName.QIITA, url="https://Example.com/path/")
    b = make_item_id(SourceName.QIITA, url="https://example.com/path")
    assert a == b
    assert a.startswith("qiita:url:")
    assert normalize_url("https://Example.com/x/") == "https://example.com/x"


def test_fake_adapters_are_protocols():
    source = get_source(SourceName.FAKE)
    scorer = get_scorer("fake")
    assert isinstance(source, SourceAdapter)
    assert isinstance(scorer, ScoreStrategy)
    assert SourceName.FAKE in list_sources()
    assert "fake" in list_scorers()


def test_real_sources_are_registered():
    for name in (
        SourceName.ZENN,
        SourceName.QIITA,
        SourceName.GIGAZINE,
        SourceName.GITHUB_TRENDING,
    ):
        adapter = get_source(name)
        assert isinstance(adapter, SourceAdapter)
        assert adapter.name == name
        assert name in list_sources()


def test_run_pipeline_returns_top_n():
    result = run_pipeline(
        AppConfig(top_n=10, default_scorer="fake", enabled_sources=[SourceName.FAKE])
    )
    assert result.status == PipelineStatus.OK
    assert result.scorer == "fake"
    assert len(result.items) == 10
    scores = [s.score for s in result.items]
    assert scores == sorted(scores, reverse=True)


def test_render_and_memory_stores():
    result = run_pipeline(AppConfig(top_n=3, enabled_sources=[SourceName.FAKE]))
    meta = RenderMeta(
        generated_at=result.fetched_at,
        scorer=result.scorer,
        count=len(result.items),
    )
    bundle = render_bundle(result.items, meta)
    assert "my feed" in bundle
    assert "### なぜ今見るか" in bundle
    assert "### 壁打ちの問い" in bundle
    assert result.items[0].item.title in bundle
    single = render_single(result.items[0], meta)
    assert result.items[0].item.title in single
    assert "Gemini への貼り付け" in single

    runs = InMemoryRunStore()
    run_id = runs.save_run(result)
    assert runs.get_run(run_id) == result
    assert runs.list_runs() == [run_id]

    favs = InMemoryFavoriteStore()
    item = result.items[0].item
    fav_id = favs.add(item)
    assert favs.add(item) == fav_id  # upsert by item.id
    assert favs.list()[0].id == item.id
    favs.remove(fav_id)
    assert favs.list() == []


def test_item_model_roundtrip():
    now = datetime.now(UTC)
    item = Item(
        id="fake:1",
        source=SourceName.FAKE,
        title="t",
        url="https://example.com/1",
        fetched_at=now,
        metrics={"likes": 1},
    )
    assert item.model_dump()["source"] == "fake"
