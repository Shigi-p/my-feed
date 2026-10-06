# フェーズ別 詳細実装計画

親ドキュメント: [../2026-10-06-roadmap.md](../2026-10-06-roadmap.md)

このディレクトリは、ロードマップ各フェーズの **実装計画（何を・どの順で・何ができたら完了か）** を置く場所。  
コードはここには置かない。マージ後はフェーズ単位で worktree / ブランチを切って実装する想定。

## 読み方

1. まず [ロードマップ](../2026-10-06-roadmap.md) で全体像を把握する
2. 各 `phase-XX-*.md` で詳細を確認する
3. [承認チェックリスト](../APPROVAL.md) で PR マージ可否を判断する

## フェーズ一覧

| ファイル | フェーズ | 内容 | 実装着手 |
|----------|----------|------|----------|
| [phase-00-design.md](./phase-00-design.md) | Phase 0 | 設計固定・本 PR の範囲 | ドキュメントのみ（進行中） |
| [phase-01-cli-pipeline.md](./phase-01-cli-pipeline.md) | Phase 1 | CLI 取得パイプライン（B） | マージ後・最初の worktree |
| [phase-02-markdown.md](./phase-02-markdown.md) | Phase 2 | Markdown / 壁打ち体裁 | Phase 1 完了後 |
| [phase-03-local-web.md](./phase-03-local-web.md) | Phase 3 | ローカル Web + 履歴・お気に入り（A） | Phase 2 完了後 |
| [phase-04-ops-tuning.md](./phase-04-ops-tuning.md) | Phase 4 | 運用改善・設定化 | Phase 3 運用後 |
| [phase-05-publish-and-ai.md](./phase-05-publish-and-ai.md) | Phase 5 | 公開・認証・AI・Drive 等 | 必要になったら |

## worktree 運用（マージ後の想定）

- ベース: `main`（本計画マージ後）
- 推奨ブランチ例:
  - `cursor/phase-01-cli-pipeline-xxxx`
  - `cursor/phase-02-markdown-xxxx`
  - …
- 原則 **1 worktree = 1 フェーズ**。前フェーズの完了条件を満たしてから次を開始する
- 方針変更が出たら `docs/plans/tech-catchup/` に日付付きメモを追加し、該当 `phase-XX` を更新 or 追記する
