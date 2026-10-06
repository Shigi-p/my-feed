"""Shared domain models (C0 contracts)."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class SourceName(StrEnum):
    """Known feed sources.

    Real adapters (T-Src) register under these names. ``fake`` exists only
    for C0 / tests and should not appear in production configs after M1.
    """

    ZENN = "zenn"
    QIITA = "qiita"
    GIGAZINE = "gigazine"
    GITHUB_TRENDING = "github_trending"
    FAKE = "fake"


class PipelineStatus(StrEnum):
    OK = "ok"
    PARTIAL = "partial"
    ERROR = "error"


class Item(BaseModel):
    """Normalized content unit produced by a SourceAdapter."""

    id: str
    source: SourceName
    title: str
    url: str
    published_at: datetime | None = None
    excerpt: str = ""
    tags: list[str] = Field(default_factory=list)
    metrics: dict[str, float | int] = Field(default_factory=dict)
    fetched_at: datetime


class ScoredItem(BaseModel):
    """An Item with a cross-source comparable score."""

    item: Item
    score: float
    score_breakdown: dict[str, float] = Field(default_factory=dict)


class PipelineResult(BaseModel):
    """Output of ``run_pipeline``."""

    items: list[ScoredItem]
    scorer: str
    fetched_at: datetime
    source_errors: dict[str, str] = Field(default_factory=dict)
    status: PipelineStatus


class RenderMeta(BaseModel):
    """Metadata passed to markdown renderers."""

    generated_at: datetime
    scorer: str
    count: int
    intro: str | None = None


# Convenience alias for JSON-ish payloads stored by T-Store later.
JsonDict = dict[str, Any]

# Pydantic may coerce URLs; adapters may also keep plain strings.
UrlLike = str | HttpUrl
