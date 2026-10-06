"""Injectable dependencies for the web app (Fake now; M2 swaps wiring)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from my_feed.config import AppConfig, load_config
from my_feed.models import PipelineResult, RenderMeta, ScoredItem
from my_feed.output import render_bundle, render_single
from my_feed.pipeline import run_pipeline
from my_feed.scoring import list_scorers
from my_feed.store import FavoriteStore, InMemoryFavoriteStore, InMemoryRunStore, RunStore

PipelineFn = Callable[[AppConfig], PipelineResult]
RenderBundleFn = Callable[[list[ScoredItem], RenderMeta], str]
RenderSingleFn = Callable[[ScoredItem, RenderMeta], str]
LoadConfigFn = Callable[[Path | None], AppConfig]
ListScorersFn = Callable[[], list[str]]


@dataclass
class WebDeps:
    """Composition root for T-Web. M2 replaces store/renderer/pipeline here."""

    run_store: RunStore = field(default_factory=InMemoryRunStore)
    favorite_store: FavoriteStore = field(default_factory=InMemoryFavoriteStore)
    run_pipeline_fn: PipelineFn = field(default=run_pipeline)
    render_bundle_fn: RenderBundleFn = field(default=render_bundle)
    render_single_fn: RenderSingleFn = field(default=render_single)
    load_config_fn: LoadConfigFn = field(default=load_config)
    list_scorers_fn: ListScorersFn = field(default=list_scorers)
    config_path: Path = field(default_factory=lambda: Path("config.toml"))
