"""Base protocol for article summarizers."""

from __future__ import annotations

from typing import Protocol

from my_feed.models import Item


class SummarizerAdapter(Protocol):
    """記事要約エンジンの契約。

    実装は記事コンテンツを取得し、簡潔な要約を生成する。
    失敗時は例外を上げずに None を返し、パイプラインを継続させる。
    """

    def summarize(self, item: Item) -> str | None:
        """記事の要約を生成する。

        Args:
            item: 要約対象の記事（URL、タイトル、タグ等）

        Returns:
            詳細な要約（5-8行、300〜500文字程度）。失敗時は None。
        """
        ...
