"""Markdown renderer contracts (implemented fully in T-Md)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from my_feed.models import RenderMeta, ScoredItem


@runtime_checkable
class MarkdownRenderer(Protocol):
    def render_bundle(self, items: list[ScoredItem], meta: RenderMeta) -> str: ...

    def render_single(self, item: ScoredItem, meta: RenderMeta) -> str: ...


def render_bundle(items: list[ScoredItem], meta: RenderMeta) -> str:
    """C0 stub: minimal markdown so Web/CLI can wire downloads early."""
    lines = [
        f"# my feed — {meta.generated_at.isoformat()}",
        f"- scorer: {meta.scorer}",
        f"- count: {meta.count}",
        "",
    ]
    if meta.intro:
        lines.extend([meta.intro, ""])
    for i, scored in enumerate(items, start=1):
        item = scored.item
        lines.extend(
            [
                f"## {i}. {item.title}",
                f"- source: {item.source.value}",
                f"- url: {item.url}",
                f"- score: {scored.score:.2f}",
                "",
                item.excerpt or "（抜粋なし）",
                "",
                "---",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def render_single(item: ScoredItem, meta: RenderMeta) -> str:
    """C0 stub for a single-item paste template."""
    return render_bundle([item], meta.model_copy(update={"count": 1}))
