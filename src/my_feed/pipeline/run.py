"""Fetch → score → summarize → top N pipeline."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from my_feed.config import AppConfig
from my_feed.models import PipelineResult, PipelineStatus, ScoredItem
from my_feed.scoring import build_scorer
from my_feed.sources import get_source
from my_feed.summarizer import GeminiSummarizer, OllamaSummarizer, SummarizerAdapter

logger = logging.getLogger(__name__)


def _build_summarizer(config: AppConfig) -> SummarizerAdapter | None:
    """設定から summarizer を構築。無効または利用不可の場合は None。"""
    if not config.summarizer.enabled:
        return None

    if config.summarizer.get_backend() == "ollama":
        # 未起動でも各 summarize() が None を返すだけ。Gemini へは落とさない
        return OllamaSummarizer(
            model=config.summarizer.ollama_model,
            base_url=config.summarizer.ollama.base_url,
            timeout=config.summarizer.ollama.timeout,
        )

    api_key = config.summarizer.get_api_key()
    if not api_key:
        logger.warning(
            f"Summarizer enabled but {config.summarizer.api_key_env} not set. "
            f"Summaries will be skipped. "
            f"To enable: create .env file with '{config.summarizer.api_key_env}=your-key' "
            f"or export {config.summarizer.api_key_env}=your-key"
        )
        return None

    return GeminiSummarizer(
        api_key=api_key,
        model=config.summarizer.model,
    )


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
            logger.info(f"Summarizing {len(scored)} items with {config.summarizer.get_backend()}")
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
