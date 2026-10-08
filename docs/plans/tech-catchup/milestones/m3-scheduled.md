# M3-Scheduled — GitHub Actions 定期自動取得

| 項目 | 内容 |
|------|------|
| 依存 | **M2**（ローカル完成）+ M4-D（AI要約） |
| 後続 | M3（運用改善の他項目） |
| ゴール | Web アプリでの同期的API呼び出しを廃止し、事前生成されたフィードを即座に表示できる |

---

## 1. 目的

現状の課題を解決する：

- **問題**: ブラウザで「いま取得」をクリックすると、複数の外部API（Qiita、Zenn、GitHub Trending、Gigazine、Gemini）を同期的に呼び出すため、数秒〜数十秒のレスポンスタイムが発生
- **解決**: GitHub Actions で定期的にフィードを取得・要約し、結果を JSON として保存。Web アプリは保存済みデータを読むだけで即座に表示

運用して感触を確かめることを重視する。

---

## 2. スコープ

### やること

1. **GitHub Actions ワークフロー作成**
   - **新規ファイル**: `.github/workflows/fetch-feed.yml`（既存の `ci.yml` とは別）
   - 定期実行（1日1回、cron）
   - `uv run my-feed run` を実行して JSON 出力
   - JSON ファイルをコミット & プッシュ（`[skip ci]` で CI トリガー回避）

2. **データ永続化戦略（案B）**
   - Actions で `data/latest-feed.json` を生成してコミット
   - Web アプリ起動時に JSON を読み込んで DB に投入
   - SQLite DB (`data/my_feed.db`) はローカルのみ、git 管理外

3. **Web アプリの調整**
   - 起動時に `latest-feed.json` が存在すれば自動ロード
   - `/runs` (POST) の手動取得機能は残す（任意機能として）

4. **シークレット管理**
   - GitHub Repository Secrets に `GEMINI_API_KEY` を設定
   - ワークフローで環境変数として注入

5. **既存CI基盤との共存**
   - 既存の `ci.yml`（PR/push 時の lint/typecheck/test）はそのまま維持
   - 定期取得ワークフローは別ファイルとして独立
   - uv setup などの共通ステップは各ワークフローで定義（composite action 化は将来検討）

### やらないこと

- Actions 実行失敗時の追加通知（GitHub の標準ステータスで確認）
- 複数回/日の実行（コスト管理のため1日1回）
- リアルタイム取得の完全廃止（手動取得を残す）
- DB ファイル直接コミット（案A）
- 既存 CI ワークフローの変更（lint/typecheck/test は触らない）

---

## 3. アーキテクチャ

### 変更前（現状）

```text
ユーザー「いま取得」クリック
  → Web サーバーが同期的に fetch
    → Qiita API
    → Zenn API
    → GitHub Trending スクレイピング
    → Gigazine RSS
    → Gemini API（10記事要約）
  → 結果を DB 保存
  → ブラウザにレスポンス（数秒〜数十秒）
```

### 変更後（M3-Scheduled）

```text
【定期実行（GitHub Actions）】
  cron: 毎日 UTC 00:00
    → uv run my-feed run --json --out data/latest-feed.json
    → git commit & push

【Web アプリ起動時】
  → data/latest-feed.json を検出
  → 内容を DB に投入（既存の run_id は重複回避）

【ユーザーアクセス】
  → 最新データが即座に表示（ミリ秒単位）
  → オプション: 手動「いま取得」も可能
```

---

## 4. 既存CI基盤との関係

### 現在の CI 構成（PR #14, #16 でマージ済み）

```yaml
# .github/workflows/ci.yml
on:
  pull_request:
  push:
    branches: [main]

jobs:
  - lint (Ruff check + format check)
  - type-check (mypy)
  - test (pytest with coverage, network tests 除外)
    - カバレッジ測定（pytest-cov）
    - HTML レポートを Artifact として保存（30日間、ローカル完結）
```

**目的**: コード品質保証（PR レビュー時 + main マージ時）

