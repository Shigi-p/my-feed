# 計画 PR 承認チェックリスト

**この PR の目的**: 実装ではなく、要件・届け方モデル・各トラック/マイルストーン詳細をレビューし、合意したうえでマージする。

マージ後は **C0 → 並行トラック → マイルストーン** の順で worktree 実装する。

---

## レビュー手順

1. [2026-10-06-roadmap.md](./2026-10-06-roadmap.md) で要件を確認
2. [delivery-model.md](./delivery-model.md) で届け方を確認
3. [contracts/](./contracts/README.md) / [tracks/](./tracks/README.md) / [milestones/](./milestones/README.md) を通読
4. 下記チェックリストで懸念をコメント
5. 問題なければ承認・マージ

---

## 承認チェック（要件）

- [ ] 目的・やらないことの境界が意図と一致
- [ ] 情報源（Zenn / Qiita / GIGAZINE / GitHub Trending）で当面よい
- [ ] Top 10・横断ランキング・複数スコアラー差し替え可能、でよい
- [ ] 認証・Drive・AI 要約を後回しでよい
- [ ] GIGAZINE 当面無フィルタでよい
- [ ] スタック仮決め（Python + uv + FastAPI + SQLite）でよい

---

## 承認チェック（届け方モデル）

- [ ] 「契約ハブ + 並行トラック」で進めてよい（呼び名は仮で可）
- [ ] C0 完了後に T-Web を Fake で並行着手する実験方針でよい
- [ ] トラック単位 worktree、マイルストーンで合流、の運用でよい
- [ ] [C0](./contracts/c0-contract-hub.md) の契約範囲が妥当
- [ ] [T-Src](./tracks/t-src.md) / [T-Score](./tracks/t-score.md) / [T-Md](./tracks/t-md.md) / [T-Web](./tracks/t-web.md) / [T-Store](./tracks/t-store.md) の境界が妥当
- [ ] [M1](./milestones/m1-cli.md) / [M2](./milestones/m2-local.md) / [M3](./milestones/m3-ops.md) / [M4](./milestones/m4-optional.md) の合流定義が妥当

---

## コメントしてほしい観点（任意）

- C0 に含める Protocol の過不足（Store/Markdown を C0 に含めるか等）
- T-Web を Fake で進める範囲（どこまで画面を作り込むか）
- M1 前に T-Md CLI を必須にするか任意にするか
- 呼び名「契約ハブ + 並行トラック」の別案

---

## マージ後の最初の実装

**C0（契約ハブ）のみ**を別ブランチ / worktree で着手する。  
この PR ではアプリケーションコードを追加しない。
