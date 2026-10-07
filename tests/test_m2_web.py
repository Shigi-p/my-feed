"""M2: config resolution, SQLite-backed Web persistence, source_errors UI."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from my_feed.config import AppConfig, resolve_config_path
from my_feed.models import (
    Item,
    PipelineResult,
    PipelineStatus,
    ScoredItem,
    SourceName,
)
from my_feed.store import InMemoryFavoriteStore, InMemoryRunStore, open_sqlite_stores
from my_feed.web.app import create_app
from my_feed.web.deps import WebDeps, create_default_web_deps


def test_resolve_config_path_prefers_local(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.toml").write_text('top_n = 3\ndefault_scorer = "fake"\nenabled_sources = ["fake"]\n')
    assert resolve_config_path() == tmp_path / "config.toml"
    (tmp_path / "config.local.toml").write_text(
        'top_n = 10\ndefault_scorer = "hybrid"\nenabled_sources = ["zenn"]\n'
    )
    assert resolve_config_path() == tmp_path / "config.local.toml"


def test_create_default_web_deps_uses_sqlite(tmp_path: Path):
    db = tmp_path / "m2.db"
    cfg = tmp_path / "config.toml"
    cfg.write_text('top_n = 5\ndefault_scorer = "hybrid"\nenabled_sources = ["fake"]\n')
    deps = create_default_web_deps(config_path=cfg, db_path=db)
    assert deps.config_path == cfg
    assert deps.db_path == db
    assert db.exists()


def test_web_sqlite_survives_reopen(tmp_path: Path):
    db = tmp_path / "persist.db"
    cfg = tmp_path / "config.toml"
    cfg.write_text('top_n = 10\ndefault_scorer = "fake"\nenabled_sources = ["fake"]\n')

    deps1 = create_default_web_deps(config_path=cfg, db_path=db)
    client1 = TestClient(create_app(deps1))
    res = client1.post("/runs", data={"scorer": "fake"}, follow_redirects=False)
    assert res.status_code == 303
    run_id = res.headers["location"].rsplit("/", 1)[-1]
    saved = deps1.run_store.get_run(run_id)
    assert saved is not None
    item = saved.items[0].item
    client1.post(
        "/favorites",
        data={"run_id": run_id, "item_id": item.id, "next": "/favorites"},
        follow_redirects=False,
    )

    # New process equivalent: new connection to same DB file.
    run_store, favorite_store = open_sqlite_stores(db)
    assert run_id in run_store.list_runs()
    assert run_store.get_run(run_id) is not None
    assert any(f.id == item.id for f in favorite_store.list())


def test_source_errors_rendered_on_run_detail():
    result = PipelineResult(
        items=[
            ScoredItem(
                item=Item(
                    id="fake:1",
                    source=SourceName.FAKE,
                    title="One",
                    url="https://example.com/1",
                    published_at=datetime(2026, 10, 6, tzinfo=UTC),
                    excerpt="e",
                    tags=[],
                    metrics={},
                    fetched_at=datetime(2026, 10, 6, tzinfo=UTC),
                ),
                score=1.0,
                score_breakdown={},
            )
        ],
        scorer="hybrid",
        fetched_at=datetime(2026, 10, 6, tzinfo=UTC),
        source_errors={"github_trending": "simulated outage"},
        status=PipelineStatus.PARTIAL,
    )

    def fake_pipeline(_config: AppConfig) -> PipelineResult:
        return result

    deps = WebDeps(
        run_store=InMemoryRunStore(),
        favorite_store=InMemoryFavoriteStore(),
        run_pipeline_fn=fake_pipeline,
        load_config_fn=lambda _path=None: AppConfig(
            top_n=10,
            default_scorer="hybrid",
            enabled_sources=[SourceName.FAKE],
        ),
        config_path=Path("config.toml"),
    )
    client = TestClient(create_app(deps))
    res = client.post("/runs", data={"scorer": "hybrid"}, follow_redirects=False)
    run_id = res.headers["location"].rsplit("/", 1)[-1]
    detail = client.get(f"/runs/{run_id}")
    assert detail.status_code == 200
    assert "github_trending" in detail.text
    assert "simulated outage" in detail.text
    assert "partial" in detail.text


def test_single_markdown_with_slash_in_item_id():
    """GitHub Trending IDs look like ``github_trending:owner/repo``."""
    from urllib.parse import quote

    gh_id = "github_trending:DuarteSantos8/openGym"
    result = PipelineResult(
        items=[
            ScoredItem(
                item=Item(
                    id=gh_id,
                    source=SourceName.GITHUB_TRENDING,
                    title="openGym",
                    url="https://github.com/DuarteSantos8/openGym",
                    published_at=datetime(2026, 10, 6, tzinfo=UTC),
                    excerpt="repo",
                    tags=["Python"],
                    metrics={"stars_today": 10},
                    fetched_at=datetime(2026, 10, 6, tzinfo=UTC),
                ),
                score=0.9,
                score_breakdown={},
            )
        ],
        scorer="hybrid",
        fetched_at=datetime(2026, 10, 6, tzinfo=UTC),
        source_errors={},
        status=PipelineStatus.OK,
    )

    deps = WebDeps(
        run_store=InMemoryRunStore(),
        favorite_store=InMemoryFavoriteStore(),
        run_pipeline_fn=lambda _c: result,
        load_config_fn=lambda _path=None: AppConfig(
            top_n=10,
            default_scorer="hybrid",
            enabled_sources=[SourceName.GITHUB_TRENDING],
        ),
        config_path=Path("config.toml"),
    )
    client = TestClient(create_app(deps))
    create = client.post("/runs", data={"scorer": "hybrid"}, follow_redirects=False)
    run_id = create.headers["location"].rsplit("/", 1)[-1]

    detail = client.get(f"/runs/{run_id}")
    assert detail.status_code == 200
    encoded = quote(gh_id, safe="")
    assert f"/runs/{run_id}/items/{encoded}/markdown" in detail.text

    md = client.get(f"/runs/{run_id}/items/{encoded}/markdown")
    assert md.status_code == 200
    assert "openGym" in md.text
    assert "attachment" in md.headers.get("content-disposition", "")


def test_fetch_form_defaults_to_hybrid_when_no_result():
    deps = WebDeps(
        run_store=InMemoryRunStore(),
        favorite_store=InMemoryFavoriteStore(),
        load_config_fn=lambda _path=None: AppConfig(
            top_n=10,
            default_scorer="hybrid",
            enabled_sources=[SourceName.FAKE],
        ),
        config_path=Path("config.toml"),
    )
    client = TestClient(create_app(deps))
    home = client.get("/")
    assert home.status_code == 200
    assert 'value="hybrid" selected' in home.text or 'value="hybrid" selected' in home.text
