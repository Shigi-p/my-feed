# T-Store — 永続化トラック

| 項目 | 内容 |
|------|------|
| 依存 | **C0 のみ** |
| 合流先 | M2 |
| ゴール | `RunStore` / `FavoriteStore` の SQLite 実装が契約を満たす |

---

## 1. 目的

実行履歴とお気に入りを、プロセス再起動後も残す。  
UI は T-Web、ここでは永続化の正しさに集中する。

---

## 2. スコープ

### やること

- SQLite スキーマ
- runs / favorites の CRUD
- `PipelineResult` スナップショット保存
- お気に入りの UPSERT 方針固定
- DB パス設定（デフォルト `data/my_feed.db`、gitignore）
- ストア単体テスト

### やらないこと

- HTML テンプレート
- 認証
- マイグレーション基盤の作り込みすぎ（起動時 `CREATE IF NOT EXISTS` で開始可）

---

## 3. テーブル案

**runs**

| 列 | 説明 |
|----|------|
| `id` | UUID / 整数 |
| `created_at` | |
| `scorer` | |
| `top_n` | |
| `status` | `ok` / `partial` / `error` |
| `source_errors` | JSON |
| `result_json` | Top N スナップショット |

**favorites**

| 列 | 説明 |
|----|------|
| `id` | |
| `item_id` | `Item.id` |
| `saved_at` | |
| `item_json` | スナップショット |
| `note` | 任意（初期空可） |

同一 `item_id` は UPSERT か「既存を返す」のどちらかに固定。

---

## 4. タスク分解

### T1. DB 接続と schema

- [ ] ファイル作成、CREATE IF NOT EXISTS
- **完了**: 空 DB が作れる

### T2. runs CRUD

- [ ] save / get / list
- **完了**: 再起動後もランが読めるテスト

### T3. favorites CRUD

- [ ] add / list / remove + 重複方針
- **完了**: お気に入りが残るテスト

### T4. C0 Protocol 実装として露出

- [ ] ファクトリ or 具象クラスを registry 的に提供
- **完了**: T-Web がメモリ実装から差し替えられる

---

## 5. 完了条件

- [ ] RunStore / FavoriteStore 契約を SQLite が満たす
- [ ] DB ファイル場所が設定可能
- [ ] 単体テストがある
- [ ] M2 で T-Web に配線できる

---

## 6. worktree

- `cursor/t-store-<suffix>`
