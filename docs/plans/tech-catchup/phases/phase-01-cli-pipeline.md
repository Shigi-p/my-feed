# Phase 1 — CLI 取得パイプライン（B）

| 項目 | 内容 |
|------|------|
| ステータス | 計画承認待ち → マージ後に着手 |
| 依存 | Phase 0 完了（計画マージ） |
| 後続 | Phase 2（Markdown） |
| ゴール | 1 コマンドで 4 ソース取得 → スコア → Top 10 が再現可能に出る |

---

## 1. 目的

取得と評価のコアを **CLI だけで** 固める。Web・DB・Markdown 本格テンプレには手を出さない。

理由: UI より先に「取れる・選べる・差し替えられる」を検証した方が、アダプタ／スコアラーの境界が壊れにくい。

---

## 2. スコープ

### やること

- プロジェクト骨格（Python）
- 共通 `Item` モデル
- Source Adapter 枠 + 4 ソース実装
- Score Strategy 枠 + 初期 3 戦略
- `fetch → score → top N` CLI
- 最低限の手動確認手順（README）

### やらないこと

- FastAPI / HTML UI
- SQLite / お気に入り
- Gemini 向け Markdown 本格テンプレ（簡易 JSON/表出力まで）
- AI 要約、Drive、認証、Actions
- GIGAZINE 技術フィルタ

---

## 3. 技術決定（このフェーズで固定する案）

| 項目 | 仮決め | 変更容易性 |
|------|--------|------------|
| 言語 | Python 3.12+ | 低（以降固定） |
| パッケージ管理 | **uv**（`pyproject.toml`） | 中 |
| モデル | pydantic v2 | 中 |
| HTTP | `httpx` | 高 |
| RSS/Atom | `feedparser` | 高 |
| CLI | `typer` または argparse（推奨: typer） | 高 |
| 設定 | `config.toml` or YAML + 環境変数オーバーライド | 高 |
| テスト | pytest（アダプタはフィクスチャ／録音レスポンス優先） | 高 |

レビューで異論があれば Phase 0 PR 内で修正する。

---

## 4. 想定ディレクトリ構成（このフェーズ終了時）

```
README.md
pyproject.toml
config.toml                 # 有効ソース、top_n、default_scorer
src/my_feed/
  __init__.py
  models.py                 # Item, SourceName, ScoredItem
  config.py                 # 設定読み込み
  sources/
    __init__.py             # レジストリ
    base.py                 # SourceAdapter Protocol / ABC
    zenn.py
    qiita.py
    gigazine.py
    github_trending.py
  scoring/
    __init__.py             # レジストリ
    base.py                 # ScoreStrategy Protocol / ABC
    normalize.py            # ソース内正規化
    popularity.py
    recency.py
    hybrid.py
  pipeline/
    __init__.py
    run.py                  # fetch → score → top_n
  cli.py                    # エントリポイント
tests/
  fixtures/                 # サンプル RSS / HTML
  test_scoring_normalize.py
  test_pipeline_top_n.py
  # アダプタはネットワーク無しテストを優先
```

パッケージ名 `my_feed` は仮。レビューで変更可。

---

## 5. データモデル詳細

### 5.1 `Item`

| フィールド | 型（案） | 必須 | 説明 |
|------------|----------|------|------|
| `id` | `str` | yes | `{source}:{stable_key}` |
| `source` | enum | yes | `zenn` / `qiita` / `gigazine` / `github_trending` |
| `title` | `str` | yes | |
| `url` | `str` | yes | |
| `published_at` | `datetime \| None` | no | timezone-aware 推奨 |
| `excerpt` | `str` | no | 生抜粋（整形は Phase 2） |
| `tags` | `list[str]` | no | |
| `metrics` | `dict[str, float \| int]` | no | 例: `liked_count`, `stocks`, `stars` |
| `fetched_at` | `datetime` | yes | パイプライン実行時刻 |

`raw` はデバッグ時のみ保持し、本番パスでは捨ててよい（メモリ・ログ肥大防止）。

### 5.2 `ScoredItem`

