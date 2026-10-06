# Source adapters (T-Src)

Short notes on fetch paths chosen for each `SourceAdapter`. Default
`config.toml` still enables only `fake` so local runs stay offline-safe.

## Endpoints

| Source | Method | URL / notes |
|--------|--------|-------------|
| **Zenn** | Public JSON API | `GET https://zenn.dev/api/articles?order=daily&page=1` — unofficial but used by the Zenn web app; includes `liked_count` / `bookmarked_count`. RSS (`https://zenn.dev/feed`) is available but omits likes, so API is preferred. |
| **Qiita** | Official API v2 | `GET https://qiita.com/api/v2/items?page=1&per_page=20` — public GET needs **no token**. Returns `likes_count` / `stocks_count`. Unauthenticated rate limits are tighter; token optional later. RSS exists (`/popular-items/feed`) but lacks stock/like metrics. |
| **GIGAZINE** | Official RSS 2.0 | `GET https://gigazine.net/news/rss_2.0/` — no metrics. **No filtering** in the adapter (topic filters belong to M3). |
| **GitHub Trending** | HTML scrape (isolated) | `GET https://github.com/trending` — no official API. Parser lives in `github_trending.py` only; failures raise and the pipeline records `source_errors` without aborting other sources. Metrics: `stars`, `forks`, `stars_today` when present in markup. |

## Error policy

- Whole-source transport / fatal parse → raise (`RuntimeError`); pipeline catches.
- Single entry parse failure → skip that entry (warning log).
- Genuine empty result → `[]`.

## Enabling real sources

Example `config.toml` snippet (keep `fake` only if you want offline demos):

```toml
top_n = 10
default_scorer = "fake"
enabled_sources = ["zenn", "qiita", "gigazine", "github_trending"]
```

## Live smoke (optional)

CI tests use fixtures only (no network). To hit live endpoints locally:

```bash
MY_FEED_LIVE=1 uv run pytest -m network
```
