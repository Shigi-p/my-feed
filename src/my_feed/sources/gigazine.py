"""GIGAZINE source adapter — site RSS (no filtering; that is M3)."""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import feedparser

from my_feed.ids import make_item_id
from my_feed.models import Item, SourceName
from my_feed.sources.http_util import get_text
from my_feed.sources.time_util import parse_datetime

logger = logging.getLogger(__name__)

GIGAZINE_RSS_URL = "https://gigazine.net/news/rss_2.0/"
_TAG_RE = re.compile(r"<[^>]+>")
_SLUG_RE = re.compile(r"/news/([^/]+)/?")

Fetcher = Callable[..., str]


class GigazineSourceAdapter:
    """Fetch GIGAZINE headlines via the official RSS 2.0 feed.

    No topic filter here — filtering belongs to later ops (M3).
    """

    def __init__(self, *, fetcher: Fetcher = get_text, url: str = GIGAZINE_RSS_URL) -> None:
        self._fetcher = fetcher
        self._url = url

    @property
    def name(self) -> SourceName:
        return SourceName.GIGAZINE

    def fetch(self) -> list[Item]:
        text = self._fetcher(self._url)
        if not text.strip():
            raise RuntimeError("gigazine: empty RSS body")
        return parse_gigazine_rss(text)


def parse_gigazine_rss(
    xml_text: str,
    *,
    fetched_at: datetime | None = None,
) -> list[Item]:
    """Parse GIGAZINE RSS XML into ``Item``s; skip broken entries."""
    now = fetched_at or datetime.now(UTC)
    feed = feedparser.parse(xml_text)
    # feedparser sets bozo on minor XML quirks; only fail if we got nothing
    # *and* a hard parse problem with no entries at all from empty/garbage.
    if not feed.entries and getattr(feed, "bozo", False):
        bozo_exc = getattr(feed, "bozo_exception", None)
        # Truly empty-but-valid channel is OK (returns []). Garbage raises.
        if not _looks_like_rss(xml_text):
            raise RuntimeError(f"gigazine: RSS parse failed: {bozo_exc}")

    items: list[Item] = []
    for raw in feed.entries:
        try:
            item = _parse_one(raw, fetched_at=now)
        except Exception as exc:  # noqa: BLE001 — skip bad entries
            logger.warning("gigazine: skip entry: %s", exc)
            continue
        items.append(item)
    return items


def _looks_like_rss(text: str) -> bool:
    lower = text[:500].lower()
    return "<rss" in lower or "<feed" in lower or "<channel" in lower


def _parse_one(raw: Any, *, fetched_at: datetime) -> Item:
    title = (getattr(raw, "title", None) or "").strip()
    url = (getattr(raw, "link", None) or "").strip()
    if not title:
        raise ValueError("missing title")
    if not url:
        raise ValueError("missing url")

    official = _official_id(raw, url)
    published = parse_datetime(getattr(raw, "published", None)) or parse_datetime(
        getattr(raw, "published_parsed", None)
    )

    tags: list[str] = []
    for tag in getattr(raw, "tags", None) or []:
        term = getattr(tag, "term", None) if not isinstance(tag, dict) else tag.get("term")
        if term:
            cleaned = str(term).strip().rstrip(",")
            if cleaned:
                tags.append(cleaned)

    summary = getattr(raw, "summary", None) or ""
    excerpt = _excerpt(str(summary))

    return Item(
        id=make_item_id(
            SourceName.GIGAZINE,
            official_id=official,
            url=None if official else url,
        ),
        source=SourceName.GIGAZINE,
        title=title,
        url=url,
        published_at=published,
        excerpt=excerpt,
        tags=tags,
        metrics={},
        fetched_at=fetched_at,
    )


def _official_id(raw: Any, url: str) -> str | None:
    """Stable key from URL/guid slug (``/news/<slug>/``).

    Favorites depend on this staying stable across refetches. If GIGAZINE
    changes URL shape, slug extraction may yield a new id and orphan saves.
    """
    guid = getattr(raw, "id", None) or getattr(raw, "guid", None)
    if isinstance(guid, str) and guid.strip():
        match = _SLUG_RE.search(guid)
        if match:
            return match.group(1)
    match = _SLUG_RE.search(url)
    if match:
        return match.group(1)
    return None


def _excerpt(html: str, limit: int = 200) -> str:
    text = _TAG_RE.sub("", html)
    text = re.sub(r"\s+", " ", text).strip()
    # Drop the trailing "続きを読む..." CTA if present
    text = re.sub(r"続きを読む\.{0,3}$", "", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"