| フィールド | 説明 |
|------------|------|
| `item` | 元 `Item` |
| `score` | 横断比較用の最終スコア（float） |
| `score_breakdown` | 内訳（正規化人気、recency 係数など）辞書 |

### 5.3 ID 生成ルール

1. 公式 ID がある → `source:{official_id}`
2. なければ正規化した URL のハッシュ短絡 → `source:url:{sha256_12}`
3. 同一実行内で衝突したらログ警告（後勝ち or スキップを設定で固定）

---

## 6. Source Adapter 詳細

### 6.1 インターフェース

```text
class SourceAdapter(Protocol):
    name: SourceName
    def fetch(self) -> list[Item]: ...
```

- `fetch` は成功時のみ Item を返す
- 例外はパイプライン側で捕捉し、**他ソース継続**
- アダプタ内で「空リスト」と「例外」を区別できるよう、一時障害は例外、真に 0 件は空リスト

### 6.2 レジストリ

- `SOURCES: dict[SourceName, SourceAdapter]`
- `config.toml` の `enabled_sources` で絞る
- 追加手順: モジュール追加 → レジストリ登録 → 設定に名前を足す

### 6.3 各ソース実装方針

| ソース | 取得手段（第1候補） | metrics の例 | 備考 |
|--------|---------------------|--------------|------|
| Zenn | 公開トレンド/フィード（RSS or 公開 API） | likes 等 | 公式で取れる経路を調査して決定。スクレイピングは最終手段 |
| Qiita | 公開 API or RSS | likes / stocks | レート制限・トークン要否を Phase 1 着手時に確認 |
| GIGAZINE | サイト RSS | なし（recency 寄り） | フィルタなし。metrics 欠落を許容 |
| GitHub Trending | 非公式 HTML or 既知の代替フィード | stars / forks（取れる範囲） | **隔離モジュール**。失敗してもパイプライン全体は成功扱い |

着手時に「実際に使えるエンドポイント」を短い調査メモとして `docs/plans/tech-catchup/` か `docs/notes/` に残してよい（実装 PR 内）。

### 6.4 エラー方針

| 事象 | 挙動 |
|------|------|
| 1 ソース HTTP 失敗 | 警告ログ + そのソース 0 件、続行 |
| 全ソース失敗 | CLI 終了コード非 0 |
| パース失敗（一部エントリ） | そのエントリをスキップ、ソース全体は継続 |

---

## 7. Score Strategy 詳細

### 7.1 インターフェース

```text
class ScoreStrategy(Protocol):
    name: str
    def score(self, items: list[Item]) -> list[ScoredItem]: ...
```

戻り値は **スコア降順**。パイプライン側で `top_n` を切る。

### 7.2 正規化（必須コンポーネント）

`normalize.py` の責務:

1. ソースごとにグループ化
2. そのソース内で人気指標を 0〜1 に正規化（ランク or min-max）
3. metrics が無いソース（GIGAZINE 等）は **中立値（例: 0.5）** または recency のみで勝負できるよう戦略側で扱う

**禁止**: 生のいいね数をソース横断で直接比較すること。

### 7.3 初期戦略

| name | 計算（初期案） |
|------|----------------|
| `popularity` | ソース内正規化人気のみ |
| `recency` | `published_at` からの時間減衰（欠落はペナルティ or 中立） |
| `hybrid` | `norm_popularity * recency_factor`（デフォルト） |

パラメータ（半減期など）は `config.toml` に置き、Phase 4 で触りやすくする。Phase 1 ではハードコード＋設定1箇所で可。

### 7.4 CLI からの選択

```bash
my-feed run --scorer hybrid --top 10
my-feed run --scorer popularity --json
```

---

## 8. パイプライン / CLI

### 8.1 処理フロー

```
load config
 → enabled adapters を並列 or 直列 fetch（初期は直列でよい）
 → 結合
 → selected scorer.score
 → top_n
 → stdout（table 既定 / --json）
 → 任意で --out result.json
```

### 8.2 コマンド案

| コマンド | 説明 |
|----------|------|
| `my-feed run` | 本流 |
| `my-feed sources` | 登録ソース一覧 |
| `my-feed scorers` | 登録スコアラー一覧 |

