# C0 — 契約ハブ

| 項目 | 内容 |
|------|------|
| ステータス | **完了**（`main` 合流済み） |
| 依存 | 計画ドキュメントのマージ |
| 後続 | 全トラックが並行着手可能になる |
| ゴール | 他トラックが import できる契約（型・Protocol・スタブ）がある |

---

## 1. 目的

実装の中身より先に **境界と署名** を固定する。
これ以降、T-Web などは Fake 実装で UI を進められる。

---

## 2. スコープ

### やること

- プロジェクト骨格（Python / uv / `pyproject.toml`）
- 共通モデル: `Item`, `ScoredItem`, `PipelineResult`, `SourceName`
- Protocol: `SourceAdapter`, `ScoreStrategy`
- （任意だが推奨）`MarkdownRenderer`, `RunStore`, `FavoriteStore` の Protocol
- `run_pipeline(...)` の署名 + **Fake 実装**（固定の数件を返す）
- 設定の最小形（`enabled_sources`, `top_n`, `default_scorer`）
- レジストリの枠（空 or Fake 登録）
- 契約を説明する短い README 節

### やらないこと

- 実ソース取得（T-Src）
- 本スコア計算（T-Score）
- 本 Markdown テンプレ（T-Md）
- FastAPI UI（T-Web）
- SQLite 本実装（T-Store）

---

## 3. 技術決定（ここで仮固定）

| 項目 | 仮決め |
|------|--------|
| 言語 | Python 3.12+ |
| パッケージ管理 | **uv**（`pyproject.toml` + 可能なら `uv.lock`） |
| 開発環境 | **当面はホスト上の uv**。Docker は C0 では作らない |
| コンテナ | 必要になったら追加（イメージ内でも uv を使う想定）。M4 や環境差分が痛くなったタイミング |
| モデル | pydantic v2 |
| HTTP（後続用） | `httpx`（C0 では未使用でも依存に含めてよい） |
| RSS（後続用） | `feedparser` |
| CLI 枠 | `typer`（`run` は Fake で動かす） |
| 設定 | `config.toml` |
| テスト | pytest |

理由の要約: 短期はフィードバック速度と worktree 並行を優先。Python 依存の再現は `uv.lock` でまず担保し、OS/実行環境まで固定したくなったら Docker を後付けする。

---

## 4. ディレクトリ骨格（C0 終了時）

```text
README.md
pyproject.toml
config.toml
src/my_feed/
  __init__.py
  models.py
  config.py
  sources/
    base.py          # SourceAdapter Protocol
    __init__.py      # registry（Fake 可）
    fake.py
  scoring/
    base.py          # ScoreStrategy Protocol
    __init__.py
    fake.py
  pipeline/
    run.py           # run_pipeline 署名 + Fake
  output/
    base.py          # MarkdownRenderer Protocol のみ
    markdown.py      # render_bundle / render_single 実装（C0 stub → T-Md）
  store/
    base.py          # RunStore / FavoriteStore Protocol のみ
    memory.py        # InMemory 実装（Fake）
    sqlite.py        # SQLite 実装（T-Store）
  cli.py
tests/
  test_contracts_smoke.py
```

パッケージ名 `my_feed` は仮。変更可だが C0 で決めて以降は安易に変えない。

---

## 5. データモデル契約

### 5.1 `Item`

| フィールド | 型（案） | 必須 | 説明 |
|------------|----------|------|------|
| `id` | `str` | yes | `{source}:{stable_key}` |
| `source` | enum | yes | `zenn` / `qiita` / `gigazine` / `github_trending` |
| `title` | `str` | yes | |
| `url` | `str` | yes | |
| `published_at` | `datetime \| None` | no | timezone-aware 推奨 |
| `excerpt` | `str` | no | |
| `tags` | `list[str]` | no | |
| `metrics` | `dict[str, float \| int]` | no | likes / stocks / stars 等 |
| `fetched_at` | `datetime` | yes | |

### 5.2 `ScoredItem`

| フィールド | 説明 |
|------------|------|
| `item` | `Item` |
| `score` | 横断比較用 float |
| `score_breakdown` | 内訳 dict |

### 5.3 `PipelineResult`

| フィールド | 説明 |
|------------|------|
| `items` | Top N の `ScoredItem` リスト |
| `scorer` | 使用戦略名 |
| `fetched_at` | 実行時刻 |
| `source_errors` | `{source: message}`（空でも可） |
| `status` | `ok` / `partial` / `error` |

### 5.4 ID 生成ルール

1. 公式 ID があれば `source:{official_id}`
2. なければ正規化 URL のハッシュ → `source:url:{sha256_12}`

---

## 6. Protocol 契約

```text
SourceAdapter:
  name: SourceName
  fetch() -> list[Item]

ScoreStrategy:
  name: str
  score(items: list[Item]) -> list[ScoredItem]   # 降順

run_pipeline(config) -> PipelineResult

render_bundle(items, meta) -> str
render_single(item, meta) -> str

RunStore:
  save_run(result) -> run_id
  list_runs() / get_run(id)

FavoriteStore:
  add(item) / list() / remove(id)
```

意味の約束:

- 1 ソース失敗でも pipeline は継続し、`source_errors` に残す
- 生のいいね数での横断比較はしない（正規化は T-Score の責務だが、契約コメントに明記）
- 要約 AI は契約に含めない（将来は別フィールド / 出力層）

---

## 7. タスク分解

### T1. 骨格

- [ ] uv + pyproject + パッケージレイアウト
- [ ] config 最小
- **完了**: import / hello CLI が動く

### T2. モデル

- [ ] Item / ScoredItem / PipelineResult / SourceName
- **完了**: ユニットで生成できる

### T3. Protocol + Fake

- [ ] Source / Score / output / store の署名
- [ ] Fake 実装
- **完了**: `run_pipeline` が Fake で 10 件相当を返す

### T4. CLI 枠

- [ ] `my-feed run`（Fake）
- [ ] `sources` / `scorers` 一覧（登録枠）
- **完了**: 他トラックが「動く骨格」に対して PR を出せる

### T5. 契約スモークテスト

- [ ] Fake パイプラインの形が崩れないテスト
- **完了**: CI 無しでも `pytest` ローカルで確認可能

---

## 8. 完了条件（Exit Criteria）

- [ ] 上記モデルと Protocol がコード上に存在する
- [ ] Fake で `run_pipeline` が呼べる
- [ ] T-Src / T-Score / T-Md / T-Web / T-Store が **同じ契約を見て** 並行着手できる
- [ ] 契約変更の手順（C0 先出し）が README か本ディレクトリに書いてある

---

## 9. worktree

- ブランチ例: `cursor/c0-contract-hub-<suffix>`
- 短命を目指す。広げすぎない