**追加機能（PR #16）**:
- **pre-commit フック**: Ruff、trailing-whitespace、Conventional Commits 等
- **テストカバレッジ**: pytest-cov による測定、現在 86.23%
- **Issue テンプレート**: バグ報告、機能リクエスト、ドキュメント改善

### 新規追加する定期取得ワークフロー

```yaml
# .github/workflows/fetch-feed.yml (新規)
on:
  schedule:
    - cron: '0 0 * * *'
  workflow_dispatch:

jobs:
  - fetch (フィード取得 + JSON 出力 + commit & push)
```

**目的**: データ自動更新（開発とは独立）

### 共存の方針

| 観点 | CI ワークフロー | 定期取得ワークフロー |
|------|----------------|---------------------|
| **ファイル名** | `.github/workflows/ci.yml` | `.github/workflows/fetch-feed.yml` |
| **トリガー** | PR + main への push | cron (1日1回) + 手動 |
| **目的** | コード品質チェック | データ更新 |
| **git 操作** | なし（read-only） | commit & push (`[skip ci]`) |
| **Secrets** | なし | `GEMINI_API_KEY`（必須） |
| **実行時間** | 〜2-3分（カバレッジ含む） | 〜5分（API呼び出し含む） |
| **Artifact** | coverage HTML レポート（30日） | なし |

### `[skip ci]` の必要性

定期取得が `data/latest-feed.json` をコミットすると、それが main への push となり、`ci.yml` がトリガーされる可能性がある。これを防ぐため：

- コミットメッセージに `[skip ci]` を含める
- これにより CI ワークフローがスキップされ、無駄な実行を回避

```bash
git commit -m "chore: update feed [skip ci]"
```

### pre-commit フックとの関係

- **定期取得ワークフロー**: GitHub Actions 内で直接 `git commit` するため、**pre-commit フックは実行されない**
- **ローカル開発**: 開発者が手動で変更をコミットする際は pre-commit が実行される
- **影響**: 定期取得のコミットは pre-commit のチェックをバイパスするが、生成される JSON ファイルのみなので品質上の問題はない

### 将来の拡張可能性

- 共通ステップ（uv setup など）の composite action 化
- 定期取得失敗時の Slack 通知（別ワークフローとして追加）
- フィード更新後の自動デプロイ（M4 以降）
- 定期取得ワークフローでも pre-commit 相当のチェックを実行（必要に応じて）

---

## 5. タスク分解

### T0. 既存CI基盤の確認

- [x] `.github/workflows/ci.yml` が存在（PR #14, #16 でマージ済み）
  - lint (Ruff)、typecheck (mypy)、test (pytest with coverage) を実行
  - トリガー: `pull_request` と `push: branches: [main]`
  - カバレッジ測定、Codecov アップロード、Artifact 保存
- [x] `.pre-commit-config.yaml` が存在（PR #16 でマージ済み）
  - Ruff、trailing-whitespace、Conventional Commits 等
  - GitHub Actions 内のコミットでは実行されない（pre-commit フックはローカルのみ）
- [x] `Makefile` でローカルCI相当の操作が可能（`make ci`, `make test-cov` 等）
- [ ] 定期取得ワークフローが `ci.yml` と干渉しないことを確認
- **完了条件**: 新ワークフローのコミットが `[skip ci]` でCIをスキップできる

### T1. JSON 出力機能の確認

- [x] CLI で `--json --out` が機能している（M1 完了時点で実装済み）
- [ ] 出力形式が DB ロードに適しているか確認
- **完了条件**: `PipelineResult` を JSON serialize/deserialize できる

### T2. GitHub Actions ワークフロー作成

- [ ] `.github/workflows/fetch-feed.yml` を作成（`ci.yml` とは別ファイル）
  - トリガー: cron `0 0 * * *`（UTC 00:00 = JST 09:00）+ `workflow_dispatch`
  - 既存 `ci.yml` と同様の uv setup 手順を使用
  - `GEMINI_API_KEY` を secrets から注入
  - `uv run my-feed run --config config.example.toml --json --out data/latest-feed.json`
  - git config (bot user)
  - commit & push（`[skip ci]` でCIトリガー回避）
