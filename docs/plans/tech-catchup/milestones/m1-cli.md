# M1 — CLI 縦切り

| 項目 | 内容 |
|------|------|
| 依存 | C0 + **T-Src** + **T-Score** |
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

- [ ] registry から実ソース・実スコアを解決
- **完了**: Fake 無しでも `run_pipeline` が動く

### T2. CLI UX

- [ ] `--scorer` / `--top` / `--json` / `--out`
- **完了**: フラグがドキュメントどおり

### T3. 手動確認

- [ ] 全ソース有効で 10 件
- [ ] scorer 切替
- [ ] Trending 障害 or disable でも全体成功
- **完了**: README の確認節が実行可能

---

## 5. 完了条件（Exit Criteria）

- [ ] ローカル 1 コマンドで実 Top 10
- [ ] スコアラー切替可
- [ ] ソース追加が「Adapter + 登録 + 設定」で済むことが維持されている
- [ ] partial 失敗がログ / `source_errors` に残る
- [ ] T-Web が同じ `run_pipeline` を後で呼べる

---

## 6. worktree

- `cursor/m1-cli-<suffix>`
- T-Src / T-Score がそれぞれマージ可能になってからが安全  
  （または integration ブランチで両方を取り込む）
