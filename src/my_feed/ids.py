"""Stable ID helpers for Items."""

from __future__ import annotations

import hashlib
from urllib.parse import urlsplit, urlunsplit

from my_feed.models import SourceName


def normalize_url(url: str) -> str:
    """Normalize a URL enough for stable hashing (scheme/host/path/query)."""
    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower()
    netloc = parts.netloc.lower()
    path = parts.path.rstrip("/") or ""
    return urlunsplit((scheme, netloc, path, parts.query, ""))


def make_item_id(source: SourceName, *, official_id: str | None = None, url: str | None = None) -> str:
    """Build ``{source}:{stable_key}``.

    Prefer an official ID when the upstream provides one; otherwise hash the
    normalized URL (12 hex chars).
    """
    if official_id:
        return f"{source.value}:{official_id}"
    if not url:
        raise ValueError("either official_id or url is required")
    digest = hashlib.sha256(normalize_url(url).encode("utf-8")).hexdigest()[:12]
    return f"{source.value}:url:{digest}"
