# Phase 0 — 設計固定

| 項目 | 内容 |
|------|------|
| ステータス | 本 PR で完了させる |
| 依存 | なし |
| 成果物 | `docs/plans/tech-catchup/` 配下の計画ドキュメント一式 |
| 実装コード | **作らない** |

---

## 1. 目的

実装に入る前に、目的・境界・フェーズ分割・詳細実装計画を文書化し、レビューで合意する。

---

## 2. このフェーズでやること

1. 全体ロードマップの確定（要件・アーキテクチャ・リスク）
2. 各フェーズの詳細実装計画の作成
3. 承認チェックリストの提示
4. マージ後の worktree 運用方針の明文化

## 3. やらないこと

- アプリケーションコードの追加
- 依存パッケージの導入
- 外部 API / RSS の実装検証（Phase 1 で行う）
- ホスティング・認証・AI・Drive

---

## 4. 成果物一覧

```
docs/plans/tech-catchup/
  README.md
  APPROVAL.md
  2026-10-06-roadmap.md
  phases/
    README.md
    phase-00-design.md          ← 本ファイル
    phase-01-cli-pipeline.md
    phase-02-markdown.md
    phase-03-local-web.md
    phase-04-ops-tuning.md
    phase-05-publish-and-ai.md
```

---

## 5. 完了条件（Exit Criteria）

- [ ] ロードマップと全フェーズ詳細がリポジトリ上にある
- [ ] [APPROVAL.md](../APPROVAL.md) の観点でレビューできる
- [ ] レビュー指摘があれば計画ドキュメントを修正済み
- [ ] PR がマージされ、`main` に計画が残っている

---

## 6. マージ後の引き継ぎ

1. `main` を最新化
2. Phase 1 用 worktree / ブランチを作成
3. [phase-01-cli-pipeline.md](./phase-01-cli-pipeline.md) のタスク順に実装開始

方針変更時は日付付きメモを `docs/plans/tech-catchup/` に追加し、該当 phase ファイルを更新する。
