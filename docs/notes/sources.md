# ソースアダプタ

各 `SourceAdapter` の取得経路メモ。ルートの `config.toml` はオフライン安全のため `fake` のみ。

## エンドポイント

| ソース | 手段 | URL / メモ |
|--------|------|------------|
| **Zenn** | 非公式の公開 JSON API | `GET https://zenn.dev/api/articles?order=daily&page=1` — Zenn の Web が使う API。`liked_count` / `bookmarked_count` がある。RSS（`https://zenn.dev/feed`）は likes が無いので API を優先。 |
| **Qiita** | 公式 API v2 | `GET https://qiita.com/api/v2/items?page=1&per_page=20` — 公開 GET にトークン不要。`likes_count` / `stocks_count` を返す。未認証はレート制限が厳しい。トークンは後から任意。RSS（`/popular-items/feed`）は stock/like が無い。 |
| **GIGAZINE** | 公式 RSS 2.0 | `GET https://gigazine.net/news/rss_2.0/` — 指標なし。アダプタ内ではフィルタしない（トピックフィルタは運用改善の Issue）。 |
| **GitHub Trending** | HTML スクレイピング（隔離） | `GET https://github.com/trending` — 公式 API なし。パーサは `github_trending.py` のみ。失敗は raise し、pipeline が `source_errors` に残して他ソースは続ける。取れるとき: `stars` / `forks` / `stars_today`。 |

## 失敗時

- ソース全体の通信失敗・致命的なパース失敗 → raise（`RuntimeError`）。pipeline が捕捉する。
- 1件のパース失敗 → その件だけスキップ（warning ログ）。
- 本当に空 → `[]`。

## 実ソースを有効にする

コミット済みの example をコピーする（ルート `config.toml` は fake のまま）:

```bash
cp config.example.toml config.local.toml
uv run my-feed run --config config.local.toml
```

同じキーをローカル上書きに書いてもよい。手順は README の CLI 節。

## ライブ確認（任意）

CI と通常の pytest は fixtures のみ（ネットワークなし）。実際のエンドポイントを叩くとき:

```bash
MY_FEED_LIVE=1 uv run pytest -m network
# M1 の結合だけ:
MY_FEED_LIVE=1 uv run pytest -m network tests/test_m1_pipeline.py
```
