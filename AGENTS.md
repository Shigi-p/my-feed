# AGENTS.md — AIエージェント向けガイド

作成日: 2026-10-07  
ステータス: **草案**（運用しながら改善する）

---

## 1. このプロジェクトについて

### 1.1 プロジェクト概要

**my feed** は、技術記事とGitHub Trendingを効率よくキャッチアップするためのフィードアプリケーションです。

- **目的**: 複数の情報源から横断的に評価して**厳選Top 10**を表示
- **現在地**: **M2（ローカル完成）** まで到達。localhost で動作する完全なWebアプリケーション
- **次のステップ**: 任意で M3（運用改善）や M4（公開・発展）へ進む段階

### 1.2 技術スタック

- **言語**: Python 3.12+
- **パッケージ管理**: uv（`pyproject.toml` + `uv.lock`）
- **Web**: FastAPI + サーバサイドテンプレート（Jinja2）
- **DB**: SQLite（履歴・お気に入り）
- **情報源**: Zenn / Qiita / GIGAZINE / GitHub Trending
- **スコアリング**: popularity / recency / hybrid（複数戦略を差し替え可能）

### 1.3 段階的な発展計画

このプロジェクトは「ローカル完結」が最終目標ではありません：

| 段階 | 内容 | 状態 |
|------|------|------|
| M1 | CLI縦切り（実ソース取得 → Top 10） | ✅ 完了 |
| M2 | ローカル完成（Web UI + SQLite） | ✅ 完了 |
| M3 | 運用改善（設定化・フィルタ） | 任意 |
| M4 | 公開・発展（ホスティング・認証・Actions・AI要約・Drive連携） | 任意・選択的 |

M4では**必要な機能を選んで**実装します（一括ではない）。

---

## 2. このプロジェクトで大切にしていること

### 2.1 契約優先・並行開発モデル

このプロジェクトは「**契約ハブ + 並行トラック**」という届け方を採用しています。

```text
              [C0 契約ハブ]
                   |
  +--------+-------+--------+--------+
  |        |       |        |        |
[T-Src] [T-Score] [T-Md]  [T-Web] [T-Store]
  |        |       |        |        |
  +----[M1 CLI 縦切り]-----+ |        |
           |                |        |
           +-------[M2 ローカル完成]--+
                        |
                 [M3 運用改善]
                        |
                 [M4 公開・発展]
```

**重要な原則:**

1. **契約（C0）を先に固定する** — 型・Protocol・Fake実装を先に決める
2. **実装トラック（T-*）は契約に対してのみ依存** — 他トラックの完成を待たない
3. **Fake実装で並行開発を可能にする** — UIは実ソース待ちにせず、Fake pipelineで進める
4. **マイルストーン（M1/M2）で段階的に結合** — 「使える断面」を作る地点

### 2.2 学習重視のコミュニケーション

**計画 → 承認 → 実装**の順を崩さない。

- ❌ **いきなりコードを生成しない**
- ✅ **全体計画を先に示し、「実装してください」と言われたら小さいステップで進める**
- ✅ **判断が必要なときだけ聞く** — 機械的な修正は任せる、方針・トレードオフは確認する
- ✅ **コードより理由を重視** — 「なぜこの形か」「別案との差」を優先する
- ✅ **日本語で、短く、事実ベース** — 相槌や過剰な褒めは不要

### 2.3 契約変更の手順

**契約を壊す変更は、実装トラックより先に C0 を変更する**

1. 先に契約（`models` / `sources.base` / `scoring.base` / `output` / `store` / `pipeline`）を変える PR を出す
2. それをマージしてから、各トラック（T-Src 等）の実装 PR を追随させる
3. トラック PR だけで契約を壊さない

詳細: [docs/plans/tech-catchup/contracts/c0-contract-hub.md](./docs/plans/tech-catchup/contracts/c0-contract-hub.md)

---

## 3. アーキテクチャと設計原則

### 3.1 ディレクトリ構造の意図

```text
src/my_feed/
  models.py          # 共通データモデル（Item, ScoredItem, PipelineResult）
  sources/           # 取得トラック（T-Src）
    base.py            # ← Protocol のみ
    zenn.py            # ← 実装
    qiita.py
    gigazine.py
    github_trending.py
    fake.py            # ← 開発用
  scoring/           # スコアトラック（T-Score）
    base.py            # ← Protocol のみ
    popularity.py      # ← 実装
    recency.py
    hybrid.py
    fake.py
  output/            # Markdown トラック（T-Md）
    markdown.py
  store/             # 永続化トラック（T-Store）
    base.py            # ← Protocol のみ
    memory.py          # ← Fake 実装
    sqlite.py          # ← 本実装
  web/               # Web UI トラック（T-Web）
  pipeline/          # パイプライン実行
  cli.py             # CLI エントリポイント
```

