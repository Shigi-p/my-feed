"""Rule-based markdown renderers for Gemini / ChatGPT paste (T-Md).

Excerpt / value-line helpers live in ``formatters``. Some SourceAdapters
(especially GIGAZINE) already strip HTML into ``Item.excerpt`` — we still run
``format_excerpt`` here so paste length stays consistent. Prefer improving
formatters rather than diverging adapter-side truncation rules.
"""

from __future__ import annotations

from datetime import datetime

from my_feed.models import RenderMeta, ScoredItem
from my_feed.output.formatters import (
    DEFAULT_GEMINI_INTRO,
    brainstorm_prompts,
    format_excerpt,
    format_generated_at,
    value_line,
)


def _render_item_block(scored: ScoredItem, *, index: int | None, now: datetime) -> list[str]:
    item = scored.item
    title = item.title.strip() if item.title else "(無題)"
    heading = f"## {index}. {title}" if index is not None else f"## {title}"

    lines = [
        heading,
        f"- source: {item.source.value}",
        f"- url: {item.url}",
        f"- score: {scored.score:.2f}",
    ]
    if item.tags:
        lines.append(f"- tags: {', '.join(item.tags)}")

    lines.append("")

    # AI要約（M4-D）
    if scored.summary:
        lines.extend(
            [
                "### AI要約",
                scored.summary,
                "",
            ]
        )

    excerpt = format_excerpt(item.excerpt)
    lines.extend(
        [
            "### 抜粋",
            excerpt if excerpt else "（抜粋なし）",
            "",
            "### なぜ今見るか",
            value_line(scored, now=now),
            "",
            "### 壁打ちの問い",
        ]
    )
    for i, prompt in enumerate(brainstorm_prompts(item), start=1):
        lines.append(f"{i}. {prompt}")
    lines.extend(["", "---", ""])
    return lines


def render_bundle(items: list[ScoredItem], meta: RenderMeta) -> str:
    """Bundle markdown for Gemini/ChatGPT paste (rule-based, no LLM)."""
    count = meta.count if meta.count else len(items)
    lines = [
        f"# my feed — {format_generated_at(meta.generated_at)}",
        f"- scorer: {meta.scorer}",
        f"- count: {count}",
        "",
    ]
    intro = meta.intro if meta.intro is not None else DEFAULT_GEMINI_INTRO
    if intro:
        lines.extend([intro, ""])

    if not items:
        lines.extend(["（項目なし）", ""])
    else:
        for i, scored in enumerate(items, start=1):
            lines.extend(_render_item_block(scored, index=i, now=meta.generated_at))

    lines.extend(
        [
            "## Gemini への貼り付け",
            "気になる番号を指定して「要約 → 反論 → 最小実験」の順で壁打ちしてください。",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_single(item: ScoredItem, meta: RenderMeta) -> str:
    """Single-item paste template (same sections as bundle, one article)."""
    lines = [
        f"# my feed — {format_generated_at(meta.generated_at)}",
        f"- scorer: {meta.scorer}",
        "- count: 1",
        "",
    ]
    intro = meta.intro if meta.intro is not None else DEFAULT_GEMINI_INTRO
    if intro:
        lines.extend([intro, ""])

    lines.extend(_render_item_block(item, index=None, now=meta.generated_at))
    lines.extend(
        [
            "## Gemini への貼り付け",
            "上の問いを順に投げ、自分の文脈に合わせて深掘りしてください。",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"
