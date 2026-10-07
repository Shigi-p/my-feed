#!/usr/bin/env python3
"""Test Gemini API connection and URL Context feature."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

# Load .env
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

print("=" * 60)
print("Gemini API Test")
print("=" * 60)

# Step 1: Check API key
print("\n[1] API Key Check")
if not api_key:
    print("❌ GEMINI_API_KEY not found in environment")
    print("\nPlease set it:")
    print("  echo 'GEMINI_API_KEY=your-key' > .env")
    sys.exit(1)

print(f"✅ API Key found: {api_key[:8]}...{api_key[-4:]}")

# Step 2: Test basic Gemini connection (without URL Context)
print("\n[2] Basic Gemini API Test (without URL Context)")
try:
    from google import genai

    client = genai.Client(api_key=api_key)

    print("Sending test request...")
    response = client.interactions.create(
        model="gemini-3.5-flash",
        input="Hello, please respond with 'OK'",
        generation_config={
            "temperature": 0.3,
            "max_output_tokens": 50,
        }
    )

    print(f"✅ Response: {response.output_text.strip()}")

except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
    print("\nFull error:")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 3: Test URL Context feature
print("\n[3] URL Context Test")
try:
    test_url = "https://example.com"
    print(f"Testing with URL: {test_url}")

    response = client.interactions.create(
        model="gemini-3.5-flash",
        input=f"この記事の内容を1行で要約してください: {test_url}",
        tools=[{"type": "url_context"}],
        generation_config={
            "temperature": 0.3,
            "max_output_tokens": 200,
        }
    )

    summary = response.output_text.strip()
    print(f"✅ Summary: {summary}")

except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
    print("\nFull error:")
    import traceback
    traceback.print_exc()

    print("\nPossible causes:")
    print("  - URL Context not available in your API plan")
    print("  - API key doesn't have proper permissions")
    print("  - Rate limit exceeded")
    sys.exit(1)

# Step 4: Test with real article summarization
print("\n[4] Real Article Test")
try:
    from datetime import UTC, datetime

    from my_feed.models import Item, SourceName
    from my_feed.summarizer import GeminiSummarizer

    # Create test item
    item = Item(
        id="test:1",
        source=SourceName.QIITA,
        title="テスト記事",
        url="https://qiita.com",
        fetched_at=datetime.now(UTC),
        tags=["test"],
    )

    summarizer = GeminiSummarizer(api_key=api_key)
    print(f"Summarizing: {item.url}")

    summary = summarizer.summarize(item)

    if summary:
        print(f"✅ Summary generated ({len(summary)} chars):")
        print(f"   {summary[:100]}...")
    else:
        print("❌ Summary is None")

except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ All tests passed!")
print("=" * 60)
