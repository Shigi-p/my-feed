"""Unit tests for OllamaSummarizer (httpx mocked; no live Ollama)."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import httpx
import pytest

from my_feed.models import Item, SourceName
from my_feed.summarizer import OllamaSummarizer, SummarizerAdapter
from tests.helpers import fixture_text


def _item(*, excerpt: str = "", title: str = "テスト記事") -> Item:
    return Item(
        id="test:1",
        source=SourceName.FAKE,
        title=title,
        url="https://example.com/article",
        excerpt=excerpt,
        tags=["rust", "async"],
        fetched_at=datetime.now(UTC),
    )


def test_ollama_summarizer_protocol() -> None:
    summarizer: SummarizerAdapter = OllamaSummarizer(fetcher=lambda _url: "<p>hi</p>")
    assert hasattr(summarizer, "summarize")


def test_summarize_success_with_fetched_body() -> None:
    html = fixture_text("article_sample.html")

    def fetcher(_url: str) -> str:
        return html

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"response": "これは要約です。"}

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None
    mock_client.post.return_value = mock_response

    with patch("my_feed.summarizer.ollama.httpx.Client", return_value=mock_client):
        summary = OllamaSummarizer(fetcher=fetcher).summarize(_item())

    assert summary == "これは要約です。"
    args, kwargs = mock_client.post.call_args
    assert args[0] == "http://localhost:11434/api/generate"
    payload = kwargs["json"]
    assert payload["model"] == "gemma4:e4b"
    assert payload["stream"] is False
    assert "Tokio" in payload["prompt"]
    assert "テスト記事" in payload["prompt"]
    assert "rust" in payload["prompt"]


def test_summarize_falls_back_to_excerpt_on_fetch_error() -> None:
    def fetcher(_url: str) -> str:
        raise RuntimeError("fetch failed")

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"response": "excerpt要約"}

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None
    mock_client.post.return_value = mock_response

    with patch("my_feed.summarizer.ollama.httpx.Client", return_value=mock_client):
        summary = OllamaSummarizer(fetcher=fetcher).summarize(_item(excerpt="短い抜粋テキスト"))

    assert summary == "excerpt要約"
    prompt = mock_client.post.call_args.kwargs["json"]["prompt"]
    assert "短い抜粋テキスト" in prompt


def test_summarize_falls_back_to_title_when_no_excerpt() -> None:
    def fetcher(_url: str) -> str:
        raise RuntimeError("fetch failed")

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"response": "title要約"}

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None
    mock_client.post.return_value = mock_response

    with patch("my_feed.summarizer.ollama.httpx.Client", return_value=mock_client):
        summary = OllamaSummarizer(fetcher=fetcher).summarize(_item(title="タイトルのみ"))

    assert summary == "title要約"
    prompt = mock_client.post.call_args.kwargs["json"]["prompt"]
    assert "タイトルのみ" in prompt


def test_summarize_returns_none_on_api_error() -> None:
    def fetcher(_url: str) -> str:
        return "<p>body</p>"

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None
    mock_client.post.side_effect = httpx.ConnectError("connection refused")

    with patch("my_feed.summarizer.ollama.httpx.Client", return_value=mock_client):
        summary = OllamaSummarizer(fetcher=fetcher).summarize(_item())

    assert summary is None


def test_summarize_returns_none_on_empty_response() -> None:
    def fetcher(_url: str) -> str:
        return "<p>body</p>"

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"response": "  "}

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = None
    mock_client.post.return_value = mock_response

    with patch("my_feed.summarizer.ollama.httpx.Client", return_value=mock_client):
        summary = OllamaSummarizer(fetcher=fetcher).summarize(_item())

    assert summary is None


@pytest.mark.skipif(os.getenv("MY_FEED_OLLAMA") != "1", reason="opt-in live Ollama")
def test_live_ollama_generate() -> None:
    """Hit a real local Ollama. Opt-in: MY_FEED_OLLAMA=1."""
    summarizer = OllamaSummarizer(
        fetcher=lambda _url: "<p>Python の asyncio 入門。イベントループの基本。</p>"
    )
    summary = summarizer.summarize(_item(title="asyncio 入門"))
    assert summary is not None
    assert len(summary) > 10
    # Ensure response is JSON-serializable text (sanity).
    assert json.dumps(summary, ensure_ascii=False)
