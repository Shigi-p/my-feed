"""Tests for HTML → text extraction used by OllamaSummarizer."""

from __future__ import annotations

from my_feed.summarizer.html_text import html_to_text
from tests.helpers import fixture_text


def test_html_to_text_strips_blocks_and_tags() -> None:
    html = fixture_text("article_sample.html")
    text = html_to_text(html)

    assert "Rust で学ぶ非同期ランタイム" in text
    assert "Tokio" in text
    assert "バックプレッシャー" in text
    assert "window.track" not in text
    assert "display: none" not in text
    assert "Ignore this nav" not in text
    assert "Site Header Brand" not in text
    assert "関連記事リンク" not in text
    assert "Copyright 2026" not in text


def test_html_to_text_empty() -> None:
    assert html_to_text("") == ""
    assert html_to_text("   ") == ""


def test_html_to_text_truncates() -> None:
    html = "<p>" + ("あ" * 100) + "</p>"
    text = html_to_text(html, max_chars=50)
    assert len(text) == 50


def test_html_to_text_unescapes_entities() -> None:
    assert html_to_text("<p>A&nbsp;&amp;&nbsp;B</p>") == "A & B"
