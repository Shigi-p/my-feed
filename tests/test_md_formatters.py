"""Unit tests for T-Md excerpt / value_line / prompts helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from my_feed.models import Item, ScoredItem, SourceName
from my_feed.output.formatters import brainstorm_prompts, format_excerpt, strip_html, value_line


def _item(**kwargs) -> Item:
    now = datetime(2026, 10, 6, 3, 0, tzinfo=UTC)
    base = {
        "id": "zenn:1",
        "source": SourceName.ZENN,
        "title": "Rust で書く小さな CLI",
        "url": "https://example.com/a",
        "published_at": now - timedelta(hours=5),
        "excerpt": "本文抜粋",
        "tags": ["rust", "cli"],
        "fetched_at": now,
    }
    base.update(kwargs)
    return Item(**base)


def test_strip_html_and_entities():
    assert strip_html("") == ""
    assert strip_html("<p>Hello&nbsp;<b>world</b></p>") == "Hello world"
    assert strip_html("  a   \n  b ") == "a b"


def test_format_excerpt_empty_and_limit():
    assert format_excerpt("") == ""
    assert format_excerpt("<div></div>") == ""

    jp = "一文目。二文目。三文目。四文目。"
    out = format_excerpt(jp)
    assert out == "一文目。 二文目。 三文目。"
    assert "四文目" not in out

    long = "A" * 500
    clipped = format_excerpt(long, max_sentences=1, max_chars=50)
    assert clipped.endswith("…")
    assert len(clipped) <= 50


def test_format_excerpt_strips_html_before_split():
    raw = "<p>First sentence.</p><p>Second sentence.</p><p>Third sentence.</p><p>Fourth.</p>"
    out = format_excerpt(raw)
    assert "<" not in out
    assert "First sentence." in out
    assert "Fourth." not in out


def test_value_line_templates_and_empty_breakdown():
    now = datetime(2026, 10, 6, 3, 0, tzinfo=UTC)
    scored = ScoredItem(
        item=_item(published_at=now - timedelta(hours=3)),
        score=0.91,
        score_breakdown={"recency": 0.7, "pop": 0.4},
    )
    line = value_line(scored, now=now)
    assert "0.91" in line
    assert "Zenn" in line
    assert "時間" in line
    assert "recency" in line

    low = ScoredItem(
        item=_item(published_at=None, source=SourceName.QIITA, title="x"),
        score=0.2,
    )
    low_line = value_line(low, now=now)
    assert "補助枠" in low_line
    assert "Qiita" in low_line
    assert "不明" in low_line


def test_brainstorm_prompts_count_and_empty_title():
    prompts = brainstorm_prompts(_item())
    assert 2 <= len(prompts) <= 3
    assert all("Rust" in p for p in prompts)
    assert "rust, cli" in prompts[0]

    bare = brainstorm_prompts(_item(title="  ", tags=[]))
    assert len(bare) == 3
    assert all("この記事" in p for p in bare)
