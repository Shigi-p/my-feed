"""Qiita source adapter — public API v2 (no token for public GET)."""

from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from typing import Any, Callable

from my_feed.ids import make_item_id
from my_feed.models import Item, SourceName
from my_feed.sources.http_util import get_text
from my_feed.sources.time_util import parse_datetime

logger = logging.getLogger(__name__)

QIITA_ITEMS_URL = "https://qiita.com/api/v2/items"
_TAG_RE = re.compile(r"<[^>]+>")

Fetcher = Callable[..., str]


class QiitaSourceAdapter:
    """Fetch recent public Qiita items via API v2.

    Public GET does not require a token. Rate limits apply (stricter without
    auth); this adapter requests a single page only.
    """

    def __init__(
        self,
        *,
        fetcher: Fetcher = get_text,
        page: int = 1,
        per_page: int = 20,
    ) -> None:
        self._fetcher = fetcher
        self._page = page
        self._per_page = per_page

    @property
    def name(self) -> SourceName:
        return SourceName.QIITA

    def fetch(self) -> list[Item]:
        text = self._fetcher(
            QIITA_ITEMS_URL,
            params={"page": self._page, "per_page": self._per_page},
        )
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"qiita: invalid JSON: {exc}") from exc
        if not isinstance(payload, list):
            raise RuntimeError("qiita: unexpected payload shape (expected list)")
        return parse_qiita_items(payload)


def parse_qiita_items(
    payload: list[Any],
    *,
    fetched_at: datetime | None = None,
) -> list[Item]:
    """Normalize a Qiita ``/api/v2/items`` JSON list to ``Item``s."""
    now = fetched_at or datetime.now(UTC)
    items: list[Item] = []
    for raw in payload:
        try:
            item = _parse_one(raw, fetched_at=now)
        except Exception as exc:  # noqa: BLE001 — skip bad entries
            logger.warning("qiita: skip entry: %s", exc)
            continue
        items.append(item)
    return items


def _parse_one(raw: Any, *, fetched_at: datetime) -> Item:
    if not isinstance(raw, dict):
        raise ValueError("entry is not an object")
    title = (raw.get("title") or "").strip()
    url = (raw.get("url") or "").strip()
    official_id = raw.get("id")
    if not title:
        raise ValueError("missing title")
    if not url:
        raise ValueError("missing url")
    if not official_id:
        raise ValueError("missing id")

    tags: list[str] = []
    for tag in raw.get("tags") or []:
        if isinstance(tag, dict) and tag.get("name"):
            tags.append(str(tag["name"]))
        elif isinstance(tag, str) and tag:
            tags.append(tag)

    metrics: dict[str, float | int] = {}
    if raw.get("likes_count") is not None:
        metrics["likes"] = int(raw["likes_count"])
    if raw.get("stocks_count") is not None:
        metrics["stocks"] = int(raw["stocks_count"])

    excerpt = _excerpt(raw.get("body") or raw.get("rendered_body") or "")

    return Item(
        id=make_item_id(SourceName.QIITA, official_id=str(official_id)),
        source=SourceName.QIITA,
        title=title,
        url=url,
        published_at=parse_datetime(raw.get("created_at")),
        excerpt=excerpt,
        tags=tags,
        metrics=metrics,
        fetched_at=fetched_at,
    )


def _excerpt(body: str, limit: int = 200) -> str:
    text = _TAG_RE.sub("", body)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"
