"""GitHub Trending source adapter (isolated HTML scrape).

GitHub does not provide an official Trending API. This module scrapes
``https://github.com/trending`` and is intentionally isolated so HTML
breakage cannot affect other adapters' tests or imports beyond registry
wiring.

Fragility: fixtures freeze today's markup; production DOM drift will empty
or mis-parse until regexes are updated. Prefer keeping all HTML assumptions
inside this file only.
"""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from typing import Callable

from my_feed.ids import make_item_id
from my_feed.models import Item, SourceName
from my_feed.sources.http_util import get_text

logger = logging.getLogger(__name__)

GITHUB_TRENDING_URL = "https://github.com/trending"

_ARTICLE_RE = re.compile(r'<article class="Box-row">(.*?)</article>', re.S)
_HREF_RE = re.compile(r'<h2[^>]*>.*?href="(/[^"/]+/[^"/]+)"', re.S)
_STARS_RE = re.compile(r'href="(/[^"/]+/[^"/]+/stargazers)"[^>]*>\s*(.*?)\s*</a>', re.S)
_FORKS_RE = re.compile(r'href="(/[^"/]+/[^"/]+/forks)"[^>]*>\s*(.*?)\s*</a>', re.S)
_TODAY_RE = re.compile(
    r'([\d,]+)\s+stars?\s+today',
    re.I,
)
_LANG_RE = re.compile(r'itemprop="programmingLanguage"[^>]*>\s*([^<]+)')
_DESC_RE = re.compile(
    r'<p[^>]*class="[^"]*color-fg-muted[^"]*"[^>]*>\s*(.*?)\s*</p>',
    re.S,
)
_TAG_RE = re.compile(r"<[^>]+>")

Fetcher = Callable[..., str]


class GitHubTrendingSourceAdapter:
    """Scrape GitHub Trending repositories.

    Failures here raise and are caught by the pipeline; other sources continue.
    """

    def __init__(
        self,
        *,
        fetcher: Fetcher = get_text,
        url: str = GITHUB_TRENDING_URL,
    ) -> None:
        self._fetcher = fetcher
        self._url = url

    @property
    def name(self) -> SourceName:
        return SourceName.GITHUB_TRENDING

    def fetch(self) -> list[Item]:
        text = self._fetcher(
            self._url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (compatible; my-feed/0.1; "
                    "+https://github.com/shigi-p/my-feed)"
                ),
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        if not text.strip():
            raise RuntimeError("github_trending: empty HTML body")
        return parse_github_trending_html(text)


def parse_github_trending_html(
    html: str,
    *,
    fetched_at: datetime | None = None,
) -> list[Item]:
    """Parse trending page HTML into ``Item``s.

    Returns an empty list when the page has no repo articles (genuine zero).
    Per-article parse failures are skipped. Does not raise solely because
    zero articles were found — callers that need to treat "layout broken"
    differently should inspect fixtures / live HTML separately.
    """
    now = fetched_at or datetime.now(UTC)
    articles = _ARTICLE_RE.findall(html)
    items: list[Item] = []
    for block in articles:
        try:
            item = _parse_article(block, fetched_at=now)
        except Exception as exc:  # noqa: BLE001 — skip bad entries
            logger.warning("github_trending: skip entry: %s", exc)
            continue
        items.append(item)
    return items


def _parse_article(block: str, *, fetched_at: datetime) -> Item:
    href_m = _HREF_RE.search(block)
    if not href_m:
        raise ValueError("missing repo href")
    path = href_m.group(1)
    full_name = path.lstrip("/")
    if "/" not in full_name:
        raise ValueError(f"unexpected repo path: {path}")
    url = f"https://github.com/{full_name}"
    title = full_name

    metrics: dict[str, float | int] = {}
    stars_m = _STARS_RE.search(block)
    if stars_m:
        metrics["stars"] = _parse_int(stars_m.group(2))
    forks_m = _FORKS_RE.search(block)
    if forks_m:
        metrics["forks"] = _parse_int(forks_m.group(2))
    today_m = _TODAY_RE.search(_strip_tags(block))
    if today_m:
        metrics["stars_today"] = _parse_int(today_m.group(1))

    tags: list[str] = []
    lang_m = _LANG_RE.search(block)
    if lang_m:
        lang = lang_m.group(1).strip()
        if lang:
            tags.append(lang)

    excerpt = ""
    desc_m = _DESC_RE.search(block)
    if desc_m:
        excerpt = re.sub(r"\s+", " ", _strip_tags(desc_m.group(1))).strip()

    return Item(
        id=make_item_id(SourceName.GITHUB_TRENDING, official_id=full_name),
        source=SourceName.GITHUB_TRENDING,
        title=title,
        url=url,
        published_at=None,
        excerpt=excerpt,
        tags=tags,
        metrics=metrics,
        fetched_at=fetched_at,
    )


def _strip_tags(text: str) -> str:
    return _TAG_RE.sub("", text)


def _parse_int(raw: str) -> int:
    digits = re.sub(r"[^\d]", "", raw)
    if not digits:
        raise ValueError(f"not an int: {raw!r}")
    return int(digits)
