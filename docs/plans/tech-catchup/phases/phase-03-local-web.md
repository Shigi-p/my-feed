# Phase 3 — ローカル Web（A）+ 履歴・お気に入り

| 項目 | 内容 |
|------|------|
| ステータス | 計画承認待ち |
| 依存 | Phase 1（パイプライン）、Phase 2（Markdown レンダラ） |
| 後続 | Phase 4（運用改善） |
| ゴール | localhost で「いま取得」→ 10 件表示 → Markdown DL → お気に入り／履歴の見返しができる |

---

## 1. 目的

任意トリガーの主戦場を **ブラウザ** に移す。  
通勤・息抜きで使える導線の原型を、認証なしのローカル動作で完成させる。

---

## 2. スコープ

### やること

- FastAPI による最小 Web UI
- 「いま取得」ボタン（Phase 1 パイプライン呼び出し）
- スコアラー選択
- 最新結果一覧
- Markdown ダウンロード（bundle / 必要なら single）
- SQLite による実行履歴・お気に入り
- 履歴一覧・お気に入り一覧
- ローカル起動手順の文書化

### やらないこと

- 本番デプロイ・ドメイン・HTTPS
- 本格認証（Basic Auth 等も原則後回し。どうしても必要なら Phase 5）
- Google Drive 連携
- AI 要約
- 凝ったダッシュボード UI（統計カード群などは置かない）
- リアルタイム進捗 WebSocket（初期は同期リクエストで可。遅ければ後で改善）

---

## 3. UI 方針（最小）

一覧特化。最初の画面は次だけでよい。

1. ヘッダー: アプリ名（my feed）
2. 操作: スコアラー選択 + 「いま取得」ボタン
3. 結果: Top 10 のリスト（タイトル・出典・スコア・リンク・お気に入りボタン）
4. アクション: Markdown DL
5. ナビ: 履歴 / お気に入り

装飾優先ではなく、**取得と保存と書き出し**が迷わずできること。

---

## 4. モジュール構成案

```
src/my_feed/
  store/
    __init__.py
    db.py                 # SQLite 接続・マイグレーション簡易版
    runs.py               # 実行ラン CRUD
    favorites.py          # お気に入り CRUD
  web/
    __init__.py
    app.py                # FastAPI factory
    routes/
      home.py
      runs.py
      favorites.py
      export.py
    templates/
      base.html
      index.html
      run_detail.html
      favorites.html
    static/               # 最小 CSS のみ
```

CLI は残す。Web は `pipeline.run` と `output.render_*` を呼ぶだけ。

---

## 5. データ永続化

### 5.1 テーブル案

**runs**

| 列 | 説明 |
|----|------|
| `id` | UUID / 整数 |
| `created_at` | 実行日時 |
| `scorer` | 使用戦略名 |
| `top_n` | 件数 |
| `status` | `ok` / `partial` / `error` |
| `source_errors` | JSON（落ちたソースと理由） |
| `result_json` | Top 10 のスナップショット |

**favorites**

| 列 | 説明 |
|----|------|
| `id` | |
| `item_id` | `Item.id` |
| `saved_at` | |
| `item_json` | 保存時点のスナップショット |
| `note` | 任意メモ（初期は空で可） |

同一 `item_id` の重複お気に入りは、UPSERT か「既にある」表示のどちらかに固定する。

### 5.2 DB ファイル場所

- デフォルト: プロジェクトローカル `data/my_feed.db`（gitignore）
- 設定で変更可

---

## 6. ルート案

| メソッド | パス | 説明 |
|----------|------|------|
| GET | `/` | 最新ラン or 空状態 + 取得フォーム |
| POST | `/runs` | いま取得（scorer 指定）→ 保存 → リダイレクト |
| GET | `/runs` | 履歴一覧 |
| GET | `/runs/{id}` | 過去ラン詳細 |
| GET | `/runs/{id}/markdown` | bundle MD DL |
| GET | `/runs/{id}/items/{item_id}/markdown` | single MD DL |
| POST | `/favorites` | お気に入り追加 |
| DELETE | `/favorites/{id}` | 削除 |
| GET | `/favorites` | お気に入り一覧 |

初期はサーバサイドレンダリング中心でよい（JSON API 化は任意）。

---

## 7. 「いま取得」の挙動

1. フォームから scorer / top_n（固定10でも可）を受ける
2. パイプライン実行（同期）
3. ソースエラーを `source_errors` に記録
4. Top 10 を `result_json` に保存
5. 詳細ページへリダイレクト
6. 失敗時（全ソース死）はエラーページ or フラッシュメッセージ

タイムアウト: 外部取得が遅い場合に備え、httpx タイムアウトを Phase 1 設定と共有する。

---

## 8. タスク分解

### T1. FastAPI 骨格と起動

- [ ] `my-feed serve` or `uvicorn my_feed.web.app:app`
- [ ] 空の index テンプレ
- **完了**: localhost でページが開く

### T2. 取得ボタン → パイプライン

- [ ] POST `/runs`
- [ ] 結果一覧表示
- **完了**: ブラウザだけで Top 10 が見える

### T3. Markdown DL

- [ ] Phase 2 レンダラ接続
- **完了**: ダウンロードした MD が Phase 2 と同等

### T4. SQLite runs

- [ ] schema + 保存 + 履歴一覧 + 詳細
- **完了**: 再起動後も過去ランが見れる

### T5. お気に入り

- [ ] 追加・一覧・削除
- **完了**: 気になった記事を残して見返せる

### T6. 文書化と手動確認

- [ ] README に起動手順
- [ ] 通勤利用を想定した最短操作の記載
- **完了**: 手順どおりに第三者がローカルで再現できる（自分の別端末でも可）

---

## 9. 完了条件（Exit Criteria）

- [ ] localhost で取得 → 10 件表示ができる
- [ ] スコアラーを UI から選べる
- [ ] Markdown を DL できる
- [ ] 実行履歴を見返せる
- [ ] お気に入りの追加・一覧ができる
- [ ] CLI パイプラインを壊していない（回帰確認）

---

## 10. worktree / ブランチ提案

- ブランチ例: `cursor/phase-03-local-web-<suffix>`
- Phase 2 マージ後の `main` から分岐

---

## 11. リスク

| リスク | 緩和 |
|--------|------|
| 取得が長くブラウザが待つ | タイムアウト明示、後でバックグラウンド化（Phase 4 候補） |
| UI を作り込みすぎる | 画面要素を本ドキュメントの最小セットに制限 |
| DB スキーマがすぐ変わる | 簡易マイグレーション（起動時 CREATE IF NOT EXISTS）で開始 |
| 認証なしで誤って公開 | README で「ローカル専用」と明記。Phase 5 まで bind は 127.0.0.1 推奨 |

---

## 12. 次フェーズへの引き渡し

Phase 4 に渡すもの:

- 動くローカル Web
- 設定を増やす前提の `config.toml`
- ソースエラー表示の置き場（`source_errors`）
