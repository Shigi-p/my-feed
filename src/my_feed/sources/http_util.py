"""Shared HTTP helpers for source adapters."""

from __future__ import annotations

import httpx

DEFAULT_TIMEOUT = 30.0
DEFAULT_HEADERS = {
    "User-Agent": "my-feed/0.1 (+https://github.com/shigi-p/my-feed)",
    "Accept": "*/*",
}


def get_text(
    url: str,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    headers: dict[str, str] | None = None,
    params: dict[str, str | int] | None = None,
) -> str:
    """GET ``url`` and return response text.

    Raises ``RuntimeError`` on transport or HTTP status failures so the
    pipeline can record ``source_errors`` for this source.
    """
    merged = {**DEFAULT_HEADERS, **(headers or {})}
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True, headers=merged) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            return response.text
    except httpx.HTTPError as exc:
        raise RuntimeError(f"fetch failed for {url}: {exc}") from exc
