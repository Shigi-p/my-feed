"""Ollama HTTP summarizer with on-demand article body fetch (M4-H)."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import httpx

from my_feed.models import Item
from my_feed.sources.http_util import get_text
from my_feed.summarizer.html_text import html_to_text

logger = logging.getLogger(__name__)

Fetcher = Callable[[str], str]


class OllamaSummarizer:
    """Ollama ``/api/generate`` による記事要約。

    Gemini と違い URL Context が無いため、要約時に記事 URL を GET して本文を抜く。
    取得失敗時は ``excerpt`` → タイトルのみにフォールバックする。
    失敗は例外を上げず ``None`` を返し、パイプラインを継続させる。
    """

    def __init__(
        self,
        *,
        model: str = "gemma4:e4b",
        base_url: str = "http://localhost:11434",
        timeout: float = 120.0,
        fetcher: Fetcher = get_text,
    ) -> None:
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._fetcher = fetcher

    def summarize(self, item: Item) -> str | None:
        """記事本文（またはフォールバック）を Ollama に渡して要約する。"""
        body = self._resolve_body(item)
        prompt = self._build_prompt(item, body)
        try:
            summary = self._generate(prompt)
        except Exception as exc:
            logger.warning(
                "Failed to summarize %s (%s) via ollama: %s: %s",
                item.id,
                item.url,
                type(exc).__name__,
                exc,
            )
            return None

        if not summary:
            logger.warning("Empty summary for %s", item.id)
            return None
        return summary

    def _resolve_body(self, item: Item) -> str:
        """Fetch and extract article text; fall back to excerpt / title."""
        try:
            html = self._fetcher(item.url)
            text = html_to_text(html)
            if text:
                return text
            logger.warning("Empty body extracted for %s; falling back", item.id)
        except Exception as exc:
            logger.warning(
                "Failed to fetch body for %s (%s): %s: %s",
                item.id,
                item.url,
                type(exc).__name__,
                exc,
            )

        excerpt = (item.excerpt or "").strip()
        if excerpt:
            return excerpt
        return item.title

    def _build_prompt(self, item: Item, body: str) -> str:
        parts = [
            "以下の技術記事を5-8行（300〜500文字程度）で要約してください。",
            "記事の主要なポイント、技術的な価値、対象読者、実用性を詳しくまとめてください。",
            "",
            f"タイトル: {item.title}",
        ]
        if item.tags:
            parts.append(f"タグ: {', '.join(item.tags)}")
        parts.extend(["", "本文:", body])
        return "\n".join(parts)

    def _generate(self, prompt: str) -> str:
        """Call Ollama generate API (non-streaming)."""
        url = f"{self._base_url}/api/generate"
        payload: dict[str, Any] = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
        }
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
        text = data.get("response", "")
        return text.strip() if isinstance(text, str) else ""
