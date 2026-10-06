"""Unit tests for SQLite RunStore / FavoriteStore (T-Store)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from my_feed.config import AppConfig
from my_feed.models import Item, PipelineStatus, SourceName
from my_feed.pipeline import run_pipeline
from my_feed.store import (
    DEFAULT_DB_PATH,
    FavoriteStore,
    InMemoryFavoriteStore,
    InMemoryRunStore,
    RunStore,
    SQLiteFavoriteStore,
    SQLiteRunStore,
    create_sqlite_favorite_store,
    create_sqlite_run_store,
    open_sqlite_stores,
)
from my_feed.store.sqlite import connect, ensure_schema


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "test.db"


@pytest.fixture
def sample_result():
    return run_pipeline(
        AppConfig(top_n=3, default_scorer="fake", enabled_sources=[SourceName.FAKE])
    )


def test_default_db_path():
    assert DEFAULT_DB_PATH == Path("data/my_feed.db")


def test_schema_creates_tables(db_path: Path):
    conn = connect(db_path)
    ensure_schema(conn)
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    assert "runs" in tables
    assert "favorites" in tables
    conn.close()


def test_sqlite_stores_satisfy_protocols(db_path: Path):
    runs, favs = open_sqlite_stores(db_path)
    assert isinstance(runs, RunStore)
    assert isinstance(favs, FavoriteStore)


def test_run_store_crud_persists_across_connections(
    db_path: Path, sample_result
) -> None:
    store = create_sqlite_run_store(db_path)
    run_id = store.save_run(sample_result)
    assert store.get_run(run_id) == sample_result
    assert store.list_runs() == [run_id]
    assert store.get_run("missing") is None

    # Re-open as a fresh connection (process restart simulation).
    store2 = create_sqlite_run_store(db_path)
    loaded = store2.get_run(run_id)
    assert loaded is not None
    assert loaded == sample_result
    assert loaded.status == PipelineStatus.OK
    assert loaded.scorer == "fake"
    assert len(loaded.items) == 3


def test_list_runs_newest_first(db_path: Path, sample_result) -> None:
    store = create_sqlite_run_store(db_path)
    older = sample_result.model_copy(
        update={"fetched_at": datetime(2020, 1, 1, tzinfo=UTC)}
    )
    newer = sample_result.model_copy(
        update={"fetched_at": datetime(2024, 6, 1, tzinfo=UTC)}
    )
    id_old = store.save_run(older)
    id_new = store.save_run(newer)
    assert store.list_runs() == [id_new, id_old]


def test_favorite_upsert_by_item_id_and_persist(db_path: Path) -> None:
    store = create_sqlite_favorite_store(db_path)
    now = datetime.now(UTC)
    item = Item(
        id="fake:1",
        source=SourceName.FAKE,
        title="first",
        url="https://example.com/1",
        fetched_at=now,
        tags=["a"],
        metrics={"likes": 1},
    )
    fav_id = store.add(item)
    assert store.add(item) == fav_id  # upsert keeps same favorite id
    assert store.favorite_id_for(item.id) == fav_id
    assert store.favorite_id_for("missing") is None

    updated = item.model_copy(update={"title": "updated"})
    assert store.add(updated) == fav_id
    listed = store.list()
    assert len(listed) == 1
    assert listed[0].title == "updated"

    # Persist across reconnect.
    store2 = create_sqlite_favorite_store(db_path)
    assert store2.list()[0].title == "updated"
    assert store2.favorite_id_for(item.id) == fav_id
    store2.remove(fav_id)
    assert store2.list() == []
    assert store2.favorite_id_for(item.id) is None

    # remove is idempotent for unknown ids
    store2.remove("no-such-id")
    assert store2.list() == []


def test_inmemory_favorite_id_for_is_read_only():
    favs = InMemoryFavoriteStore()
    now = datetime.now(UTC)
    item = Item(
        id="fake:9",
        source=SourceName.FAKE,
        title="t",
        url="https://example.com/9",
        fetched_at=now,
    )
    assert favs.favorite_id_for(item.id) is None
    fav_id = favs.add(item)
    assert favs.favorite_id_for(item.id) == fav_id
    assert favs.list() == [item]


def test_open_sqlite_stores_share_db(db_path: Path, sample_result) -> None:
    runs, favs = open_sqlite_stores(db_path)
    run_id = runs.save_run(sample_result)
    fav_id = favs.add(sample_result.items[0].item)

    runs2, favs2 = open_sqlite_stores(db_path)
    assert runs2.get_run(run_id) == sample_result
    assert favs2.list()[0].id == sample_result.items[0].item.id
    favs2.remove(fav_id)
    assert favs2.list() == []


def test_inmemory_stores_still_available():
    """T-Web Fake path must keep working without SQLite."""
    assert InMemoryRunStore is not None
    assert InMemoryFavoriteStore is not None
    runs = InMemoryRunStore()
    favs = InMemoryFavoriteStore()
    assert isinstance(runs, RunStore)
    assert isinstance(favs, FavoriteStore)


def test_factory_creates_concrete_types(db_path: Path):
    assert isinstance(create_sqlite_run_store(db_path), SQLiteRunStore)
    assert isinstance(create_sqlite_favorite_store(db_path), SQLiteFavoriteStore)
