#!/usr/bin/env python3
"""Gemini API 要約機能の単体テストスクリプト

.env ファイルからAPIキーを読み込み、1記事だけ要約を試します。
エラーの詳細を表示するので、問題の特定に使えます。

使い方:
    python scripts/test_summarizer.py
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from dotenv import load_dotenv

from my_feed.config import SummarizerConfig
from my_feed.models import Item, SourceName
from my_feed.summarizer import GeminiSummarizer

# .env を読み込む
load_dotenv()


def test_api_key() -> str | None:
    """APIキーが設定されているか確認"""
    config = SummarizerConfig()
    api_key = config.get_api_key()

    if not api_key:
        print("❌ APIキーが設定されていません")
        print(f"   環境変数 {config.api_key_env} を確認してください")
        print("   .env ファイルがあるか確認: ls -la .env")
        return None

    # APIキーをマスク表示
    masked = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
    print(f"✅ APIキーを検出: {masked}")
    return api_key


def test_summarize_simple() -> None:
    """シンプルなテスト記事で要約を試す"""
    api_key = test_api_key()
    if not api_key:
        return

    print("\n--- テスト記事で要約を試します ---")

    # テスト用の記事（実在する技術記事）
    test_item = Item(
        id="test:example",
        source=SourceName.FAKE,
        title="Pythonの非同期プログラミング入門",
        url="https://docs.python.org/ja/3/library/asyncio.html",
        tags=["Python", "asyncio"],
        fetched_at=datetime.now(UTC),
    )

    print(f"記事タイトル: {test_item.title}")
    print(f"記事URL: {test_item.url}")
    print(f"タグ: {', '.join(test_item.tags)}")
    print()

    try:
        config = SummarizerConfig()
        summarizer = GeminiSummarizer(
            api_key=api_key,
            model=config.model,
        )

        print("⏳ Gemini APIに要約をリクエスト中...")
        summary = summarizer.summarize(test_item)

        if summary:
            print("✅ 要約に成功しました！\n")
            print("=" * 60)
            print(summary)
            print("=" * 60)
        else:
            print("⚠️  要約が空でした（API呼び出しは成功したが結果なし）")

    except Exception as exc:
        print(f"❌ エラーが発生しました: {type(exc).__name__}")
        print(f"   詳細: {exc}")
        print()

        # 詳細なトレースバック
        import traceback
        print("--- 詳細なエラー情報 ---")
        traceback.print_exc()
        print()

        # よくあるエラーのヒント
        error_msg = str(exc).lower()
        if "403" in error_msg or "forbidden" in error_msg:
            print("💡 ヒント: APIキーが無効か、権限がありません")
            print("   - Google AI Studio でAPIキーを再確認してください")
            print("   - https://aistudio.google.com/apikey")
        elif "401" in error_msg or "unauthorized" in error_msg:
            print("💡 ヒント: 認証エラーです")
            print("   - APIキーが正しく設定されているか確認してください")
        elif "429" in error_msg or "rate limit" in error_msg:
            print("💡 ヒント: レート制限に達しました")
            print("   - しばらく待ってから再試行してください")
        elif "404" in error_msg:
            print("💡 ヒント: エンドポイントが見つかりません")
            print("   - モデル名が正しいか確認してください")
            print(f"   - 現在のモデル: {config.model}")
        elif "500" in error_msg or "503" in error_msg:
            print("💡 ヒント: Gemini API側のエラーです")
            print("   - しばらく待ってから再試行してください")
        elif "attribute" in error_msg:
            print("💡 ヒント: 属性エラーです")
            print("   - SummarizerConfig や GeminiSummarizer の実装を確認してください")
            print("   - config.model が存在するか確認してください")

        sys.exit(1)


def main() -> None:
    print("=" * 60)
    print("Gemini API 要約機能の診断スクリプト")
    print("=" * 60)
    print()

    test_summarize_simple()

    print()
    print("=" * 60)
    print("✅ テスト完了")
    print("=" * 60)


if __name__ == "__main__":
    main()
