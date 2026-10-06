# tech-catchup 計画メモ

技術キャッチアップ支援ツール（リポジトリ名: **my feed**）の開発計画を堆積する場所。

## このディレクトリの使い方

- 日付付きで計画・方針メモを追加していく
- 実装の詳細ログではなく、「なぜこの方針か」「次に何をするか」を残す
- 方針が変わったら、旧ファイルは消さず、新しい日付のメモで上書き判断を記録する
- 実装の進め方は **契約ハブ + 並行トラック**（[delivery-model.md](./delivery-model.md)）

## まず読む順番（レビュー用）

1. [2026-10-06-roadmap.md](./2026-10-06-roadmap.md) — 全体方針・要件
2. [delivery-model.md](./delivery-model.md) — 届け方（契約 / トラック / マイルストーン）
3. [contracts/](./contracts/README.md) → [tracks/](./tracks/README.md) → [milestones/](./milestones/README.md)
4. [APPROVAL.md](./APPROVAL.md) — この PR の承認チェックリスト

## ドキュメント一覧

| ファイル / ディレクトリ | 内容 |
|-------------------------|------|
| [APPROVAL.md](./APPROVAL.md) | 計画 PR の承認チェックリスト |
| [2026-10-06-roadmap.md](./2026-10-06-roadmap.md) | 初回ロードマップ（要件・アーキテクチャ） |
| [delivery-model.md](./delivery-model.md) | 契約ハブ + 並行トラックの説明 |
| [contracts/](./contracts/README.md) | C0 契約ハブ詳細 |
| [tracks/](./tracks/README.md) | T-Src / T-Score / T-Md / T-Web / T-Store |
| [milestones/](./milestones/README.md) | M1〜M4 合流点 |
| [../../guides/pr-review.md](../../guides/pr-review.md) | PR レビュー観点（草案） |

## 現在の位置

**計画レビュー（本 PR）** → マージ後は **C0（契約ハブ）** から着手  
C0 完了後、T-Src / T-Score / T-Md / **T-Web** / T-Store を並行 worktree で開始してよい
