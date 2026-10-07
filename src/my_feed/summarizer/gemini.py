"""Gemini API summarizer with URL Context."""

from __future__ import annotations

import logging

from google import genai

from my_feed.models import Item

logger = logging.getLogger(__name__)


class GeminiSummarizer:
    """Summarize articles using Gemini 3.5 Flash Lite + URL Context.
    
    URL Context allows Gemini to fetch and analyze the full article content
    directly from the URL, without requiring manual HTML parsing.
    
    Technical parameters are optimized for summarization tasks:
    - thinking_level: "minimal" (Flash-Lite default, cost-efficient)
    - max_output_tokens: 3000 (enough for thinking + detailed summary)
    - temperature: 1.0 (Gemini 3.x official default, DO NOT CHANGE per docs)
    """

    # Technical parameters (hardcoded for optimal summarization)
    # DO NOT CHANGE: Gemini 3.x is optimized for default temperature=1.0
    _TEMPERATURE = 1.0
    _MAX_OUTPUT_TOKENS = 3000
    _THINKING_LEVEL = "minimal"

    def __init__(
        self,
        api_key: str,
        *,
        model: str = "gemini-3.5-flash-lite",
    ) -> None:
        """Initialize Gemini client.
        
        Args:
            api_key: Gemini API key
            model: Model name (default: gemini-3.5-flash-lite)
        """
        self._api_key = api_key
        self._model = model
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
            
            # Log token usage for monitoring
            if hasattr(interaction, 'usage_metadata'):
                usage = interaction.usage_metadata
                logger.info(
                    f"Token usage for {item.id}: "
                    f"input={getattr(usage, 'prompt_token_count', '?')}, "
                    f"output={getattr(usage, 'candidates_token_count', '?')}, "
                    f"total={getattr(usage, 'total_token_count', '?')}"
                )
            
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
            "以下の技術記事を5-8行（300〜500文字程度）で要約してください。",
            "記事の主要なポイント、技術的な価値、対象読者、実用性を詳しくまとめてください。",
            "",
            f"URL: {item.url}",
            f"タイトル: {item.title}",
        ]
        
        if item.tags:
            prompt_parts.append(f"タグ: {', '.join(item.tags)}")
        
        return "\n".join(prompt_parts)
