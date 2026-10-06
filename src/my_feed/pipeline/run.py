"""Fetch → score → summarize → top N pipeline."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from my_feed.config import AppConfig
from my_feed.models import PipelineResult, PipelineStatus, ScoredItem
from my_feed.scoring import build_scorer
from my_feed.sources import get_source
from my_feed.summarizer import FakeSummarizer, GeminiSummarizer, SummarizerAdapter

logger = logging.getLogger(__name__)


def _build_summarizer(config: AppConfig) -> SummarizerAdapter | None:
    """Build a summarizer from config, or None if disabled/unavailable."""
    if not config.summarizer.enabled:
        return None

    api_key = config.summarizer.get_api_key()
    if not api_key:
        logger.warning(
            f"Summarizer enabled but {config.summarizer.api_key_env} not set. "
            f"Summaries will be skipped."
        )
        return None

    if config.summarizer.provider == "gemini":
        return GeminiSummarizer(
            api_key=api_key,
            model=config.summarizer.model,
            temperature=config.summarizer.temperature,
            max_output_tokens=config.summarizer.max_output_tokens,
        )

    logger.warning(f"Unknown summarizer provider: {config.summarizer.provider}")
    return None


def _mask_api_key(key: str | None) -> str:
    """Mask API key for logging."""
    if not key:
        return "(not set)"
    return f"{key[:8]}...{key[-4:]}" if len(key) > 12 else "***"


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
        # build_scorer (not get_scorer) so config.toml half-life / neutrals apply.
        strategy = build_scorer(config.default_scorer, config)
        scorer_name = strategy.name
        scored = strategy.score(items)[: config.top_n]
        status = PipelineStatus.PARTIAL if source_errors else PipelineStatus.OK

        # Summarize top N items (M4-D)
        summarizer = _build_summarizer(config)
        if summarizer:
            logger.info(f"Summarizing {len(scored)} items with {config.summarizer.provider}")
            for scored_item in scored:
                summary = summarizer.summarize(scored_item.item)
                scored_item.summary = summary

    return PipelineResult(
        items=scored,
        scorer=scorer_name,
        fetched_at=fetched_at,
        source_errors=source_errors,
        status=status,
    )
