"""Injectable dependencies for the web app (M2: SQLite + config-aware defaults)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from my_feed.config import AppConfig, load_config, resolve_config_path
from my_feed.models import PipelineResult, RenderMeta, ScoredItem
from my_feed.output import render_bundle, render_single
from my_feed.pipeline import run_pipeline
from my_feed.scoring import list_scorers
from my_feed.store import (
    DEFAULT_DB_PATH,
    FavoriteStore,
    RunStore,
    open_sqlite_stores,
)

PipelineFn = Callable[[AppConfig], PipelineResult]
RenderBundleFn = Callable[[list[ScoredItem], RenderMeta], str]
RenderSingleFn = Callable[[ScoredItem, RenderMeta], str]
LoadConfigFn = Callable[[Path | None], AppConfig]
ListScorersFn = Callable[[], list[str]]


@dataclass
class WebDeps:
    """Composition root for the local Web UI.

    Production defaults (see ``create_default_web_deps``) use SQLite and the
    resolved config path. Tests inject in-memory stores and a fixed config.
    """

    run_store: RunStore
    favorite_store: FavoriteStore
    run_pipeline_fn: PipelineFn = field(default=run_pipeline)
    render_bundle_fn: RenderBundleFn = field(default=render_bundle)
    render_single_fn: RenderSingleFn = field(default=render_single)
    load_config_fn: LoadConfigFn = field(default=load_config)
    list_scorers_fn: ListScorersFn = field(default=list_scorers)
    config_path: Path = field(default_factory=resolve_config_path)
    db_path: Path = field(default_factory=lambda: DEFAULT_DB_PATH)


def create_default_web_deps(
    *,
    config_path: Path | None = None,
    db_path: Path | str | None = None,
) -> WebDeps:
    """Wire SQLite stores + config resolution for ``my-feed serve``."""
    resolved_config = config_path if config_path is not None else resolve_config_path()
    resolved_db = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    # Shared connection; local single-process uvicorn keeps requests on one thread.
    run_store, favorite_store = open_sqlite_stores(resolved_db)
    return WebDeps(
        run_store=run_store,
        favorite_store=favorite_store,
        config_path=resolved_config,
        db_path=resolved_db,
    )
