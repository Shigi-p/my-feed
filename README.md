# my feed

キャッチアップをいい感じにしたい

## 現状（C0 + T-Md）

契約ハブ（型・Protocol・Fake パイプライン）に加え、壁打ち用 Markdown（ルールベース）を生成できる。  
実ソース取得・本スコア・Web・SQLite は各トラックで後続。

## セットアップ（uv）

```bash
# uv が無い場合: https://docs.astral.sh/uv/getting-started/installation/
uv sync --extra dev
```

## よく使うコマンド

```bash
uv run my-feed sources
uv run my-feed scorers
uv run my-feed run
uv run my-feed run --json
uv run my-feed run --out-md /tmp/feed.md
uv run pytest
```

`config.toml` の `enabled_sources` / `default_scorer` / `top_n` を変更できる。  
デフォルトはオフライン安全のため `fake` のみ。実ソース（Zenn / Qiita / GIGAZINE / GitHub Trending）はレジストリ登録済み — 有効化例は [docs/notes/sources.md](./docs/notes/sources.md)。

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