- [ ] 初回手動実行（`workflow_dispatch`）でワークフロー動作確認
- [ ] `ci.yml` が意図せずトリガーされないことを確認
- **完了条件**: Actions が成功して `data/latest-feed.json` がコミットされ、CI が走らない

### T3. Web アプリ起動時ロード機能

- [ ] `WebDeps` または `create_app` に JSON ロード処理を追加
  - 起動時に `data/latest-feed.json` の存在確認
  - 存在すれば `PipelineResult` にデシリアライズ
  - `run_store.save_run()` で DB に投入（既存 run_id は更新 or スキップ）
- [ ] 重複投入の防止ロジック
- **完了条件**: サーバー起動後すぐに最新データが `/` で表示される

### T4. README 更新

- [ ] セットアップ手順に GitHub Secrets 設定を追加
- [ ] 「定期自動取得」の説明セクション追加
- [ ] 手動取得との使い分けを明記
- **完了条件**: 初見ユーザーが定期取得の存在を理解できる

### T5. `.gitignore` 調整

- [ ] `data/my_feed.db` は git 管理外（既存）
- [ ] `data/latest-feed.json` は git 管理対象に追加
- **完了条件**: JSON はコミットされるが DB はされない

---

## 6. 完了条件（Exit Criteria）

- [ ] GitHub Actions が毎日 UTC 00:00 に自動実行される
- [ ] Actions が成功して `data/latest-feed.json` が更新・コミットされる
- [ ] 定期取得のコミット（`[skip ci]` 付き）が既存の `ci.yml` をトリガーしない
- [ ] 既存の CI ワークフロー（lint/typecheck/test/coverage）が正常に動作し続ける
- [ ] Web アプリ起動時に自動的に最新データがロードされる
- [ ] ブラウザアクセスで即座にフィードが表示される（同期API呼び出しなし）
- [ ] 手動取得機能も引き続き利用可能
- [ ] Actions 失敗時は GitHub UI でステータス確認できる
- [ ] `make ci` でローカルでもCIチェックが可能（既存機能の維持）
- [ ] pre-commit フックがローカル開発時に正常動作する（定期取得には影響しない）

---

## 7. 設定例

### GitHub Actions ワークフロー（`.github/workflows/fetch-feed.yml`）

```yaml
name: Fetch Feed Daily

on:
  schedule:
    - cron: '0 0 * * *'  # UTC 00:00 (JST 09:00)
  workflow_dispatch:  # 手動実行も可能

jobs:
  fetch:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"
        
      - name: Set up Python
        run: uv python install 3.12
        
      - name: Install dependencies
        run: uv sync --extra dev
        
      - name: Fetch feed
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: |
          uv run my-feed run \
            --config config.example.toml \
            --json \
            --out data/latest-feed.json
      
      - name: Commit and push
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add data/latest-feed.json
          git diff --staged --quiet || git commit -m "chore: update feed [skip ci]"
          git push
```

### `.gitignore` 追記

```gitignore
# SQLite DB (local only)
data/my_feed.db
data/my_feed.db-*

# Keep JSON feed in git
!data/latest-feed.json
```

---

## 8. worktree

- `cursor/m3-scheduled-<suffix>`
- M2 および M4-D（AI要約）が `main` 合流後に着手

---

## 9. コスト管理

- Gemini API: 1日1回実行 × 10記事 ≈ 1円/日 ≈ 30円/月
- GitHub Actions: 無料枠内（数分/日）
- リアルタイム性: 最大24時間遅延（許容範囲内と判断）

---

## 10. 今後の拡張可能性（M3-Scheduled 範囲外）

- 複数回/日実行（朝・昼・夕）
- Actions 失敗時の Slack/Email 通知
- 過去データの履歴管理（日付別 JSON）
- Vercel/Cloudflare Pages への自動デプロイ
