"""Gemini API summarizer with URL Context."""

from __future__ import annotations

import logging

from google import genai

from my_feed.models import Item

logger = logging.getLogger(__name__)


class GeminiSummarizer:
    """Gemini 3.5 Flash Lite + URL Context による記事要約。

    URL Context により、Gemini が記事 URL から直接コンテンツを取得・分析する。
    手動での HTML パースは不要。

    技術パラメータは要約タスク向けに最適化:
    - thinking_level: "minimal" (Flash-Lite のデフォルト、コスト効率的)
    - max_output_tokens: 3000 (thinking + 詳細要約に十分)
    - temperature: 1.0 (Gemini 3.x 公式デフォルト、変更禁止)
    - timeout: 30秒 (URL Context は記事取得を含むため長め)
    """

    # 技術パラメータ（要約に最適化された固定値）
    # 変更禁止: Gemini 3.x は temperature=1.0 で最適化されている
    _TEMPERATURE = 1.0
    _MAX_OUTPUT_TOKENS = 3000
    _THINKING_LEVEL = "minimal"
    _TIMEOUT_SECONDS = 30

    def __init__(
        self,
        api_key: str,
        *,
        model: str = "gemini-3.5-flash-lite",
    ) -> None:
        """Gemini クライアントを初期化。

        Args:
            api_key: Gemini API キー
            model: モデル名（デフォルト: gemini-3.5-flash-lite）
        """
        self._api_key = api_key
        self._model = model
        # タイムアウト設定付きでクライアントを初期化
        # URL Context は記事取得も含むため、通常の API より長めに設定
        self._client = genai.Client(api_key=api_key, http_options={"timeout": self._TIMEOUT_SECONDS})

    def summarize(self, item: Item) -> str | None:
        """URL Context を使って要約を生成。

        Args:
            item: 要約対象の記事

        Returns:
            詳細な要約（5-8行）。API 呼び出し失敗時は None。
        """
        try:
            prompt = self._build_prompt(item)

            interaction = self._client.interactions.create(
                model=self._model,
                input=prompt,
                tools=[{"type": "url_context"}],
                generation_config={
                    "temperature": self._TEMPERATURE,
                    "max_output_tokens": self._MAX_OUTPUT_TOKENS,
                    "thinking_config": {
                        "thinking_level": self._THINKING_LEVEL,
                    },
                },
            )

            summary = interaction.output_text.strip()  # type: ignore[union-attr]
            if not summary:
                logger.warning(f"Empty summary for {item.id}")
                return None

            # Log token usage for monitoring
            if hasattr(interaction, "usage_metadata"):
                usage = interaction.usage_metadata
                logger.info(
                    f"Token usage for {item.id}: "
                    f"input={getattr(usage, 'prompt_token_count', '?')}, "
                    f"output={getattr(usage, 'candidates_token_count', '?')}, "
                    f"total={getattr(usage, 'total_token_count', '?')}"
                )

            return summary  # type: ignore[return-value]

        except Exception as exc:
            # Log the error but don't propagate — pipeline should continue
            logger.warning(
                f"Failed to summarize {item.id} ({item.url}): {type(exc).__name__}: {exc}",
                exc_info=True,  # Include full traceback for debugging
            )
            return None

    def _build_prompt(self, item: Item) -> str:
        """Gemini 用のプロンプトを構築。

        URL（URL Context 用）、タイトル、オプションのタグを含む。
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
