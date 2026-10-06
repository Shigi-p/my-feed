"""Zenn source adapter — public JSON API (likes included).

Fetch path trade-off: Zenn RSS omits like counts, so we use the unofficial
web JSON API (``/api/articles``) that the Zenn site itself calls. That buys
``liked_count`` for scoring at the cost of higher breakage / ToS risk than
RSS. If the API disappears, fall back to RSS and accept empty metrics.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any, Callable

from my_feed.ids import make_item_id
from my_feed.models import Item, SourceName
from my_feed.sources.http_util import get_text
from my_feed.sources.time_util import parse_datetime

logger = logging.getLogger(__name__)

# Unofficial but public list API used by the Zenn web app.
# ``order=daily`` approximates the trending surface; likes come as liked_count.
ZENN_ARTICLES_URL = "https://zenn.dev/api/articles"

Fetcher = Callable[..., str]


class ZennSourceAdapter:
    """Fetch recent/daily Zenn articles via the public articles API."""

    def __init__(
        self,
        *,
        fetcher: Fetcher = get_text,
        order: str = "daily",
        page: int = 1,
    ) -> None:
        self._fetcher = fetcher
        self._order = order
        self._page = page

    @property
    def name(self) -> SourceName:
        return SourceName.ZENN

    def fetch(self) -> list[Item]:
        text = self._fetcher(
            ZENN_ARTICLES_URL,
            params={"order": self._order, "page": self._page},
        )
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"zenn: invalid JSON: {exc}") from exc
        if not isinstance(payload, dict) or "articles" not in payload:
            raise RuntimeError("zenn: unexpected payload shape (missing articles)")
        return parse_zenn_articles(payload)


def parse_zenn_articles(
    payload: dict[str, Any],
    *,
    fetched_at: datetime | None = None,
) -> list[Item]:
    """Normalize a Zenn articles API payload to ``Item`` list.

    Per-entry failures are skipped; an empty ``articles`` list yields ``[]``.
    """
    now = fetched_at or datetime.now(UTC)
    raw_articles = payload.get("articles")
    if raw_articles is None:
        raise RuntimeError("zenn: missing articles key")
    if not isinstance(raw_articles, list):
        raise RuntimeError("zenn: articles must be a list")

    items: list[Item] = []
    for raw in raw_articles:
        try:
            item = _parse_one(raw, fetched_at=now)
        except Exception as exc:  # noqa: BLE001 — skip bad entries
            logger.warning("zenn: skip entry: %s", exc)
            continue
        items.append(item)
    return items


def _parse_one(raw: Any, *, fetched_at: datetime) -> Item:
    if not isinstance(raw, dict):
        raise ValueError("entry is not an object")
    path = raw.get("path")
    title = (raw.get("title") or "").strip()
    official_id = raw.get("id")
    if not title:
        raise ValueError("missing title")
    if not path or not isinstance(path, str):
        raise ValueError("missing path")
    url = f"https://zenn.dev{path}" if path.startswith("/") else path
    if official_id is None:
        raise ValueError("missing id")

    tags: list[str] = []
    article_type = raw.get("article_type")
    if isinstance(article_type, str) and article_type:
        tags.append(article_type)

    metrics: dict[str, float | int] = {}
    if "liked_count" in raw and raw["liked_count"] is not None:
        metrics["likes"] = int(raw["liked_count"])
    if "bookmarked_count" in raw and raw["bookmarked_count"] is not None:
        metrics["bookmarks"] = int(raw["bookmarked_count"])

    return Item(
        id=make_item_id(SourceName.ZENN, official_id=str(official_id)),
        source=SourceName.ZENN,
        title=title,
        url=url,
        published_at=parse_datetime(raw.get("published_at")),
        excerpt="",
        tags=tags,
        metrics=metrics,
        fetched_at=fetched_at,
    )
