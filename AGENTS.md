# AGENTS.md — AIエージェント向けガイド

**このドキュメントの目的**: AIエージェントが、このリポジトリで何に気をつけて振る舞うべきか、必要な情報がどこにあるかを示す。

ステータス: **草案**（運用しながら改善する）

---

## 1. プロジェクト概要

**my feed** — 技術記事とGitHub Trendingのキャッチアップフィード。今の位置と使い方は [README.md](./README.md)。未着手は [GitHub Issues](https://github.com/Shigi-p/my-feed/issues)。

---

## 2. 基本姿勢

このプロジェクトでは以下を重視しています：

- **計画 → 承認 → 実装** の順を崩さない
- **コードより理由** — なぜその形にするか、別案との差を優先
- **判断が必要なときだけ聞く** — 機械的な修正は任せられる
- **小さいステップで進める** — 一度に大量のコードを生成しない
- **日本語で、短く、事実ベース** — 相槌や過剰な褒めは不要

詳細: [docs/guides/collaboration.md](./docs/guides/collaboration.md)

---

## 3. 新しいタスクを受けたら

### 3.1 まず計画を示す

いきなりコードを書かず、以下を示してください：

- 全体の流れ
- 変更箇所
- トレードオフ
- 不明点があれば質問

### 3.2 関連ドキュメントを確認

タスクに応じて該当する情報を確認：

| 確認すべきこと | 参照先 |
|--------------|--------|
| **今の位置・使い方** | [README.md](./README.md) |
| **未着手の仕事** | [GitHub Issues](https://github.com/Shigi-p/my-feed/issues) |
| **協働方針（進め方・学習姿勢）** | [docs/guides/collaboration.md](./docs/guides/collaboration.md) |
| **実装ルール（base.py・境界・ドメインルール）** | [docs/guides/implementation.md](./docs/guides/implementation.md) |
| **コードの読み順（理解するとき）** | [docs/guides/reading-order.md](./docs/guides/reading-order.md) |
| **レビュー観点（PR前チェック）** | [docs/guides/pr-review.md](./docs/guides/pr-review.md) |

### 3.3 承認されたら小さく実装

計画が承認されたら、小さいステップで進めてください。

---

## 4. 実装時の注意点（概要）

詳細は [docs/guides/implementation.md](./docs/guides/implementation.md) にありますが、特に重要な点：

### 4.1 必ず守ること

- ❌ **`base.py` に実装を書かない** — Protocol のみ、実装は別ファイル
- ❌ **契約を静かに変えない** — 型の正本はコード（`models.py` / 各 `base.py`）。意味が変わる変更は実装 PR に混ぜない
- ❌ **生のいいね数で横断比較しない** — ソース内正規化してから横断ランキング

### 4.2 推奨すること

- ✅ **境界と責任を守る** — 各層の責任を明確に（取得・スコア・出力・永続化・UI）
- ✅ **テストを書く** — 特に外部取得は fixtures ベースのパーステスト
- ✅ **設定と実行の一致を確認** — `config.toml` のパラメータが実際に効くか

---

## 5. 判断を求めるタイミング

機械的な修正は任せられますが、以下のときは確認してください：

- 方針・トレードオフが分かれる点（設計の選択）
- 契約変更が必要そうなとき（`models.py` / 各 `base.py` を先に変えるべきか）
- 外部 API の選択（公式 API vs 非公式スクレイピング）
- セキュリティ・認証の方針
- 新しいツール・依存の導入（Docker, ORM など）

---

## 6. コミット前の最小チェック

- [ ] 計画と一致しているか
- [ ] [実装ルール](./docs/guides/implementation.md) を守っているか
- [ ] [レビュー観点](./docs/guides/pr-review.md) の該当項目を確認したか
- [ ] テストは書いたか（該当する場合）

---

## 7. 困ったときの参照先

| 知りたいこと | 参照先 |
|------------|--------|
| プロジェクトの現在地・使い方 | [README.md](./README.md) |
| 未着手の仕事 | [GitHub Issues](https://github.com/Shigi-p/my-feed/issues) |
| 進め方・学習姿勢 | [docs/guides/collaboration.md](./docs/guides/collaboration.md) |
| 実装の具体的なルール | [docs/guides/implementation.md](./docs/guides/implementation.md) |
| コードをどの順で読むか | [docs/guides/reading-order.md](./docs/guides/reading-order.md) |
| PR レビュー観点 | [docs/guides/pr-review.md](./docs/guides/pr-review.md) |

---

## 変更履歴

| 日付 | 内容 |
|------|------|
| 2026-10-07 | 初版作成 |
| 2026-10-07 | メタ情報とナビゲーションだけに削減。実装ルールは implementation.md に分離 |
| 2026-10-09 | 参照先にコードの読み順（reading-order.md）を追加 |
| 2026-10-09 | 計画 md をやめ、今の位置は README、未着手は Issues |
