# my feed

キャッチアップをいい感じにしたい

## 現状

並行トラック統合済み。**M1（CLI 実 Top 10）** まで到達。次は **M2**（Web を SQLite / 実取得の本番配線）。

## セットアップ（uv）

```bash
# uv が無い場合: https://docs.astral.sh/uv/getting-started/installation/
uv sync --extra dev
```

## M1: 実ソースで CLI Top 10

ルートの `config.toml` はオフライン安全のため **`fake` のまま**。実取得は example をコピーする。

```bash
cp config.example.toml config.local.toml
uv run my-feed run --config config.local.toml
# スコアラー切替例:
uv run my-feed run --config config.local.toml --scorer popularity --top 10
uv run my-feed run --config config.local.toml --json --out /tmp/feed.json
```

期待:

- 表形式で最大 10 件（`rank` / `score` / `source` / `title`）
- 1 ソース失敗でも他が生きていれば `status=partial` と `source_errors=...` が出て終了コード 0
- 全ソース失敗時のみ終了コード 1

結合テスト（ネットワークなし）:

```bash
uv run pytest tests/test_m1_pipeline.py -q
```

任意の live スモーク（実 HTTP）:

```bash
MY_FEED_LIVE=1 uv run pytest -m network tests/test_m1_pipeline.py -q
```

ソース別の取得メモ: [docs/notes/sources.md](./docs/notes/sources.md)。

## Web UI（ローカル専用）

`127.0.0.1` バインド前提。認証なし・本番向けではない。  
デフォルト設定では Fake データ。Store はメモリ（M2 で SQLite へ）。

```bash
uv run my-feed serve
# 同等:
uv run uvicorn my_feed.web.app:app --host 127.0.0.1 --port 8000
```

開く: <http://127.0.0.1:8000/>

「いま取得」→ Top 一覧 → Markdown DL → 履歴 / お気に入り。  
pipeline / store / renderer は `my_feed.web.deps.WebDeps` 経由で注入（M2 で配線替え）。

## CLI（その他）

```bash
uv run my-feed sources
uv run my-feed scorers
uv run my-feed run
uv run my-feed run --json
uv run my-feed run --out-md /tmp/feed.md
uv run pytest
```

`config.toml` の `enabled_sources` / `default_scorer` / `top_n` を変更できる。
## Markdown → Gemini 壁打ち

`--out-md` で Top N の bundle（抜粋・なぜ今見るか・問い 2〜3）を書き出す。  
ファイル内容を Gemini / ChatGPT に貼り、「気になる番号で要約 → 反論 → 最小実験」と依頼する。LLM API は使わない。

## 契約変更の手順

1. **先に** 契約（`models` / `sources.base` / `scoring.base` / `output` / `store` / `pipeline`）を変える PR を出す  
2. それをマージしてから、各トラック（T-Src 等）の実装 PR を追随させる  
3. トラック PR だけで契約を壊さない

詳細: [docs/plans/tech-catchup/contracts/c0-contract-hub.md](./docs/plans/tech-catchup/contracts/c0-contract-hub.md)

## 計画ドキュメント

- [docs/plans/tech-catchup/README.md](./docs/plans/tech-catchup/README.md)
- 届け方: [契約ハブ + 並行トラック](./docs/plans/tech-catchup/delivery-model.md)
- レビュー観点: [docs/guides/pr-review.md](./docs/guides/pr-review.md)
