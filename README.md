# my feed

キャッチアップをいい感じにしたい

個人用。第三者の利用・サポートは想定していない。ライセンスは置いていない（著作権のみ）。
Web は認証なし・`127.0.0.1` 前提。インターネットに晒さない。
取得の一部は非公式（Zenn の JSON API、GitHub Trending の HTML）。壊れたり利用規約の対象になり得る。

## セットアップ

```bash
# uv が無い場合: https://docs.astral.sh/uv/getting-started/installation/
uv sync --extra dev
```

## Web

```bash
cp config.example.toml config.local.toml   # 初回のみ（実ソース + hybrid + AI要約）
cp .env.example .env                       # 要約を使う場合。GEMINI_API_KEY を入れる
uv run my-feed serve
```

開く: <http://127.0.0.1:8000/>

- `config.local.toml` があれば優先（無ければルートの `config.toml`。こちらは `fake` のまま）
- 履歴・お気に入りは `data/my_feed.db`（再起動後も残る）
- 「いま取得」→ Top 一覧 → Markdown DL → 履歴 / お気に入り
- 要約は Gemini 3.5 Flash Lite。キー未設定なら警告してスキップ
- 1 ソース失敗時は `source_errors` を表示（`status=partial`）

オプション:

```bash
uv run my-feed serve --config config.local.toml --db data/my_feed.db
```

## CLI

```bash
cp config.example.toml config.local.toml
uv run my-feed run --config config.local.toml
uv run my-feed run --config config.local.toml --scorer popularity --top 10
uv run my-feed run --config config.local.toml --json --out /tmp/feed.json
uv run my-feed run --config config.local.toml --out-md /tmp/feed.md
uv run my-feed sources
uv run my-feed scorers
```

- 表形式で最大 10 件（`rank` / `score` / `source` / `title`）
- 1 ソース失敗でも他が生きていれば `status=partial`（終了コード 0）
- 全ソース失敗時のみ終了コード 1
