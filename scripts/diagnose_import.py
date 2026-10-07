#!/usr/bin/env python3
"""Minimal test to diagnose import issues"""

import sys
from pathlib import Path

# Add src to path (same as test_summarizer.py)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

print("=== Import Diagnostic ===")
print(f"Python: {sys.version}")
print(f"Project root: {project_root}")
print(f"Src path: {project_root / 'src'}")
print()

try:
    print("1. Importing SummarizerConfig...")
    from my_feed.config import SummarizerConfig
    print("   ✅ Success")
    
    print("2. Creating config instance...")
    config = SummarizerConfig()
    print("   ✅ Success")
    
    print("3. Checking config attributes...")
    print(f"   - enabled: {config.enabled}")
    print(f"   - model: {config.model}")
    print(f"   - api_key_env: {config.api_key_env}")
    print("   ✅ All attributes present")
    
    print("4. Checking get_api_key method...")
    api_key = config.get_api_key()
    print(f"   - API key: {'(set)' if api_key else '(not set)'}")
    print("   ✅ Method works")
    
    print("5. Importing GeminiSummarizer...")
    from my_feed.summarizer import GeminiSummarizer
    print("   ✅ Success")
    
    print()
    print("=== All checks passed ===")
    
except AttributeError as e:
    print(f"   ❌ AttributeError: {e}")
    print()
    import traceback
    traceback.print_exc()
    sys.exit(1)
    
except Exception as e:
    print(f"   ❌ Error: {type(e).__name__}: {e}")
    print()
    import traceback
    traceback.print_exc()
    sys.exit(1)
