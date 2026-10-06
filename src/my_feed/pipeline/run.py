"""Fetch → score → top N pipeline."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from my_feed.config import AppConfig
from my_feed.models import PipelineResult, PipelineStatus, ScoredItem
from my_feed.scoring import get_scorer
from my_feed.sources import get_source

logger = logging.getLogger(__name__)


def run_pipeline(config: AppConfig) -> PipelineResult:
    """Run enabled sources, score, and return top_n items.

    One source failing does not abort the others; errors go into
    ``source_errors``. If every source fails, status is ``error``.
    """
    fetched_at = datetime.now(UTC)
    source_errors: dict[str, str] = {}
    items = []

    for source_name in config.enabled_sources:
        try:
            adapter = get_source(source_name)
            items.extend(adapter.fetch())
        except Exception as exc:  # noqa: BLE001 — isolate per-source failures
            logger.warning("source %s failed: %s", source_name, exc)
            source_errors[source_name.value] = str(exc)

    if not items and source_errors:
        status = PipelineStatus.ERROR
        scored: list[ScoredItem] = []
        scorer_name = config.default_scorer
    elif not items:
        status = PipelineStatus.OK
        scored = []
        scorer_name = config.default_scorer
    else:
        strategy = get_scorer(config.default_scorer)
        scorer_name = strategy.name
        scored = strategy.score(items)[: config.top_n]
        status = PipelineStatus.PARTIAL if source_errors else PipelineStatus.OK

    return PipelineResult(
        items=scored,
        scorer=scorer_name,
        fetched_at=fetched_at,
        source_errors=source_errors,
        status=status,
    )
