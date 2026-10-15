"""Article summarization adapters (T-Summarizer)."""

from __future__ import annotations

from my_feed.summarizer.base import SummarizerAdapter
from my_feed.summarizer.fake import FakeSummarizer
from my_feed.summarizer.gemini import GeminiSummarizer
from my_feed.summarizer.ollama import OllamaSummarizer

__all__ = [
    "SummarizerAdapter",
    "FakeSummarizer",
    "GeminiSummarizer",
    "OllamaSummarizer",
]
