# 実装ルール

ステータス: **草案**
対象: このリポジトリでコードを書くとき（エージェント・人）の具体的な規約

関連: [collaboration.md](./collaboration.md)（全体方針）、[pr-review.md](./pr-review.md)（レビュー観点）、[reading-order.md](./reading-order.md)（コードを理解するときの読み順）

---

## 1. このドキュメントの使い方

- コードを書く前に該当する節を確認する
- 「なぜそうするか」が不明なら質問する
- ルールが変わったら日付付きで追記する

---

## 2. ファイル構造のルール

### 2.1 `base.py` は Protocol のみ

**各パッケージの `base.py` は Protocol / 契約のみを置く**

```text
✅ 良い例:
sources/
  base.py        # ← SourceAdapter Protocol のみ
  zenn.py        # ← Zenn の実装
  qiita.py       # ← Qiita の実装
  fake.py        # ← Fake 実装

❌ 悪い例:
sources/
  base.py        # ← Protocol と FakeSource 実装が同居
```

**理由**: `base.py` に実装を同居させると、後続トラックが実装をそこに足してしまいやすい。

**適用パッケージ**: `sources` / `scoring` / `output` / `store`

### 2.2 実装は役割名のファイルへ

実装は役割が分かるファイル名で分離する。

```text
output/
  markdown.py    # ← render_bundle / render_single 実装
store/
  memory.py      # ← InMemory 実装（Fake）
  sqlite.py      # ← SQLite 実装
```

---

## 3. 境界と責任

### 3.1 各層の責任

| 層 | 責任 | やらないこと |
|----|------|-------------|
| **Sources** | 外部取得 → 共通 Item へ正規化 | スコアリング、Top N 選定 |
| **Scoring** | Item[] → ScoredItem[]（降順） | 取得、UI、永続化 |
| **Output** | 結果の Markdown 化 | 取得、スコア計算 |
| **Store** | 履歴・お気に入りの永続化 | 取得、スコア計算 |
| **Web** | UI と導線 | パイプライン実装（注入のみ） |
| **Pipeline** | 上記を統合して実行 | 個別の取得・スコア・永続化ロジック |

### 3.2 よくある違反例

❌ **表示層が永続化の仕事をする**
❌ **取得層がスコアリングをする**
❌ **設定値が実行時に反映されない**

---

## 4. ドメインルール

### 4.1 生のいいね数での横断比較は禁止

❌ **Zenn のいいね数と GitHub の star 数を直接比較しない**
✅ **ソース内で正規化（minmax 等）してから横断ランキング**

**理由**: スケールが違いすぎて不公平。

**実装場所**: `scoring/normalize.py` で正規化してから横断評価。

### 4.2 1ソース失敗でも継続

- **partial 失敗** — `status=partial` + `source_errors={source: message}`
- **全ソース失敗** — `status=error` + 終了コード 1
- **1ソース失敗時** — 他が生きていれば終了コード 0

### 4.3 GitHub Trending は特に脆い

- **非公式 HTML スクレイピング** — 壊れやすい
- **モジュール隔離** — 他に影響しない構造
- **失敗時も他ソースで継続**

---

## 5. 契約変更のルール

### 5.1 契約を壊す変更は C0 を先に変更

**トラック PR で Protocol を静かに変えない**

手順:

1. 先に契約（`models` / `sources.base` / `scoring.base` / `output` / `store` / `pipeline`）を変える PR を出す
2. それをマージしてから、各トラック（T-Src 等）の実装 PR を追随させる
3. トラック PR だけで契約を壊さない
4. 層の増減や Protocol の入出力が変わったら、[reading-order.md](./reading-order.md) の「次のファイル」がまだ正しいかを見る

詳細: [docs/plans/tech-catchup/contracts/c0-contract-hub.md](../plans/tech-catchup/contracts/c0-contract-hub.md)

---

## 6. Fake 実装の扱い

### 6.1 Fake は並行開発の鍵

Fake は「消すべき恥」ではない。

- **T-Web は Fake pipeline で進められる** — 実ソース待ちにしない
- **M2 で本番配線に差し替える** — それまでは Fake でも可
- **ルート `config.toml` は `fake` のまま** — オフライン安全のため
- **実取得は `config.local.toml` をコピー** — `cp config.example.toml config.local.toml`

### 6.2 Fake を残す判断もある

デバッグ用、比較用として Fake を残すこともある（マイルストーンの意図次第）。

---

## 7. テストのルール

### 7.1 外部取得はパーステスト推奨

- **fixtures ベース** — ネットワーク無しで動く
- **エントリ単位のパース失敗をスキップ** — その件だけスキップして継続

### 7.2 ネットワークありテストは opt-in

```bash
# オフライン（Fake + fixtures）
uv run pytest

# ネットワークありテスト（opt-in）
MY_FEED_LIVE=1 uv run pytest -m network
```

---

## 8. コメントのルール

### 8.1 自明なコメントは書かない

❌ **書かないコメント**:

```python
# Import the module
import foo


# Define the function
def bar():
    pass


# Increment the counter
counter += 1
```

✅ **書くべきコメント**:

- 非自明な意図・トレードオフ
- なぜこの実装を選んだか
- 制約・前提条件

---

## 9. 設定と実行の一致

### 9.1 設定値が実際に効くことを確認

❌ **よくある問題**:

- `config.toml` に `half_life` があるが、戦略生成時に渡していない
- 運用でパラメータを変えても順位が変わらない

✅ **確認方法**:

- 設定変更後、実際に挙動が変わるかテストする
- レジストリやファクトリで設定を注入しているか確認

---

## 10. 外部ソースの扱い

### 10.1 取得手段の優先順位

1. **公式 RSS / 公開 API** — 最優先
2. **非公式 API / HTML スクレイピング** — 最終手段

### 10.2 非公式手段を選ぶ場合

- 理由を `docs/notes/sources.md` に残す
- モジュール隔離する
- 失敗時も他ソースで継続できる構造にする

---

## 変更履歴

| 日付 | 内容 |
|------|------|
| 2026-10-07 | 初版作成。AGENTS.md から実装ルールを分離 |
| 2026-10-09 | 契約変更時に reading-order.md の矢印を確認する手順を追加 |
