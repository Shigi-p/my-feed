"""Test summarizer protocol and fake implementation."""

from __future__ import annotations

from datetime import UTC, datetime

from my_feed.models import Item, SourceName
from my_feed.summarizer import FakeSummarizer, SummarizerAdapter


def test_fake_summarizer_protocol() -> None:
    """FakeSummarizer satisfies the SummarizerAdapter protocol."""
    summarizer: SummarizerAdapter = FakeSummarizer()
    item = Item(
        id="test:1",
        source=SourceName.FAKE,
        title="テスト記事のタイトル",
        url="https://example.com/article",
        fetched_at=datetime.now(UTC),
    )
    summary = summarizer.summarize(item)
    assert summary is not None
    assert "テスト記事のタイトル" in summary
    assert "[FAKE]" in summary


def test_fake_summarizer_handles_long_title() -> None:
    """FakeSummarizer truncates long titles."""
    summarizer = FakeSummarizer()
    long_title = "あ" * 100
    item = Item(
        id="test:long",
        source=SourceName.FAKE,
        title=long_title,
        url="https://example.com/long",
        fetched_at=datetime.now(UTC),
    )
    summary = summarizer.summarize(item)
    assert summary is not None
    assert len(summary) < len(long_title) + 50  # truncated + message
