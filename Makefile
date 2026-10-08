.PHONY: install test test-all lint format format-check typecheck ci clean help

help:
	@echo "利用可能なコマンド:"
	@echo "  make install       - 依存関係をインストール"
	@echo "  make test          - テストを実行（ネットワークテスト除外）"
	@echo "  make test-all      - 全テストを実行（ネットワークテスト含む）"
	@echo "  make lint          - Ruffでコードをチェック"
	@echo "  make format        - Ruffでコードをフォーマット"
	@echo "  make format-check  - フォーマットチェック（CI用）"
	@echo "  make typecheck     - mypyで型チェック"
	@echo "  make ci            - CI相当の全チェックを実行"
	@echo "  make clean         - キャッシュファイルを削除"

install:
	uv sync --extra dev

test:
	uv run pytest tests/ -v

test-all:
	MY_FEED_LIVE=1 uv run pytest tests/ -v

lint:
	uv run ruff check .

format:
	uv run ruff format .

format-check:
	uv run ruff format --check .

typecheck:
	uv run mypy src/

ci: lint format-check typecheck test
	@echo "✓ 全てのCIチェックが通りました"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
