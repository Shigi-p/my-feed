"""SQLite backends for RunStore and FavoriteStore (T-Store)."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from my_feed.models import Item, PipelineResult

DEFAULT_DB_PATH: Final[Path] = Path("data/my_feed.db")

_SCHEMA_SQL: Final[str] = """
CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    scorer TEXT NOT NULL,
    -- Column name is historical: stores len(result.items) at save time,
    -- NOT AppConfig.top_n. Rename carefully if dashboards ever assume "requested N".
    top_n INTEGER NOT NULL,
    status TEXT NOT NULL,
    source_errors TEXT NOT NULL,
    result_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS favorites (
    id TEXT PRIMARY KEY,
    item_id TEXT NOT NULL UNIQUE,
    saved_at TEXT NOT NULL,
    item_json TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_runs_created_at ON runs (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_favorites_saved_at ON favorites (saved_at DESC);
"""


def connect(
    db_path: Path | str | None = None,
    *,
    check_same_thread: bool = True,
) -> sqlite3.Connection:
    """Open a SQLite connection and ensure schema exists.

    Lifecycle note (M2 / T-Web): the returned connection is owned by the caller.
    Default sqlite3 connections are not safely shared across threads. For the
    local FastAPI UI (TestClient / threadpool), pass ``check_same_thread=False``
    via ``open_sqlite_stores``. Factories do not close the connection — call
    ``conn.close()`` when the process/app shuts down.
    """
    path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=check_same_thread)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    """Create runs / favorites tables if missing."""
    conn.executescript(_SCHEMA_SQL)
    conn.commit()


class SQLiteRunStore:
    """Persist pipeline runs in SQLite."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def save_run(self, result: PipelineResult) -> str:
        run_id = str(uuid.uuid4())
        created_at = result.fetched_at.astimezone(UTC).isoformat()
        # Persist actual returned count (see schema comment on top_n).
        result_count = len(result.items)
        self._conn.execute(
            """
            INSERT INTO runs (
                id, created_at, scorer, top_n, status, source_errors, result_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                created_at,
                result.scorer,
                result_count,
                result.status.value,
                json.dumps(result.source_errors, ensure_ascii=False),
                result.model_dump_json(),
            ),
        )
        self._conn.commit()
        return run_id

    def get_run(self, run_id: str) -> PipelineResult | None:
        row = self._conn.execute(
            "SELECT result_json FROM runs WHERE id = ?",
            (run_id,),
        ).fetchone()
        if row is None:
            return None
        return PipelineResult.model_validate_json(row["result_json"])

    def list_runs(self) -> list[str]:
        rows = self._conn.execute(
            "SELECT id FROM runs ORDER BY created_at DESC, rowid DESC"
        ).fetchall()
        return [row["id"] for row in rows]


class SQLiteFavoriteStore:
    """Persist favorites in SQLite; upsert by ``item.id``."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(self, item: Item) -> str:
        existing = self._conn.execute(
            "SELECT id FROM favorites WHERE item_id = ?",
            (item.id,),
        ).fetchone()
        item_json = item.model_dump_json()
        if existing is not None:
            fav_id = existing["id"]
            self._conn.execute(
                """
                UPDATE favorites
                SET item_json = ?, saved_at = ?
                WHERE id = ?
                """,
                (item_json, datetime.now(UTC).isoformat(), fav_id),
            )
            self._conn.commit()
            return fav_id

        fav_id = str(uuid.uuid4())
        self._conn.execute(
            """
            INSERT INTO favorites (id, item_id, saved_at, item_json, note)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                fav_id,
                item.id,
                datetime.now(UTC).isoformat(),
                item_json,
                "",
            ),
        )
        self._conn.commit()
        return fav_id

    def list(self) -> list[Item]:
        rows = self._conn.execute(
            "SELECT item_json FROM favorites ORDER BY saved_at DESC, rowid DESC"
        ).fetchall()
        return [Item.model_validate_json(row["item_json"]) for row in rows]

    def remove(self, favorite_id: str) -> None:
        # favorite_id is favorites.id, not Item.id (see FavoriteStore contract).
        self._conn.execute("DELETE FROM favorites WHERE id = ?", (favorite_id,))
        self._conn.commit()

    def favorite_id_for(self, item_id: str) -> str | None:
        row = self._conn.execute(
            "SELECT id FROM favorites WHERE item_id = ?",
            (item_id,),
        ).fetchone()
        return None if row is None else row["id"]


def create_sqlite_run_store(db_path: Path | str | None = None) -> SQLiteRunStore:
    """Factory: open DB (default ``data/my_feed.db``) and return a RunStore."""
    return SQLiteRunStore(connect(db_path))


def create_sqlite_favorite_store(
    db_path: Path | str | None = None,
) -> SQLiteFavoriteStore:
    """Factory: open DB (default ``data/my_feed.db``) and return a FavoriteStore."""
    return SQLiteFavoriteStore(connect(db_path))


def open_sqlite_stores(
    db_path: Path | str | None = None,
    *,
    check_same_thread: bool = False,
) -> tuple[SQLiteRunStore, SQLiteFavoriteStore]:
    """Factory: shared connection for both stores (handy for T-Web wiring).

    Defaults to ``check_same_thread=False`` so FastAPI TestClient / local
    serve can touch the same connection from worker threads. Single-process
    local use only — not a multi-writer production pool.
    """
    conn = connect(db_path, check_same_thread=check_same_thread)
    return SQLiteRunStore(conn), SQLiteFavoriteStore(conn)