### 3.2 `base.py` の役割（重要）

**各パッケージの `base.py` は Protocol / 契約のみ**

- ✅ Protocol の定義
- ✅ 型の export
- ❌ 実装の同居 ← **禁止**

**実装は役割名のファイルへ置く**（例: `output/markdown.py`, `store/sqlite.py`, `sources/zenn.py`）

理由: `base.py` に実装を同居させると、後続トラックが実装をそこに足してしまいやすい。

### 3.3 Fake 実装の位置づけ

Fake は「消すべき恥」ではなく、**並行開発の鍵**です。

- **T-Web は Fake pipeline で進められる** — 実ソース待ちにしない
- **M2 で本番配線に差し替える** — それまでは Fake でも可
- **ルート `config.toml` は `fake` のまま** — オフライン安全のため
- **実取得は `config.local.toml` をコピー** — `cp config.example.toml config.local.toml`

Fake を残す判断も取りうる（デバッグ用、比較用）。

### 3.4 境界と責任

| 層 | 責任 | やらないこと |
|----|------|-------------|
| **Sources** | 外部取得 → 共通 Item へ正規化 | スコアリング、Top N 選定 |
| **Scoring** | Item[] → ScoredItem[]（降順） | 取得、UI、永続化 |
| **Output** | 結果の Markdown 化 | 取得、スコア計算 |
| **Store** | 履歴・お気に入りの永続化 | 取得、スコア計算 |
| **Web** | UI と導線 | パイプライン実装（注入のみ） |
| **Pipeline** | 上記を統合して実行 | 個別の取得・スコア・永続化ロジック |

### 3.5 重要なドメインルール

#### 3.5.1 生のいいね数での横断比較は禁止

❌ **Zenn のいいね数と GitHub の star 数を直接比較しない**  
✅ **ソース内で正規化（minmax 等）してから横断ランキング**

理由: スケールが違いすぎて不公平。

実装場所: `scoring/normalize.py` で正規化してから横断評価。

#### 3.5.2 1ソース失敗でも継続

- **partial 失敗** — `status=partial` + `source_errors={source: message}`
- **全ソース失敗** — `status=error` + 終了コード 1
- **1ソース失敗時** — 他が生きていれば終了コード 0

#### 3.5.3 GitHub Trending は特に脆い

- **非公式 HTML スクレイピング** — 壊れやすい
- **モジュール隔離** — 他に影響しない構造
- **失敗時も他ソースで継続**

---

## 4. AIエージェントへの期待

### 4.1 やってほしいこと

✅ **計画を先に示す** — 全体の流れ、変更箇所、トレードオフを説明  
✅ **小さいステップで進める** — 一度に大量のコードを生成しない  
✅ **境界と責任を守る** — 表示層が永続化の仕事をしない、など  
✅ **契約と実装のズレをチェック** — Protocol の意味と実装が一致しているか  
✅ **base.py を汚さない** — Protocol だけ、実装は別ファイル  
✅ **テストを書く** — 特に外部取得のパーステスト（fixtures 推奨）  
✅ **設定と実行の一致を確認** — `config.toml` のパラメータが実際に効くか  

### 4.2 やってほしくないこと

❌ **いきなりコードを出す** — 計画なしで実装を始めない  
❌ **契約を静かに変える** — トラック PR で Protocol を勝手に変えない  
❌ **base.py に実装を同居** — Protocol と実装を分離する  
❌ **生のいいね数で横断比較** — 正規化を経由する  
❌ **過剰なコメント** — 「// Import the module」などの自明なコメント不要  
❌ **無意味な相槌** — 「鋭い指摘ですね」などの評価的な応答  

### 4.3 判断を求めるタイミング

**機械的な修正は任せる。以下のときだけ確認:**

- 方針・トレードオフが分かれる点（「どちらの設計が良いか」）
- 契約変更が必要そうなとき（「C0 を先に変えるべきか」）
- 外部 API の選択（「公式 API vs 非公式スクレイピング」）
- セキュリティ・認証の方針
- 新しいツール・依存の導入（Docker, ORM など）

---

## 5. レビュー観点（重要なチェック項目）

### 5.1 普遍的な観点

- **境界と責任** — この変更はどの層の責任か明確か
- **契約と実装のズレ** — Protocol の意味と実装が一致しているか
- **結合で初めて壊れるもの** — 設定が実際に配線されているか
- **外部世界との接点** — 非公式 API / HTML スクレイピングの脆さと代替手段
- **データ同一性** — 再取得しても安定して同一とみなせる ID か

