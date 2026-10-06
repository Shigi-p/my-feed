# my feed

キャッチアップをいい感じにしたい

## 現状

**M2（ローカル完成）** まで到達。localhost で実取得 → Top 10 → Markdown DL → 履歴・お気に入り（SQLite）が使える。  
次は任意の **M3**（運用改善・フィルタ等）。

## セットアップ（uv）

```bash
# uv が無い場合: https://docs.astral.sh/uv/getting-started/installation/
uv sync --extra dev
```

## いちばん短い使い方（ローカル完成）

```bash
cp config.example.toml config.local.toml   # 初回のみ（実ソース + hybrid）
uv run my-feed serve
```

開く: <http://127.0.0.1:8000/>

- `config.local.toml` があれば Web / `load_config()` はそれを優先（無ければ `config.toml`）
- 履歴・お気に入りは `data/my_feed.db`（再起動後も残る）
- 認証なし・`127.0.0.1` 前提。本番公開しない

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

CLI の `--out-md` または Web の Markdown DL で bundle（抜粋・なぜ今見るか・問い）を出す。  
Gemini / ChatGPT に貼り、「気になる番号で要約 → 反論 → 最小実験」と依頼する。LLM API は使わない。

## 契約変更の手順

1. **先に** 契約（`models` / `sources.base` / `scoring.base` / `output` / `store` / `pipeline`）を変える PR を出す  
2. それをマージしてから、各トラック（T-Src 等）の実装 PR を追随させる  
3. トラック PR だけで契約を壊さない

詳細: [docs/plans/tech-catchup/contracts/c0-contract-hub.md](./docs/plans/tech-catchup/contracts/c0-contract-hub.md)

## 計画ドキュメント

- [docs/plans/tech-catchup/README.md](./docs/plans/tech-catchup/README.md)
- 届け方: [契約ハブ + 並行トラック](./docs/plans/tech-catchup/delivery-model.md)
- レビュー観点: [docs/guides/pr-review.md](./docs/guides/pr-review.md)
- 協働方針: [docs/guides/collaboration.md](./docs/guides/collaboration.md)