### 8.3 出力（Phase 1 最低限）

表形式例:

```
rank | score | source | title | url
```

JSON は後続 Phase 2/3 が消費しやすい形（`ScoredItem` の配列）。

---

## 9. タスク分解（実装順序）

ワークツリー作成後、この順で小さく進める。各タスクに完了条件を付ける。

### T1. リポジトリ骨格

- [ ] `pyproject.toml` / パッケージレイアウト
- [ ] `config.toml`（`enabled_sources`, `top_n=10`, `default_scorer=hybrid`）
- [ ] README に「インストールと `my-feed run`」を追記
- **完了**: 空コマンドまたは hello が動く

### T2. 共通モデルと設定

- [ ] `Item` / `ScoredItem` / `SourceName`
- [ ] 設定ローダ
- **完了**: ユニットテストでモデル生成ができる

### T3. Source Adapter 枠

- [ ] `base.py` + レジストリ
- [ ] パイプラインでの例外隔離
- **完了**: 偽アダプタ 2 つで結合取得できる

### T4. アダプタ実装（ソースごと PR コミット単位でも可）

- [ ] Zenn
- [ ] Qiita
- [ ] GIGAZINE
- [ ] GitHub Trending（失敗耐性込み）
- **完了**: 単体で `fetch()` が 1 件以上返る（または意図的スキップ理由がログに出る）

### T5. Score Strategy 枠 + 3 戦略

- [ ] 正規化ヘルパ + テスト
- [ ] popularity / recency / hybrid
- **完了**: フィクスチャ Item 列で順位が説明可能

### T6. パイプライン CLI 統合

- [ ] `run` コマンド
- [ ] table / json / `--out`
- **完了**: 実ネットワークで Top 10 が出る

### T7. 手動確認チェックリスト消化

- [ ] 全ソース有効で 10 件
- [ ] scorer 切替で順位が変わる（または説明可能な同順）
- [ ] GitHub Trending を無効化 or 擬似障害でも全体成功
- **完了**: README の「動作確認」節が実行可能

---

## 10. テスト方針

| 種類 | 対象 | 方針 |
|------|------|------|
| ユニット | 正規化・hybrid 計算 | 必須 |
| ユニット | パイプライン top_n | 偽アダプタで必須 |
| 契約寄り | 各アダプタのパース | fixtures を使いネットワーク無しを推奨 |
| 手動 | 実 fetch | T7 |

CI は Phase 1 では任意（無くても可）。入れるならネットワーク無しテストのみ。

---

## 11. 完了条件（Exit Criteria）

- [ ] `my-feed run` 相当で Top 10 がローカル表示される
- [ ] `--scorer` で戦略切替できる
- [ ] ソース追加が「アダプタ 1 つ + レジストリ + 設定」で済む構造になっている
- [ ] 1 ソース失敗でも（他が生きていれば）結果が返る
- [ ] README から再現できる
- [ ] Phase 2 が消費できる JSON 形が決まっている

---

## 12. worktree / ブランチ提案

- ブランチ例: `cursor/phase-01-cli-pipeline-<suffix>`
- ベース: 計画マージ後の `main`
- このフェーズの PR 説明には、T1〜T7 のどれまで完了したかを書く

---

## 13. リスク（Phase 1 固有）

| リスク | 緩和 |
|--------|------|
| Qiita/Zenn の取得経路が想定と違う | T4 着手時に最短調査。RSS に落とす |
| Trending がすぐ壊れる | アダプタ隔離 + 設定で disable |
| スコアが感覚と合わない | 戦略を複数用意し、質の議論は運用後（Phase 4） |
| 範囲膨張（UI に手を出す） | Exit Criteria 以外は拒否 |

---

## 14. 次フェーズへの引き渡し

Phase 2 に渡すもの:

- `list[ScoredItem]`（または同等 JSON）
- `Item` の `excerpt` / `tags` / `metrics` / `score_breakdown`
- CLI から同じパイプライン関数を呼ぶ入口（Web からも後で呼ぶ）
