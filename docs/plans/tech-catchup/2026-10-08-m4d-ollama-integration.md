# M4-D 拡張 — Ollama統合によるコストゼロ要約

| 項目 | 内容 |
|------|------|
| 日付 | 2026-10-08 |
| 依存 | M2完了（Gemini要約が既に動作） |
| 参考 | [ryochin/stingray](https://github.com/ryochin/stingray) |
| ゴール | デフォルトはGemini。自宅PCでは環境変数でollamaに切り替え、コストゼロで要約できる |

このPRは**計画のみ**。実装は承認後に別PRで進める。

---

## 1. 背景

### 現状
- Gemini 3.5 Flash Lite + URL Context で Top N を要約（1記事約0.1円）
- パイプラインはオンデマンド（「いま取得」）
- 出先ではコードを触れない

### 方針
- **デフォルトは Gemini**（出先でそのまま動く）
- **自宅PCだけ** `SUMMARIZER_BACKEND=ollama` で切り替え
- ローカル実行を維持（常時稼働サーバーは作らない）
- 自動フォールバックはしない（失敗時は要約スキップ）

### 使い方（完成後）

出先・通常:

```bash
export GEMINI_API_KEY="your-key"
uv run my-feed serve
```

自宅PC:

```bash
ollama serve
ollama pull gemma4:e4b
SUMMARIZER_BACKEND=ollama uv run my-feed serve
```

---

## 2. stingray との相違点

| 観点 | stingray | my feed | 判断 |
|------|----------|---------|------|
| 実行モデル | 常時稼働 + cron | オンデマンド | **維持**。サーバー化しない |
| 要約タイミング | 全記事を ingest 時に要約してDB保存 | Top N だけその場で要約 | **維持** |
| 本文 | fetch時に全記事から `content_snippet` を抜く | 一覧API/RSSの `excerpt` のみ | **要約時に Top N だけ HTML 取得** |
| LLM | ollama のみ | Gemini が既にある | **Gemini既定 + ollama任意** |
| 並行 | asyncio + Semaphore(3) | 同期・順次 | **今回見送り** |
| 永続化 | PostgreSQL に全記事 | SQLite は履歴・お気に入り | **維持** |
| モデル | `gemma4:e4b` | — | **採用** |

取り込むもの:

- Ollama HTTP API（`/api/generate`、timeout、接続失敗はスキップ）
- シンプルな HTML → 本文テキスト抽出
- 推奨モデル `gemma4:e4b`

取り込まないもの:

- cron / adaptive interval
- 翻訳スイッチ
- 全記事の事前本文抽出（Top N 以外を取る必要がない）

---

## 3. 本文取得の判断（重要）

stingrayは全記事を保存するので、fetch時に本文を抜くのが合理的。
my feedは **スコア後の Top N（既定10件）だけ** 要約する。

| 案 | 内容 | 欠点 |
|----|------|------|
| A. 各Sourceで全件HTML取得 | Zenn/Qiita等の一覧取得後に記事ページを全部取る | 一覧が数十件あるので遅い。Sourceの責任を超える |
| B. `Item.content_snippet` を契約に追加 | C0変更が先に必要 | 今回の価値に対して重い |
| **C. 要約時に Top N だけ取得** | `OllamaSummarizer` が URL を GET して本文抽出 | Gemini経路は今のまま。失敗時は `excerpt` / タイトルにフォールバック |

**採用: C**

- `Item` の契約は変えない
- Gemini は URL Context のまま（本文取得しない）
- ollama だけ自前で HTML を取る
- 抽出は `sources/` ではなく `summarizer/` 側（要約のための取得）

既存の `Item.excerpt` は RSS/API の短い抜粋。ollamaの入力が空ならこれを使い、それも無ければタイトルのみ。

---

## 4. 設定

```toml
[summarizer]
enabled = true
backend = "gemini"                 # "gemini" | "ollama"
model = "gemini-3.5-flash-lite"     # Gemini用（現状どおり）
ollama_model = "gemma4:e4b"

[summarizer.ollama]
base_url = "http://localhost:11434"
timeout = 120
```

優先順位:

1. 環境変数 `SUMMARIZER_BACKEND`（`gemini` / `ollama`）
2. `config` の `summarizer.backend`
3. 未設定なら `gemini`

`backend=ollama` で ollama に繋がらない場合は、Geminiへ落とさず警告して要約スキップ。
出先でコードを触れない前提なので、デフォルトを Gemini にしておけば十分。

技術パラメータ（temperature 等）は実装側の固定値。ユーザーが触るのは backend / model / URL / timeout だけ。

---

## 5. 実装ステップ（承認後のPR）

契約（`Item` / `SummarizerAdapter`）は変えない。変わるのは設定と実装差し替え。

### PR-1: 設定 + OllamaSummarizer + 本文抽出

変更予定:

- `src/my_feed/config.py` — `backend` / `OllamaConfig` / `get_backend()`
- `config.example.toml` / `config.toml`（example側のみ enabled 例）
- `src/my_feed/summarizer/html_text.py` — HTML → 本文（script/style/nav除去、上限500〜2000字）
- `src/my_feed/summarizer/ollama.py` — GET本文 → ollama generate
- `src/my_feed/summarizer/__init__.py`
- `tests/test_summarizer.py` / `tests/test_html_text.py` / `tests/test_config.py`（あれば）

`summarize(item)` の流れ:

1. `get_text(item.url)`（既存 `http_util`）
2. 本文抽出。失敗なら `item.excerpt`
3. プロンプト（タイトル・タグ・本文）を ollama へ
4. 失敗は例外を上げず `None`（既存 Protocol どおり）

### PR-2: pipeline 分岐 + ドキュメント

変更予定:

- `src/my_feed/pipeline/run.py` — `get_backend()` で Gemini / Ollama を構築
- `README.md` — デフォルトGemini、自宅は環境変数
- `docs/notes/ollama-setup.md` — インストール、`gemma4:e4b`、接続失敗時の見方
- `tests/test_summarizer_integration.py` — backend分岐（fake/mock）

実 ollama 呼び出しは opt-in（例: `MY_FEED_OLLAMA=1`）。CIの通常テストはネットワーク無し。

---

## 6. テスト

- HTML抽出: fixtures の HTML → テキスト
- OllamaSummarizer: httpx を mock。本文GET成功/失敗、API成功/失敗
- config: `backend` のデフォルトが `gemini`、環境変数が上書きする
- pipeline: Geminiキー無しでも落ちない（現状維持）、ollama未起動でも落ちない
- 回帰: 既存の Gemini / M1 / M2 テスト

---

## 7. 見送り（今回やらない）

| 項目 | 理由 |
|------|------|
| `Item.content_snippet` | C0変更。Top N 取得で足りる |
| 各Sourceでの全文取得 | 遅い。層の責任を超える |
| 自動 Gemini フォールバック | 意図せず課金したくない。デフォルトGeminiで足りる |
| 並行要約 | Protocolを async にする必要がある |
| 要約の永続化・再要約スキップ | Storeの契約拡張。別議論 |
| 常時稼働サーバー / VPN | ローカル維持の判断済み |

---

## 8. 判断ログ

| 項目 | 判断 | 理由 |
|------|------|------|
| デフォルト backend | Gemini | 出先で設定を触れない |
| 切り替え | 環境変数 `SUMMARIZER_BACKEND` | config編集より手元で切り替えやすい |
| 本文取得 | 要約時・Top N のみ | 全件取得は過剰 |
| 契約 | `Item` は変えない | 設定と summarizer 実装で閉じる |
| モデル | gemma4:e4b | stingray実績、軽量 |
| 失敗時 | スキップ | パイプラインを落とさない（既存方針） |

---

## 9. リスク

| リスク | 対策 |
|--------|------|
| ollama未起動 | 警告して要約スキップ。READMEに手順 |
| 記事HTMLがJS依存で空 | `excerpt` / タイトルにフォールバック |
| サイトがブロック | User-Agentは既存 `http_util` を使う。失敗は1件スキップ |
| Gemini経路の劣化 | backend分岐以外は触らない |

---

## 10. 完了条件（実装PR群）

- [ ] `backend` 未指定時は今と同じ Gemini
- [ ] `SUMMARIZER_BACKEND=ollama` で OllamaSummarizer が使われる
- [ ] ollama未起動でもパイプラインは継続
- [ ] 本文抽出と mock テストがある
- [ ] README に自宅/出先の使い分けがある
- [ ] `make ci` 相当が通る

---

## 11. 参考

- [stingray](https://github.com/ryochin/stingray) — `backend/summarizer.py`, `backend/fetcher.py`, `backend/llm.py`
- [Ollama](https://ollama.com/)
- [gemma4](https://ollama.com/library/gemma4)
