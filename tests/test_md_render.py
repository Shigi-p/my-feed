"""Snapshot / integration tests for render_bundle and render_single."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from my_feed.models import Item, RenderMeta, ScoredItem, SourceName
from my_feed.output import render_bundle, render_single

SNAPSHOT_DIR = Path(__file__).parent / "snapshots"
# Snapshots lock prose + timestamps. Template wording changes require regenerating
# files under tests/snapshots/ — that brittleness is intentional for paste UX review.
FIXED_NOW = datetime(2026, 10, 6, 3, 15, tzinfo=UTC)


def _scored(
    n: int,
    *,
    source: SourceName = SourceName.ZENN,
    html_excerpt: bool = False,
    tags: list[str] | None = None,
) -> ScoredItem:
    excerpt = (
        f"<p>Excerpt {n} sentence one.</p><p>Sentence two.</p><p>Sentence three.</p>"
        if html_excerpt
        else f"Excerpt {n}. Second line. Third line."
    )
    item = Item(
        id=f"{source.value}:{n}",
        source=source,
        title=f"Sample article {n}",
        url=f"https://example.com/{n}",
        published_at=FIXED_NOW - timedelta(hours=n * 2),
        excerpt=excerpt,
        tags=["demo", "md"] if tags is None else tags,
        fetched_at=FIXED_NOW,
        metrics={"likes": 10 - n},
    )
    return ScoredItem(
        item=item,
        score=round(1.0 - n * 0.07, 2),
        score_breakdown={"recency": 0.6, "popularity": 0.3},
    )


def _assert_snapshot(name: str, actual: str) -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    path = SNAPSHOT_DIR / name
    if not path.exists():
        path.write_text(actual, encoding="utf-8")
    expected = path.read_text(encoding="utf-8")
    assert actual == expected, f"snapshot mismatch for {name}"


def test_render_bundle_snapshot_ten_items():
    items = [_scored(i, html_excerpt=(i == 1)) for i in range(1, 11)]
    items[2] = _scored(3, tags=[])  # omit tags row
    meta = RenderMeta(
        generated_at=FIXED_NOW,
        scorer="hybrid",
        count=10,
        intro=None,
    )
    md = render_bundle(items, meta)
    assert md.startswith("# my feed — ")
    assert "- scorer: hybrid" in md
    assert "- count: 10" in md
    assert "### 抜粋" in md
    assert "### なぜ今見るか" in md
    assert "### 壁打ちの問い" in md
    assert "Gemini への貼り付け" in md
    assert "<p>" not in md
    _assert_snapshot("bundle_ten.md", md)


def test_render_single_snapshot():
    item = _scored(1, source=SourceName.QIITA)
    meta = RenderMeta(generated_at=FIXED_NOW, scorer="hybrid", count=1)
    md = render_single(item, meta)
    assert "## Sample article 1" in md
    assert "- count: 1" in md
    assert "1. " in md  # numbered prompts
    _assert_snapshot("single_one.md", md)


def test_render_empty_bundle_does_not_crash():
    meta = RenderMeta(generated_at=FIXED_NOW, scorer="fake", count=0, intro="")
    md = render_bundle([], meta)
    assert "（項目なし）" in md
    assert md.endswith("\n")


def test_render_item_without_excerpt_or_title():
    item = Item(
        id="fake:empty",
        source=SourceName.FAKE,
        title="",
        url="https://example.com/empty",
        excerpt="",
        fetched_at=FIXED_NOW,
    )
    scored = ScoredItem(item=item, score=0.0)
    meta = RenderMeta(generated_at=FIXED_NOW, scorer="fake", count=1, intro="custom intro")
    md = render_single(scored, meta)
    assert "(無題)" in md
    assert "（抜粋なし）" in md
    assert "custom intro" in md
