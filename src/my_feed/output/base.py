"""Markdown renderer contracts (Protocol only).

Implementations live in ``output.markdown`` (C0 stub now; T-Md replaces body).
Keep this module free of rendering logic so ``base`` means “interface”,
matching ``sources`` / ``scoring``.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from my_feed.models import RenderMeta, ScoredItem


@runtime_checkable
class MarkdownRenderer(Protocol):
    def render_bundle(self, items: list[ScoredItem], meta: RenderMeta) -> str: ...

    def render_single(self, item: ScoredItem, meta: RenderMeta) -> str: ...
