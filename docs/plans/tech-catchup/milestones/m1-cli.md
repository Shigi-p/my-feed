# M1 — CLI 縦切り

| 項目 | 内容 |
|------|------|
| ステータス | **完了**（ブランチ `cursor/m1-cli-bcb5`） |
| 依存 | C0 + **T-Src** + **T-Score**（いずれも `main` 合流済み） |
| 後続 | M2 |
| ゴール | 1 コマンドで実ソース取得 → スコア → Top 10 が再現可能に出る |

---

## 1. 目的

取得と評価の最初の **縦の使用断面** を CLI で作る。  
Web や Markdown 本テンプレは必須ではない（JSON/表で可）。

---

## 2. 結合でやること

- Fake pipeline を実 Adapter + 実 Scorer に配線
- `my-feed run --scorer hybrid --top 10`
- table / `--json` / 任意 `--out`
- 1 ソース失敗でも（他が生きていれば）結果を返す
- README の動作確認手順

### やらないこと（M1 範囲外）

- FastAPI UI
- SQLite 必須化
- Gemini 向け本 Markdown（T-Md は別。任意で仮接続は可）
- 認証 / Drive / AI

---

## 3. 処理フロー

```text
load config
 → enabled adapters fetch（初期は直列で可）
 → score
 → top_n
 → stdout（table 既定 / --json）
```

---

## 4. タスク分解

### T1. 配線

- [x] registry から実ソース・実スコアを解決
- **完了**: Fake 無しでも `run_pipeline` が動く（ルート設定は offline 用に `fake` 維持。実運用は `config.example.toml`）

### T2. CLI UX

- [x] `--scorer` / `--top` / `--json` / `--out`（＋ `--config` / `--out-md`）
- **完了**: フラグがドキュメントどおり

### T3. 手動確認

- [x] 全ソース有効で 10 件（live / `MY_FEED_LIVE`）
- [x] scorer 切替（結合テスト + CLI）
- [x] Trending 障害 or disable でも全体成功（結合テストで simulated outage）
- **完了**: README の確認節が実行可能

---

## 5. 完了条件（Exit Criteria）

- [x] ローカル 1 コマンドで実 Top 10（`cp config.example.toml config.local.toml` → `my-feed run --config ...`）
- [x] スコアラー切替可
- [x] ソース追加が「Adapter + 登録 + 設定」で済むことが維持されている
- [x] partial 失敗がログ / `source_errors` に残る
- [x] T-Web が同じ `run_pipeline` を後で呼べる（既存）

---

## 6. worktree

- `cursor/m1-cli-bcb5`
- T-Src / T-Score は `main` 合流後に着手
