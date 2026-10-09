# my feed

キャッチアップをいい感じにしたい

## 現状

**M2（ローカル完成）+ M4-D（Gemini 要約）**。localhost で実取得 → Top 10 → Markdown DL → 履歴・お気に入り（SQLite）が使える。
次は任意。未着手は [GitHub Issues](https://github.com/Shigi-p/my-feed/issues)。

## 注意

個人用です。第三者の利用・サポートは想定していません。ライセンスファイルは置いていません（著作権のみ。利用許諾は与えていません）。

- Web UI は認証なし・`127.0.0.1` 前提。インターネットに晒さない
- 取得の一部は非公式で、壊れたり利用規約の対象になったりし得る
  - Zenn: サイトが使う非公式 JSON API（likes のため。RSS には無い）
  - GitHub Trending: 公式 API が無いため HTML をパース
  - Qiita / GIGAZINE: 公式 API / RSS
- 経路の詳細: [docs/notes/sources.md](./docs/notes/sources.md)

## セットアップ（uv）

```bash
# uv が無い場合: https://docs.astral.sh/uv/getting-started/installation/
uv sync --extra dev
```

## 開発者向け：コード品質チェック

このプロジェクトでは自動化されたコード品質チェックを導入しています。

### 初回セットアップ

```bash
# 依存関係をインストール
make install

# pre-commitフックをインストール（推奨）
make pre-commit-install
```

### クイックスタート

```bash
# CI相当の全チェックを実行
make ci

# 個別実行
make lint         # Ruffリント
make format       # 自動フォーマット
make typecheck    # mypy型チェック
make test         # テスト実行
make test-cov     # カバレッジ付きテスト
```

### PRを出す前に

**方法A: pre-commitを使う（推奨）**
```bash
git add .
git commit -m "feat: 新機能を追加"
# → 自動でリント・フォーマット・型チェックが実行される
```

**方法B: 手動チェック**
```bash
make format       # 1. コードをフォーマット
make ci           # 2. 全チェック実行
# 3. 全て✓ならPRを作成
```

### ツール

- **Ruff**: 高速なリンター・フォーマッター（行長110文字、日本語docstring対応）
- **mypy**: 型チェッカー（段階的な厳格化方針）
- **pytest**: テストランナー（ネットワークテストは `@pytest.mark.network` でマーク）
- **pytest-cov**: カバレッジ測定（HTML/XML/ターミナル出力）
- **pre-commit**: コミット前の自動チェック

設定は `pyproject.toml` と `.pre-commit-config.yaml` に集約されています。

### テストカバレッジ

```bash
# カバレッジ付きテスト実行
make test-cov

# HTMLレポートを確認
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

カバレッジレポートは PR の GitHub Actions でも自動生成され、Artifacts からダウンロード可能です。

## いちばん短い使い方（ローカル完成）

```bash
cp config.example.toml config.local.toml   # 初回のみ（実ソース + hybrid + AI要約）
export GEMINI_API_KEY="your-api-key-here"  # AI要約を使う場合
uv run my-feed serve
```

開く: <http://127.0.0.1:8000/>

- `config.local.toml` があれば Web / `load_config()` はそれを優先（無ければ `config.toml`）
- 履歴・お気に入りは `data/my_feed.db`（再起動後も残る）
- 認証なし・`127.0.0.1` 前提。本番公開しない（上の「注意」）

### AI要約機能（M4-D）

Gemini 3.5 Flash Lite を使った記事要約が利用可能です：

1. **APIキーの取得**: [Google AI Studio](https://aistudio.google.com/apikey) で無料取得

2. **環境変数の設定**（2つの方法）:

   **方法A: .env ファイル（推奨）**
   ```bash
   cp .env.example .env
   # .env ファイルを編集してAPIキーを設定
   ```

   `.env` の内容:
   ```
   GEMINI_API_KEY=your-api-key-here
   ```

   **方法B: export コマンド**
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   ```

3. **設定ファイル**: `config.local.toml` で `[summarizer] enabled = true`（example の初期値）

**コスト**: 1記事あたり約0.1円、10記事で約1円（無料枠でも実用的）

**技術パラメータ**: 要約に最適化された設定（thinking_level=minimal、max_output_tokens=3000）を使用。

APIキー未設定時は警告のみで要約をスキップします。

オプション:

```bash
uv run my-feed serve --config config.local.toml --db data/my_feed.db
# 同等（モジュール属性は遅延初期化）:
uv run uvicorn my_feed.web.app:app --host 127.0.0.1 --port 8000
```

「いま取得」→ Top 一覧 → Markdown DL → 履歴 / お気に入り。
1 ソース失敗時は画面に `source_errors` を表示（`status=partial`）。

## M1: CLI 実ソース Top 10

ルートの `config.toml` はオフライン安全のため **`fake` のまま**。実取得は example をコピーする。

```bash
cp config.example.toml config.local.toml
uv run my-feed run --config config.local.toml
uv run my-feed run --config config.local.toml --scorer popularity --top 10
uv run my-feed run --config config.local.toml --json --out /tmp/feed.json
uv run my-feed run --config config.local.toml --out-md /tmp/feed.md
```

期待:

- 表形式で最大 10 件（`rank` / `score` / `source` / `title`）
- 1 ソース失敗でも他が生きていれば `status=partial` と `source_errors=...` が出て終了コード 0
- 全ソース失敗時のみ終了コード 1

```bash
uv run pytest tests/test_m1_pipeline.py tests/test_m2_web.py -q
MY_FEED_LIVE=1 uv run pytest -m network tests/test_m1_pipeline.py -q
```

ソース別の取得メモ: [docs/notes/sources.md](./docs/notes/sources.md)。

## CLI（その他）

```bash
uv run my-feed sources
uv run my-feed scorers
uv run my-feed run
uv run pytest
```

## Markdown → Gemini 壁打ち

CLI の `--out-md` または Web の Markdown DL で bundle（AI要約・抜粋・なぜ今見るか・問い）を出す。
Gemini / ChatGPT に貼り、「気になる番号で要約 → 反論 → 最小実験」と依頼する。

M4-D 以降は AI 要約が自動生成されるため、手動での要約依頼は不要になります。

## 契約変更の手順

型の正本はコード（`models.py` / 各 `base.py`）。

1. **先に** 契約（`models` / `sources.base` / `scoring.base` / `output` / `store` / `pipeline` / `summarizer.base`）を変える PR を出す
2. それをマージしてから、実装 PR を追随させる
3. 機能 PR だけで契約を壊さない

詳細: [docs/guides/implementation.md](./docs/guides/implementation.md)

## ドキュメント

- 未着手: [GitHub Issues](https://github.com/Shigi-p/my-feed/issues)
- 実装ルール: [docs/guides/implementation.md](./docs/guides/implementation.md)
- レビュー観点: [docs/guides/pr-review.md](./docs/guides/pr-review.md)
- 協働方針: [docs/guides/collaboration.md](./docs/guides/collaboration.md)
- コードの読み順: [docs/guides/reading-order.md](./docs/guides/reading-order.md)
- 取得経路: [docs/notes/sources.md](./docs/notes/sources.md)
