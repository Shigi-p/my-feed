"""T-Web route smoke tests (TestClient + in-memory fakes)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from my_feed.config import AppConfig
from my_feed.models import SourceName
from my_feed.store import InMemoryFavoriteStore, InMemoryRunStore
from my_feed.web.app import create_app
from my_feed.web.deps import WebDeps


def _client() -> TestClient:
    deps = WebDeps(
        run_store=InMemoryRunStore(),
        favorite_store=InMemoryFavoriteStore(),
        load_config_fn=lambda _path=None: AppConfig(
            top_n=10,
            default_scorer="fake",
            enabled_sources=[SourceName.FAKE],
        ),
    )
    return TestClient(create_app(deps))


def test_index_empty():
    client = _client()
    res = client.get("/")
    assert res.status_code == 200
    assert "my feed" in res.text
    assert "いま取得" in res.text


def test_create_run_list_detail_and_markdown():
    client = _client()
    res = client.post("/runs", data={"scorer": "fake"}, follow_redirects=False)
    assert res.status_code == 303
    loc = res.headers["location"]
    assert loc.startswith("/runs/")
    run_id = loc.rsplit("/", 1)[-1]

    home = client.get("/")
    assert home.status_code == 200
    assert "fake:" in home.text or "score" in home.text

    history = client.get("/runs")
    assert history.status_code == 200
    assert run_id in history.text

    detail = client.get(f"/runs/{run_id}")
    assert detail.status_code == 200
    assert "Markdown DL" in detail.text

    md = client.get(f"/runs/{run_id}/markdown")
    assert md.status_code == 200
    assert "attachment" in md.headers.get("content-disposition", "")
    assert "my feed" in md.text

    saved = client.app.state.deps.run_store.get_run(run_id)
    assert saved is not None and saved.items
    item_id = saved.items[0].item.id
    single = client.get(f"/runs/{run_id}/items/{item_id}/markdown")
    assert single.status_code == 200
    assert saved.items[0].item.title in single.text


def test_favorites_add_list_and_delete():
    client = _client()
    create = client.post("/runs", data={"scorer": "fake"}, follow_redirects=False)
    run_id = create.headers["location"].rsplit("/", 1)[-1]
    saved = client.app.state.deps.run_store.get_run(run_id)
    assert saved is not None
    item = saved.items[0].item

    add = client.post(
        "/favorites",
        data={"run_id": run_id, "item_id": item.id, "next": "/favorites"},
        follow_redirects=False,
    )
    assert add.status_code == 303
    assert add.headers["location"] == "/favorites"

    page = client.get("/favorites")
    assert page.status_code == 200
    assert item.title in page.text

    fav_id = client.app.state.deps.favorite_store.add(item)
    deleted = client.delete(f"/favorites/{fav_id}")
    assert deleted.status_code == 204
    assert client.app.state.deps.favorite_store.list() == []


def test_missing_run_404():
    client = _client()
    assert client.get("/runs/nope").status_code == 404
    assert client.get("/runs/nope/markdown").status_code == 404
