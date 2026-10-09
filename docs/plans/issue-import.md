# GitHub Issue 作成用（一時稿）

このファイルは **Issue を手で作るためのコピー元** です。正本ではありません。
コピーが終わったら **このファイルごと削除** してください（計画 md の削除と同じタイミングでよい）。

使い方:

1. 下の「先に作るラベル」を GitHub の Labels に作る
2. 「作成:必須」を上から作り、作ったらチェックを入れる
3. 「作成:任意」は、バックログに載せたいものだけ作る。作らない＝今はやらない判断
4. 各 Issue は **タイトル** を Issue タイトルに、**本文** を Issue 本文に貼る。ラベルは作成画面で付ける

作らないもの:

| ID | 理由 |
|----|------|
| M4-D | Gemini 3.5 Flash Lite 要約は実装済み。Issue 不要 |
| M4-C 単独 | M3-Scheduled と中身が重なる。**1本に統合**してある |

元ファイル（削除前の参照）:

- `docs/plans/tech-catchup/milestones/m3-ops.md`
- `docs/plans/tech-catchup/milestones/m3-scheduled.md`
- `docs/plans/tech-catchup/milestones/m4-optional.md`
- `docs/plans/tech-catchup/2026-10-08-m4d-ollama-integration.md`
- `docs/plans/2026-10-08-ui-code-refactor.md`

---

## 先に作るラベル

| 名前 | 色（例） | 意味 |
|------|----------|------|
| `作成:必須` | `#B60205` | 計画 md を消す前に作る。作らないと仕事の置き場が消える |
| `作成:任意` | `#C5DEF5` | 作らなくてもよい。作らない＝バックログに載せない |
| `priority:next` | `#D93F0B` | 次に着手しうる |
| `priority:later` | `#FBCA04` | 必要になったら |
| `milestone:m3` | `#1D76DB` | M3 系 |
| `milestone:m4` | `#5319E7` | M4 系 |
| `type:feature` | `#0E8A16` | 機能 |
| `type:refactor` | `#1D76DB` | 見た目を変えない整理 |
| `type:ops` | `#0052CC` | 運用・自動化 |
| `type:docs` | `#0075CA` | ガイド追加 |

既存の `enhancement` も付けてよい。`作成:必須` / `作成:任意` はコピー作業用なので、作り終わったら外してよい。

---

## 作成状況

### 作成:必須（計画削除の前提）

- [ ] 1. [M3] 運用改善の残作業
- [ ] 2. [M3-Scheduled / M4-C] GitHub Actions 定期取得
- [ ] 3. [M4-H] 自宅で Ollama に切替
- [ ] 4. [UI] HTML/CSS 分離とコンポーネント化

### 作成:任意（メニュー。載せるものだけ）

