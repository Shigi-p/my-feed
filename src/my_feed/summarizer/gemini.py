"""Gemini API summarizer with URL Context."""

from __future__ import annotations

import logging

from google import genai

from my_feed.models import Item

logger = logging.getLogger(__name__)


class GeminiSummarizer:
    """Summarize articles using Gemini 3.5 Flash + URL Context.
    
    URL Context allows Gemini to fetch and analyze the full article content
    directly from the URL, without requiring manual HTML parsing.
    """

    def __init__(
        self,
        api_key: str,
        *,
        model: str = "gemini-3.5-flash",
        temperature: float = 0.3,
        max_output_tokens: int = 200,
    ) -> None:
        """Initialize Gemini client.
        
        Args:
            api_key: Gemini API key
            model: Model name (default: gemini-3.5-flash)
            temperature: Generation temperature (0.0-1.0)
            max_output_tokens: Maximum summary length in tokens
        """
        self._api_key = api_key
        self._model = model
        self._temperature = temperature
        self._max_output_tokens = max_output_tokens
        self._client = genai.Client(api_key=api_key)

    def summarize(self, item: Item) -> str | None:
        """Generate a summary using URL Context.
        
        Args:
            item: The article to summarize
            
        Returns:
            A 3-4 line summary, or None if the API call fails.
        """
        try:
            prompt = self._build_prompt(item)
            
            interaction = self._client.interactions.create(
                model=self._model,
                input=prompt,
                tools=[{"type": "url_context"}],
                generation_config={
                    "temperature": self._temperature,
                    "max_output_tokens": self._max_output_tokens,
                },
            )
            
            summary = interaction.output_text.strip()
            if not summary:
                logger.warning(f"Empty summary for {item.id}")
                return None
            
            return summary
            
        except Exception as exc:
            # Log the error but don't propagate — pipeline should continue
            logger.warning(
                f"Failed to summarize {item.id} ({item.url}): "
                f"{type(exc).__name__}"
            )
            return None

    def _build_prompt(self, item: Item) -> str:
        """Build the prompt for Gemini.
        
        Includes URL (for URL Context), title, and optional tags.
        """
        prompt_parts = [
            "以下の技術記事を3-4行（150文字程度）で要約してください。",
            "記事の主要なポイント、技術的な価値、対象読者を簡潔にまとめてください。",
            "",
            f"URL: {item.url}",
            f"タイトル: {item.title}",
        ]
        
        if item.tags:
            prompt_parts.append(f"タグ: {', '.join(item.tags)}")
        
        return "\n".join(prompt_parts)
