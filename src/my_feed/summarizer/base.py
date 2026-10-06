"""Base protocol for article summarizers."""

from __future__ import annotations

from typing import Protocol

from my_feed.models import Item


class SummarizerAdapter(Protocol):
    """Contract for article summarization engines.
    
    Implementations fetch article content and generate concise summaries.
    Failures return None rather than raising, so the pipeline can continue.
    """

    def summarize(self, item: Item) -> str | None:
        """Generate a 3-4 line summary of the article.
        
        Args:
            item: The article to summarize (URL, title, tags, etc.)
            
        Returns:
            A concise summary (150-200 chars), or None if summarization fails.
        """
        ...