- [ ] 5. [M4-A] ホスティング
- [ ] 6. [M4-A'] Docker 化
- [ ] 7. [M4-B] 簡易認証
- [ ] 8. [M4-E] 有料 AI 要約
- [ ] 9. [M4-F] Google Drive 連携
- [ ] 10. [M4-G] リポジトリ公開準備

---

# 作成:必須

---

## 1. [M3] 運用改善の残作業

- **作成:** 必須
- **タイトル:** `[M3] 運用改善の残作業（設定・可視化・ガイド・フィルタ口）`
- **ラベル:** `作成:必須` `priority:next` `milestone:m3` `type:feature` `enhancement`

### 本文

```markdown
## 目的

ソースや評価基準の変更を、コード大改修なしで試せるようにする。
M2 をしばらく使ってからの着手を推奨。

## 作成ラベル

- 作成: **必須**（`m3-ops.md` を消す前に必要）
- プロダクト上は任意（やらなくても今のローカル完成は維持）

## 実装済み（2026-10-09 コード確認）

次は Issue 作成時点で既にある。残が無ければチェックして Close してよい。

- [x] `top_n` / `default_scorer` / `[scoring.hybrid]` は `config.toml` で変更できる
- [x] ソースの有効/無効は `enabled_sources` で変えられる
- [x] CLI は `source_errors=...` を出す
- [x] Web の `/` と run 詳細は `source_errors` を表示する

## 残作業（優先度順）

### 1. ソース有効/無効の露出

- 設定ファイルは単一真実のまま
- 必要なら Web トグルを後付け（初期はファイルだけでよい）
- 完了: 「Trending だけオフ」が再現できる

### 2. パラメータの正式化

- バリデーションを揃える
- 完了: コードを触らず `top_n` / half_life を変えられる（大半は既存）

### 3. 取得失敗の可視化

- CLI / Web の見え方を揃える
- 完了: partial が一目で分かる（表示自体は既存。不足があればここ）

### 4. 追加ガイド

- `docs/guides/` にソース追加・スコアラー追加の手順
- 完了: 手順どおりダミーを足せる

### 5. フィルタ口（デフォルトオフ）

```toml
[sources.gigazine]
enabled = true
keyword_filter_enabled = false
keyword_allowlist = []
```

- オフ時の挙動は今と変えない
- 完了: オン時のみ絞り込み

## やらないこと

- 本番認証・公開
- 有料 AI / Drive
- 自動学習レコメンド
- LLM 要約の本導入（Gemini は M4-D で済み。Ollama は #M4-H）

## 完了条件

- [ ] ソース有効/無効・スコアパラメータが設定で変わる（既存分は確認だけ）
- [ ] 追加ガイドがある
- [ ] partial 失敗が分かる（既存分は確認だけ）
- [ ] フィルタはデフォルトオフ

## 元ドキュメント（削除予定）

- `docs/plans/tech-catchup/milestones/m3-ops.md`
```

---

## 2. [M3-Scheduled / M4-C] GitHub Actions 定期取得

- **作成:** 必須
- **タイトル:** `[M3-Scheduled / M4-C] GitHub Actions でフィードを定期取得する`
- **ラベル:** `作成:必須` `priority:next` `milestone:m3` `milestone:m4` `type:ops` `enhancement`

### 本文

```markdown
## 目的

「いま取得」の同期 API 呼び出しを主経路にせず、事前生成したフィードをすぐ表示できるようにする。
Web の手動取得は残す。

M4-C（朝の自動生成）と計画が重なるため、**この Issue 1本**にする。ID は両方残す。詳細は M3-Scheduled 側。

## 作成ラベル

- 作成: **必須**（`m3-scheduled.md` を消す前に必要）
- プロダクト上は任意

## 依存

- M2（ローカル完成）
- M4-D（Gemini 要約。実装済み）

## やること

1. `.github/workflows/fetch-feed.yml` を新設（既存 `ci.yml` は触らない）
   - cron: 毎日 UTC 00:00（JST 09:00）+ `workflow_dispatch`
   - `uv run my-feed run --config config.example.toml --json --out data/latest-feed.json`
   - commit & push。メッセージに `[skip ci]`
2. 永続化は案 B
   - Actions が `data/latest-feed.json` をコミット
   - Web 起動時に JSON を読んで DB へ投入
   - `data/my_feed.db` は git 管理外
3. 起動時に JSON があれば自動ロード。`/runs` POST の手動取得は残す
4. Repository Secret `GEMINI_API_KEY` をワークフローへ注入
5. README に Secrets・定期取得・手動との使い分けを書く
6. `.gitignore`: DB は除外、`data/latest-feed.json` は追跡

## やらないこと

- 失敗時の追加通知（GitHub の標準ステータスで見る）
- 1日複数回（コスト。1日1回）
- 手動取得の廃止
- DB ファイルのコミット
- 既存 CI ワークフローの変更

## アーキテクチャ

```text
【定期】Actions cron
  → my-feed run --json --out data/latest-feed.json
  → git commit & push ([skip ci])

【起動】latest-feed.json があれば DB に投入（重複は更新 or スキップ）

【閲覧】保存済みを表示。手動「いま取得」は任意
```

## 完了条件

- [ ] 毎日 UTC 00:00 に Actions が走る
- [ ] 成功時 `data/latest-feed.json` が更新・コミットされる
- [ ] `[skip ci]` 付きコミットが `ci.yml` を回さない
- [ ] 既存の lint / typecheck / test は維持
- [ ] 起動後すぐに `/` に最新が出る
- [ ] 手動取得も使える
- [ ] 失敗は GitHub UI で分かる

## コスト目安（計画時点）

- Gemini: 1日1回 × 10記事 ≒ 30円/月
- Actions: 無料枠内を想定
- 遅延: 最大24時間

## 元ドキュメント（削除予定）

- `docs/plans/tech-catchup/milestones/m3-scheduled.md`
- `docs/plans/tech-catchup/milestones/m4-optional.md` の M4-C 行
```

---

## 3. [M4-H] 自宅で Ollama に切替

- **作成:** 必須
- **タイトル:** `[M4-H] 自宅PCで Ollama に切り替えて要約する`
- **ラベル:** `作成:必須` `priority:next` `milestone:m4` `type:feature` `enhancement`

### 本文

```markdown
## 目的

デフォルトは Gemini（出先）。自宅 PC だけ `SUMMARIZER_BACKEND=ollama` でコストゼロ要約する。
常時稼働サーバーは作らない。自動で Gemini に落とさない。

旧称「M4-D 拡張」は使わない。M4-D は Gemini 無料枠（実装済み）。M4-E は有料・コスト上限（未着手・任意）。

## 作成ラベル

- 作成: **必須**（Ollama 計画 md を消す前に必要）
- プロダクト上は任意

## 依存

- M2 完了
- M4-D（Gemini 要約）が動作していること

## 完成後の使い方

出先:

```bash
export GEMINI_API_KEY="your-key"
uv run my-feed serve
```

自宅:

```bash
ollama serve
ollama pull gemma4:e4b
SUMMARIZER_BACKEND=ollama uv run my-feed serve
```

## やること

- 設定: `backend = "gemini" | "ollama"`。優先順位は環境変数 `SUMMARIZER_BACKEND` → config → 未設定なら `gemini`
- `OllamaSummarizer`: 要約時に Top N だけ HTML を GET して本文抽出。失敗時は `excerpt` / タイトル
- `Item` 契約は変えない。抽出は `summarizer/` 側（`sources/` ではない）
- Gemini 経路は URL Context のまま
- ollama 未起動は警告して要約スキップ（Gemini へフォールバックしない）
- 推奨モデル: `gemma4:e4b`
- 実 ollama 呼び出しは opt-in（例: `MY_FEED_OLLAMA=1`）。通常テストはネットワーク無し

実装は2PRでも可。

1. 設定 + OllamaSummarizer + HTML 抽出 + テスト
2. pipeline 分岐 + README（自宅/出先）

## やらないこと

- `Item.content_snippet` の追加
- 各 Source での全件 HTML 取得
- 自動 Gemini フォールバック
- 並行要約（async）
- 要約の永続化・再要約スキップ
- 常時稼働サーバー / VPN

## 完了条件

- [ ] `backend` 未指定時は今と同じ Gemini
- [ ] `SUMMARIZER_BACKEND=ollama` で OllamaSummarizer が使われる
- [ ] ollama 未起動でもパイプラインは継続
- [ ] 本文抽出と mock テストがある
- [ ] README に自宅/出先の使い分けがある
- [ ] `make ci` 相当が通る

## 参考

- https://github.com/ryochin/stingray
- https://ollama.com/
- https://ollama.com/library/gemma4

## 元ドキュメント（削除予定）

- `docs/plans/tech-catchup/2026-10-08-m4d-ollama-integration.md`
```

---

## 4. [UI] HTML/CSS 分離とコンポーネント化

- **作成:** 必須
- **タイトル:** `[UI] CSS を分離し、重複ボタンをマクロにする`
- **ラベル:** `作成:必須` `priority:next` `type:refactor`

### 本文

```markdown
## 目的

見た目は変えず、Web UI の構造だけ整える。
`base.html` の `<style>`（約170行）を外に出し、お気に入り/MD ボタンの重複を除く。

## 作成ラベル

- 作成: **必須**（UI 計画 md を消す前に必要）
- プロダクト上は任意（機能追加ではない）

## やること

1. HTML と CSS の分離
   - `src/my_feed/web/static/css/style.css` を配信（FastAPI `StaticFiles`）
   - `base.html` の `<style>` をやめる
2. SCSS
   - ツール: `dartsass`（Python。`pyproject.toml` に追加）
   - 初期は2ファイル: `_variables.scss` + `style.scss`
   - ビルド出力 CSS は git 管理しない（`.gitignore`）
   - 開発は watch、起動前は手動ビルド。`serve` 内の自動ビルドは今回やらない
3. コンポーネント化
   - ページ構造は `{% include %}`
   - 繰り返しパーツは `{% macro %}`
   - `macros.html` に `action_buttons(...)` を置き、`_item_list.html` と `favorites.html` から使う

## やらないこと

- 見た目の変更
- スコアバッジ・ソースラベルのマクロ（将来）
- ダークモード、タブレット専用の新規デザイン
- `style.scss` が200行を超えるまでの4ファイル分割（超えたら検討）

## 完了条件

- [ ] 全ページが表示される（`/`, `/runs`, `/favorites`, `/runs/{id}`）
- [ ] お気に入り追加/解除が動く
- [ ] Markdown DL が動く
- [ ] `pytest tests/test_m2_web.py` が通る
- [ ] SCSS watch が動く
- [ ] README にビルド手順がある
- [ ] `.gitignore` に CSS 出力がある

## 元ドキュメント（削除予定）

- `docs/plans/2026-10-08-ui-code-refactor.md`
```

---

# 作成:任意

作らないものは、バックログに載せない判断になる。後から同じタイトルで足せる。

---

## 5. [M4-A] ホスティング

- **作成:** 任意
- **タイトル:** `[M4-A] 外出先のスマホから一覧・取得できるようにする`
- **ラベル:** `作成:任意` `priority:later` `milestone:m4` `type:feature` `enhancement`

### 本文

```markdown
## 目的

外出先のスマホブラウザから一覧と取得ができる。

## 作成ラベル

- 作成: **任意**
- 着手トリガー: 外出先スマホから常用したくなった
- 推奨順（公開系）: (A+B) → C → …。C は M3-Scheduled と統合済み

## 完了条件

- [ ] スマホブラウザから一覧・取得ができる

## 約束

- 認証なしのままインターネットに晒さない（M4-B とセットで考える）

## 元ドキュメント（削除予定）

- `docs/plans/tech-catchup/milestones/m4-optional.md`
```

---

## 6. [M4-A'] Docker 化

- **作成:** 任意
- **タイトル:** `[M4-A'] docker compose で再現起動する（中は uv）`
- **ラベル:** `作成:任意` `priority:later` `milestone:m4` `type:ops` `enhancement`

### 本文

```markdown
## 目的

環境差分が実害になったとき、または CI・公開をコンテナに寄せたいときに、再現起動できるようにする。
コンテナ内のアプリは uv で動かす。

## 作成ラベル

- 作成: **任意**
- 着手トリガー: 環境差分が痛くなった / 公開をコンテナに寄せたい

## 完了条件

- [ ] `docker compose` 等で再現起動できる
- [ ] アプリはコンテナ内 uv で動く

## 元ドキュメント（削除予定）

- `docs/plans/tech-catchup/milestones/m4-optional.md`
```

---

## 7. [M4-B] 簡易認証

- **作成:** 任意
- **タイトル:** `[M4-B] 未認証では一覧も取得もできないようにする`
- **ラベル:** `作成:任意` `priority:later` `milestone:m4` `type:feature` `enhancement`

### 本文

```markdown
## 目的

URL を持つ第三者に触れられないようにする。
認証は Web 層に閉じ、pipeline には持ち込まない。

## 作成ラベル

- 作成: **任意**
- 着手トリガー: URL を持つと第三者が触れうる
- 公開するなら A とセット

## 完了条件

- [ ] 未認証では一覧も取得もできない

## 元ドキュメント（削除予定）

- `docs/plans/tech-catchup/milestones/m4-optional.md`
```

---

## 8. [M4-E] 有料 AI 要約

- **作成:** 任意
- **タイトル:** `[M4-E] 有料 AI 要約（コスト上限超過時はスキップ）`
- **ラベル:** `作成:任意` `priority:later` `milestone:m4` `type:feature` `enhancement`

### 本文

```markdown
## 目的

無料枠の品質や制限に不足を感じたら、有料モデルへ進む。
コスト上限を超えたら要約をスキップしてパイプラインは継続する。

M4-D（Gemini 無料枠）とは別。M4-H（Ollama）とも別。

## 作成ラベル

- 作成: **任意**
- 着手トリガー: 無料枠の品質/制限に不満

## 完了条件

- [ ] コスト上限超過時は要約スキップして継続

## 約束

- 要約は `excerpt` を上書きしない
- LLM は Adapter 同様に隔離

## 元ドキュメント（削除予定）

- `docs/plans/tech-catchup/milestones/m4-optional.md`
```

---

## 9. [M4-F] Google Drive 連携

- **作成:** 任意
- **タイトル:** `[M4-F] 指定フォルダへ Markdown を置く`
- **ラベル:** `作成:任意` `priority:later` `milestone:m4` `type:feature` `enhancement`

### 本文

```markdown
## 目的

Markdown DL 運用が手間になったら、指定フォルダへ `.md` を置く。
失敗時はローカル DL に戻す。

## 作成ラベル

- 作成: **任意**
- 着手トリガー: MD DL 運用が手間になった

## 完了条件

- [ ] 指定フォルダへ `.md` が置かれる
- [ ] 失敗時はローカル DL へ

## 約束

- Drive は Adapter 同様に隔離

## 元ドキュメント（削除予定）

- `docs/plans/tech-catchup/milestones/m4-optional.md`
```

---

## 10. [M4-G] リポジトリ公開準備

- **作成:** 任意
- **タイトル:** `[M4-G] リポジトリをパブリックにする前の精査`
- **ラベル:** `作成:任意` `priority:later` `milestone:m4` `type:docs`

### 本文

```markdown
## 目的

コードを公開したくなったときに、意図しない個人データや秘密がリポジトリに含まれない状態にする。
アプリをインターネットに晒す話（M4-A）とは分離する。独立していつでも可。2026-10-06 時点では後回し。

## 作成ラベル

- 作成: **任意**
- 着手トリガー: コードを公開したくなった

## 着手時に見ること

- `config.local.toml` / `data/*.db` が tracked でないこと
- 秘密情報（トークン等）がコード・履歴に無いこと
- 非公式 API / HTML スクレイピングの注意書きの要否
- コミット実名・連絡先の露出ポリシー
- 「コード公開」と「`serve` を外向きに晒す」を混同しない文言（認証なしのまま外向きは不可）

## 完了条件

- [ ] 公開チェックリストを満たす
- [ ] 意図しない個人データ／秘密がリポジトリに含まれない

## 元ドキュメント（削除予定）

- `docs/plans/tech-catchup/milestones/m4-optional.md`
```