### 5.2 このプロジェクト特有の観点

#### 5.2.1 契約ハブを壊していないか

- C0 のモデル / Protocol の意味を、トラック PR が静かに変えていないか
- 変える必要があるなら **契約変更を先出し**できているか

#### 5.2.2 ファイル命名（base.py）

- 各パッケージの `base.py` は Protocol / 契約のみ
- 実装は役割名のファイルへ置く

#### 5.2.3 スコアとソースの公平性

- 生のいいね数・星の数をソース横断で比べていないか（禁止方針）
- ソース内件数 1 のときの正規化が、横断ランキングを歪めないか

#### 5.2.4 外部ソース方針

- RSS / 公式 API を捨てて非公式手段を選ぶ場合、理由が notes に残っているか
- GitHub Trending など壊れやすい部品が **モジュール隔離**されているか

詳細: [docs/guides/pr-review.md](./docs/guides/pr-review.md)

---

## 6. よくある参照先

### 6.1 計画ドキュメント

- **ロードマップ**: [docs/plans/tech-catchup/2026-10-06-roadmap.md](./docs/plans/tech-catchup/2026-10-06-roadmap.md)
- **届け方モデル**: [docs/plans/tech-catchup/delivery-model.md](./docs/plans/tech-catchup/delivery-model.md)
- **契約ハブ（C0）**: [docs/plans/tech-catchup/contracts/c0-contract-hub.md](./docs/plans/tech-catchup/contracts/c0-contract-hub.md)

### 6.2 ガイド

- **協働方針**: [docs/guides/collaboration.md](./docs/guides/collaboration.md)
- **PR レビュー観点**: [docs/guides/pr-review.md](./docs/guides/pr-review.md)

### 6.3 トラック

- **T-Src（取得）**: [docs/plans/tech-catchup/tracks/t-src.md](./docs/plans/tech-catchup/tracks/t-src.md)
- **T-Score（スコア）**: [docs/plans/tech-catchup/tracks/t-score.md](./docs/plans/tech-catchup/tracks/t-score.md)
- **T-Md（Markdown）**: [docs/plans/tech-catchup/tracks/t-md.md](./docs/plans/tech-catchup/tracks/t-md.md)
- **T-Web（Web UI）**: [docs/plans/tech-catchup/tracks/t-web.md](./docs/plans/tech-catchup/tracks/t-web.md)
- **T-Store（永続化）**: [docs/plans/tech-catchup/tracks/t-store.md](./docs/plans/tech-catchup/tracks/t-store.md)

### 6.4 マイルストーン

- **M1（CLI 縦切り）**: [docs/plans/tech-catchup/milestones/m1-cli.md](./docs/plans/tech-catchup/milestones/m1-cli.md)
- **M2（ローカル完成）**: [docs/plans/tech-catchup/milestones/m2-local.md](./docs/plans/tech-catchup/milestones/m2-local.md)
- **M3（運用改善）**: [docs/plans/tech-catchup/milestones/m3-ops.md](./docs/plans/tech-catchup/milestones/m3-ops.md)
- **M4（公開・発展）**: [docs/plans/tech-catchup/milestones/m4-optional.md](./docs/plans/tech-catchup/milestones/m4-optional.md)

---

## 7. 開発フロー

### 7.1 セットアップ

```bash
# uv がない場合: https://docs.astral.sh/uv/getting-started/installation/
uv sync --extra dev
```

### 7.2 ローカル実行

```bash
# 初回のみ（実ソース + hybrid）
cp config.example.toml config.local.toml

# Web サーバー起動
uv run my-feed serve

# 開く: http://127.0.0.1:8000/
```

### 7.3 CLI 実行

```bash
uv run my-feed run --config config.local.toml
uv run my-feed run --config config.local.toml --scorer popularity --top 10
uv run my-feed run --config config.local.toml --json --out /tmp/feed.json
uv run my-feed run --config config.local.toml --out-md /tmp/feed.md
```

### 7.4 テスト

```bash
# オフライン（Fake + fixtures）
uv run pytest

# ネットワークありテスト（opt-in）
MY_FEED_LIVE=1 uv run pytest -m network
```

---

## 8. 一文での要約

> 先に契約と計画を共有し、承認した範囲だけ小さく実装する。コードの量より「なぜ」を残し、判断以外は任せ、差し替え可能な形で、学習しながら並行に進めたい。

---

## 変更履歴

| 日付 | 内容 |
|------|------|
| 2026-10-07 | 初版作成。docs/plans、コード実体、既存ガイドから抽出 |
