"""Integration test for summarizer in pipeline."""

import pytest

from my_feed.config import AppConfig
from my_feed.models import SourceName
from my_feed.pipeline import run_pipeline


def test_pipeline_with_summarizer_enabled_without_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pipeline runs with summarizer enabled (uses Gemini by default)."""
    config = AppConfig(
        top_n=3,
        default_scorer="fake",
        enabled_sources=[SourceName.FAKE],
    )
    # config.py の load_dotenv() が .env のキーを読むため、明示的に消して実 API 呼び出しを防ぐ
    monkeypatch.delenv(config.summarizer.api_key_env, raising=False)
    # Note: with summarizer enabled but no API key, _build_summarizer returns None
    # So summaries won't actually be generated, but pipeline should not crash
    config.summarizer.enabled = True

    # Run pipeline - should not crash even with summarizer enabled
    result = run_pipeline(config)

    assert result.status.value == "ok"
    assert len(result.items) <= 3

    # Without API key, summaries won't be generated
    for scored_item in result.items:
        assert scored_item.summary is None


def test_pipeline_with_summarizer_disabled() -> None:
    """Pipeline works with summarizer disabled (default for fake sources)."""
    config = AppConfig(
        top_n=3,
        default_scorer="fake",
        enabled_sources=[SourceName.FAKE],
    )
    config.summarizer.enabled = False

    result = run_pipeline(config)

    assert result.status.value == "ok"
    assert len(result.items) <= 3

    # No summaries should be generated
    for scored_item in result.items:
        assert scored_item.summary is None
