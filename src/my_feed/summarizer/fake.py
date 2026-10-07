"""Fake summarizer for testing (no API required)."""

from __future__ import annotations

from my_feed.models import Item


class FakeSummarizer:
    """Test stub returning predictable summaries."""

    def summarize(self, item: Item) -> str | None:
        """Return a fake summary based on the title."""
        prefix = item.title[:50] if len(item.title) > 50 else item.title
        return f"[FAKE] {prefix}の要約です。テスト用の固定メッセージ。実際のAPI呼び出しは行われません。"
