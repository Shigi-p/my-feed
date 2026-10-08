.PHONY: install test test-all test-cov lint format format-check typecheck ci clean pre-commit-install pre-commit-run help

help:
	@echo "利用可能なコマンド:"
	@echo "  make install            - 依存関係をインストール"
	@echo "  make test               - テストを実行（ネットワークテスト除外）"
	@echo "  make test-all           - 全テストを実行（ネットワークテスト含む）"
	@echo "  make test-cov           - カバレッジ付きテスト実行"
	@echo "  make lint               - Ruffでコードをチェック"
	@echo "  make format             - Ruffでコードをフォーマット"
	@echo "  make format-check       - フォーマットチェック（CI用）"
	@echo "  make typecheck          - mypyで型チェック"
	@echo "  make ci                 - CI相当の全チェックを実行"
	@echo "  make pre-commit-install - pre-commitフックをインストール"
	@echo "  make pre-commit-run     - pre-commitを手動実行"
	@echo "  make clean              - キャッシュファイルを削除"

install:
	uv sync --extra dev

test:
	uv run pytest tests/ -v --no-cov

test-all:
	MY_FEED_LIVE=1 uv run pytest tests/ -v --no-cov

test-cov:
	uv run pytest tests/ -v
	@echo ""
	@echo "📊 カバレッジレポートを htmlcov/index.html に生成しました"

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

pre-commit-install:
	uv run pre-commit install
	uv run pre-commit install --hook-type commit-msg
	@echo "✓ pre-commitフックをインストールしました"

pre-commit-run:
	uv run pre-commit run --all-files

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage .coverage.* coverage.xml 2>/dev/null || true
