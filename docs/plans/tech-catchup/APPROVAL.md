# 計画 PR 承認チェックリスト

**この PR の目的**: 実装ではなく、全体ロードマップと各フェーズ詳細計画をレビューし、合意したうえでマージする。

マージ後、フェーズ単位の worktree で実装を進める。

---

## レビュー手順

1. [2026-10-06-roadmap.md](./2026-10-06-roadmap.md) で全体方針を確認
2. [phases/](./phases/README.md) 配下を Phase 0 → 5 の順に通読
3. 下記チェックリストで懸念・修正点をコメント
4. 問題なければ本 PR を承認・マージ

---

## 承認チェック（全体）

- [ ] 目的・やらないことの境界が自分の意図と一致している
- [ ] 情報源（Zenn / Qiita / GIGAZINE / GitHub Trending）で当面よい
- [ ] Top 10・横断ランキング・複数スコアラー差し替え可能、でよい
- [ ] 進め方 B→A（CLI → ローカル Web）でよい
- [ ] スタック仮決め（Python + FastAPI + SQLite）でよい
- [ ] 認証・Drive・AI 要約を後回しにする判断でよい
- [ ] GIGAZINE 当面無フィルタでよい
- [ ] マージ後にフェーズ単位 worktree で進める想定でよい

---

## 承認チェック（フェーズ詳細）

- [ ] [Phase 0](./phases/phase-00-design.md) — 本 PR の完了条件が明確
- [ ] [Phase 1](./phases/phase-01-cli-pipeline.md) — CLI パイプラインの範囲・完了条件が妥当
- [ ] [Phase 2](./phases/phase-02-markdown.md) — Markdown 出力の範囲が妥当
- [ ] [Phase 3](./phases/phase-03-local-web.md) — ローカル Web / 履歴 / お気に入りの範囲が妥当
- [ ] [Phase 4](./phases/phase-04-ops-tuning.md) — 運用改善の範囲が妥当
- [ ] [Phase 5](./phases/phase-05-publish-and-ai.md) — 発展項目が「必要になったら」で切れている

---

## コメントしてほしい観点（任意）

計画を直すなら、特に次があると後工程が楽です。

- パッケージ管理（`uv` 仮決め）への異論
- ソース取得手段（RSS 優先）で不安なソース
- スコア正規化の初期方針への異論
- Phase 区切り（例: Phase 2 と 3 を同居させたい等）
- UI の最低要件（Phase 3）で足りない／多すぎる点

---

## マージ後の最初の実装

承認済みなら、次は **Phase 1** のみを別ブランチ / worktree で着手する。  
この PR ではアプリケーションコードを追加しない。
