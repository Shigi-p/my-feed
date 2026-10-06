# my feed

キャッチアップをいい感じにしたい

## 現状

- **C0**: 契約ハブ（型・Protocol・Fake パイプライン）
- **T-Web**: localhost FastAPI UI（Fake store / stub markdown で導線確認）

実ソース取得・本スコア・本 Markdown・SQLite は各トラックで後続。M2 で差し替え。

## セットアップ（uv）

```bash
# uv が無い場合: https://docs.astral.sh/uv/getting-started/installation/
uv sync --extra dev
```

## Web UI（ローカル専用）

`127.0.0.1` バインド前提。認証なし・本番向けではない。

```bash
uv run my-feed serve
# 同等:
uv run uvicorn my_feed.web.app:app --host 127.0.0.1 --port 8000
```

開く: <http://127.0.0.1:8000/>

「いま取得」→ Top 一覧 → Markdown DL → 履歴 / お気に入り。  
pipeline / store / renderer は `my_feed.web.deps.WebDeps` 経由で注入（M2 で配線替え）。

## CLI

```bash
uv run my-feed sources
uv run my-feed scorers
uv run my-feed run
uv run my-feed run --json
uv run my-feed run --out-md /tmp/feed.md
uv run pytest
```

`config.toml` の `enabled_sources` / `default_scorer` / `top_n` を変更できる。現状は `fake` のみ登録。

## 契約変更の手順

1. **先に** 契約（`models` / `sources.base` / `scoring.base` / `output` / `store` / `pipeline`）を変える PR を出す  
2. それをマージしてから、各トラック（T-Src 等）の実装 PR を追随させる  
3. トラック PR だけで契約を壊さない

詳細: [docs/plans/tech-catchup/contracts/c0-contract-hub.md](./docs/plans/tech-catchup/contracts/c0-contract-hub.md)

## 計画ドキュメント

- [docs/plans/tech-catchup/README.md](./docs/plans/tech-catchup/README.md)
- 届け方: [契約ハブ + 並行トラック](./docs/plans/tech-catchup/delivery-model.md)
