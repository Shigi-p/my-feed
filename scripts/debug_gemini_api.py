#!/usr/bin/env python3
"""Gemini API接続の詳細診断スクリプト（デバッグ用）

使い方:
    python scripts/debug_gemini_api.py
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

import logging
import os

from dotenv import load_dotenv

# ロギングを最大限詳細に設定
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

# .env を読み込む
load_dotenv()

def check_environment():
    """環境変数の状態を確認"""
    print("=" * 60)
    print("環境変数チェック")
    print("=" * 60)

    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        masked = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
        print(f"✅ GEMINI_API_KEY: {masked}")
        print(f"   長さ: {len(api_key)} 文字")
    else:
        print("❌ GEMINI_API_KEY が設定されていません")
        return False

    # .envファイルの存在確認
    env_path = Path.cwd() / ".env"
    if env_path.exists():
        print(f"✅ .env ファイルが存在します: {env_path}")
    else:
        print(f"⚠️  .env ファイルが見つかりません: {env_path}")

    return True


def test_google_genai_import():
    """google.genai のインポートテスト"""
    print("\n" + "=" * 60)
    print("google.genai ライブラリのインポートテスト")
    print("=" * 60)

    try:
        from google import genai
        print("✅ google.genai をインポートできました")
        print(f"   バージョン: {getattr(genai, '__version__', '不明')}")
        return True
    except ImportError as exc:
        print(f"❌ インポートエラー: {exc}")
        return False


def test_simple_api_call():
    """最もシンプルなAPI呼び出しテスト"""
    print("\n" + "=" * 60)
    print("Gemini API 接続テスト（テキストのみ）")
    print("=" * 60)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ APIキーがありません")
        return

    try:
        from google import genai

        print("⏳ クライアントを初期化中...")
        client = genai.Client(api_key=api_key)
        print("✅ クライアント初期化成功")

        print("⏳ シンプルなテキスト生成をリクエスト中...")
        print("   プロンプト: 'こんにちは'")

        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents="こんにちは"
        )

        print("✅ API呼び出し成功！")
        print(f"   レスポンス: {response.text[:100]}...")

    except Exception as exc:
        print(f"❌ エラー: {type(exc).__name__}")
        print(f"   メッセージ: {exc}")

        # 詳細なトレースバック
        import traceback
        print("\n--- 詳細なエラー情報 ---")
        traceback.print_exc()


def test_url_context():
    """URL Context機能のテスト"""
    print("\n" + "=" * 60)
    print("URL Context 機能のテスト")
    print("=" * 60)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ APIキーがありません")
        return

    try:
        from google import genai

        client = genai.Client(api_key=api_key)

        test_url = "https://www.python.org/"
        print("⏳ URL Context でリクエスト中...")
        print(f"   URL: {test_url}")
        print("   プロンプト: 'このサイトを1行で説明してください'")

        interaction = client.interactions.create(
            model="gemini-3.5-flash",
            input=f"このサイトを1行で説明してください: {test_url}",
            tools=[{"type": "url_context"}],
        )

        print("✅ URL Context 呼び出し成功！")
        print(f"   レスポンス: {interaction.output_text[:200]}...")

    except Exception as exc:
        print(f"❌ エラー: {type(exc).__name__}")
        print(f"   メッセージ: {exc}")

        import traceback
        print("\n--- 詳細なエラー情報 ---")
        traceback.print_exc()


def main():
    print("=" * 60)
    print("Gemini API 詳細診断スクリプト")
    print("=" * 60)
    print()

    if not check_environment():
        print("\n❌ 環境変数の設定に問題があります")
        sys.exit(1)

    if not test_google_genai_import():
        print("\n❌ ライブラリのインポートに失敗しました")
        sys.exit(1)

    test_simple_api_call()
    test_url_context()

    print("\n" + "=" * 60)
    print("診断完了")
    print("=" * 60)


if __name__ == "__main__":
    main()
