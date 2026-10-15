"""HTML → plain text for local LLM summarization (no BeautifulSoup)."""

from __future__ import annotations

import html
import re

# Drop non-content blocks before tag stripping.
_BLOCK_RE = re.compile(
    r"<(script|style|nav|header|footer|aside|noscript)\b[^>]*>.*?</\1>",
    re.IGNORECASE | re.DOTALL,
)
_TAG_RE = re.compile(r"<[^>]+>", re.DOTALL)
_WS_RE = re.compile(r"\s+")

# Soft upper bound for Ollama prompt body (plan: 500–2000).
DEFAULT_MAX_CHARS = 2000


def html_to_text(raw: str, *, max_chars: int = DEFAULT_MAX_CHARS) -> str:
    """Extract readable article text from HTML.

    Removes script/style/nav-like blocks, strips remaining tags, unescapes
    entities, collapses whitespace, and truncates to ``max_chars``.
    """
    if not raw:
        return ""
    cleaned = _BLOCK_RE.sub(" ", raw)
    plain = _TAG_RE.sub(" ", cleaned)
    plain = html.unescape(plain)
    plain = _WS_RE.sub(" ", plain).strip()
    if max_chars > 0 and len(plain) > max_chars:
        return plain[:max_chars].rstrip()
    return plain
