# M2 — ローカル完成

| 項目 | 内容 |
|------|------|
| ステータス | **完了**（ブランチ `cursor/m2-local-bcb5`） |
| 依存 | **M1** + **T-Md** + **T-Web** + **T-Store** |
| 後続 | M3 |
| ゴール | localhost で実取得 → 10 件表示 → Markdown DL → 履歴・お気に入りが見返せる |

---

## 1. 目的

並行トラックの成果を一本のローカルプロダクトに統合する。  
ここが「通勤・息抜きで使える原型」の完成地点。

---

## 2. 結合でやること

- T-Web の Fake pipeline → M1 の実 `run_pipeline` に置換（設定の `enabled_sources` に従う）
- Markdown DL → T-Md の `render_*`（stub intro を除去）
- メモリ Store → T-Store の SQLite に置換（デフォルト `data/my_feed.db`）
- 履歴・お気に入りが再起動後も残ることを確認
- CLI が壊れていないことの回帰確認
- ローカル起動手順の最終化

### やらないこと

- 本番公開・認証
- Actions / AI / Drive
- 運用パラメータの本格 UI（M3）

---

## 3. 受け入れシナリオ

1. `my-feed serve` で起動（`config.local.toml` があれば優先）
2. ブラウザでスコアラー選択 → 「いま取得」（初期値は設定の `default_scorer`、通常 hybrid）
3. 実 Top 10 が表示される
4. Markdown を DL し、Gemini に貼れる
5. お気に入りを付け、履歴一覧から過去ランを開ける
6. プロセス再起動後も履歴・お気に入りが残る
7. CLI `run` も引き続き動く

---

## 4. タスク分解

### T1. 依存注入の本番配線

- [x] Web ファクトリで実 pipeline / renderer / store を接続
- **完了**: デフォルトが SQLite + `resolve_config_path()`（`config.local.toml` 優先）

### T2. エラー表示の最低限

- [x] `source_errors` / `partial` を結果ページに出す
- **完了**: どのソースが落ちたか分かる

### T3. 回帰と文書

- [x] CLI + Web の手動／自動チェック
- [x] README 更新
- **完了**: 第三者が手順どおり再現できる

### T4. Fake の整理

- [x] 本番経路のデフォルト Store を SQLite に。ルート `config.toml` は offline 用 fake 維持
- [x] 実取得は `config.local.toml`（example からコピー）。スコアラー `fake` はデバッグ用に UI に残す
- **完了**: `config.local.toml` 利用時のデフォルト体験に Fake データが出ない

---

## 5. 完了条件（Exit Criteria）

- [x] 上記受け入れシナリオがすべて通る（自動テスト + 手順）
- [x] 認証なし・ローカル専用であることが明記されている
- [x] 並行トラックの契約が維持されている

---

## 6. worktree

- `cursor/m2-local-bcb5`
