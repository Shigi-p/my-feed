# CI自動化 レベル2: 開発体験の向上

## 概要

レベル1（Ruff, mypy, GitHub Actions）に加えて、開発者の体験を向上させる機能を導入しました。

## 導入した機能

### 1. pre-commit フック

コミット前に自動でコード品質チェックを実行します。

#### インストール

```bash
make pre-commit-install
```

または

```bash
uv run pre-commit install
uv run pre-commit install --hook-type commit-msg
```

#### 実行されるチェック

- **Ruff**: リント・フォーマット
- **trailing-whitespace**: 行末の空白削除
- **end-of-file-fixer**: ファイル末尾に改行追加
- **check-yaml/toml/json**: 構文チェック
- **check-merge-conflict**: マージコンフリクトマーカー検出
- **check-added-large-files**: 巨大ファイル検出（500KB以上）
- **conventional-pre-commit**: コミットメッセージ形式チェック

#### 手動実行

```bash
make pre-commit-run
# または
uv run pre-commit run --all-files
```

#### スキップ（緊急時のみ）

```bash
git commit --no-verify -m "message"
```

### 2. テストカバレッジ測定

pytest-cov を使ったカバレッジ測定を導入しました。

#### 実行方法

```bash
make test-cov
```

#### レポート形式

- **ターミナル出力**: 各ファイルのカバレッジ率とミッシング行番号
- **HTML**: `htmlcov/index.html` で詳細レポート
- **XML**: `coverage.xml` で CI ツール用（Codecov 等）

#### カバレッジ設定

`pyproject.toml` の `[tool.coverage]` セクションで設定：

- **除外パターン**: `pragma: no cover`, Protocol クラス等
- **精度**: 小数点2桁
- **ミッシング行表示**: 有効

#### 現在のカバレッジ

```
TOTAL: 86.23%
```

主な未カバー箇所：
- `cli.py`: CLIエントリーポイント（統合テストが必要）
- `gemini.py`: 外部API呼び出し部分
- `http_util.py`: ネットワーク関連

### 3. Issue テンプレート

GitHub で Issue を作成する際のテンプレートを用意しました。

#### テンプレート種類

1. **バグ報告** (`.github/ISSUE_TEMPLATE/bug_report.md`)
   - 再現手順、期待動作、実際の動作
   - 環境情報（OS, Python, uv, my-feed バージョン）

2. **機能リクエスト** (`.github/ISSUE_TEMPLATE/feature_request.md`)
   - 提案する機能、解決したい課題
   - トラック・マイルストーンとの関係

3. **ドキュメント** (`.github/ISSUE_TEMPLATE/documentation.md`)
   - 対象ドキュメント、現状の問題、提案する改善

#### 使い方

GitHub の Issues → New issue → テンプレートを選択

### 4. GitHub Actions の強化

CI パイプラインにカバレッジ関連の機能を追加しました。

#### 新機能

- **Codecov アップロード**: PR でカバレッジレポートを自動アップロード（要 `CODECOV_TOKEN`）
- **Artifact 保存**: カバレッジ HTML レポートを 30 日間保存
  - Actions タブ → 該当 run → Artifacts → `coverage-report` からダウンロード

## 開発フロー

### 通常の開発（pre-commit 使用時）

```bash
# 1. コードを書く
vim src/my_feed/some_file.py

# 2. ステージング
git add .

# 3. コミット（自動でチェック実行）
git commit -m "feat: 新機能を追加"
# → pre-commit が自動実行
# → 問題があれば修正して再コミット

# 4. プッシュ
git push
```

### 手動チェックする場合

```bash
# フォーマット
make format

# 全チェック
make ci

# カバレッジ確認
make test-cov
open htmlcov/index.html
```

### PR作成前のチェックリスト

- [ ] `make ci` が通る
- [ ] 新規コードのテストを追加した
- [ ] カバレッジが下がっていない（重要な部分）
- [ ] PRテンプレートのチェックリストを確認した

## トラブルシューティング

### pre-commit が遅い

初回実行時は各フックの環境構築が必要で数分かかります。2回目以降は高速です。

### pre-commit をスキップしたい

緊急時のみ `--no-verify` を使用してください：

```bash
git commit --no-verify -m "hotfix: 緊急修正"
```

### カバレッジレポートが生成されない

`make test` ではカバレッジは測定されません。`make test-cov` を使用してください。

### Conventional Commits とは？

コミットメッセージの形式規約です：

```
<type>: <subject>

<body>
```

**主な type**:
- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメント
- `refactor`: リファクタリング
- `test`: テスト追加・修正
- `chore`: その他（依存関係更新等）

**例**:
```
feat: AI要約機能を追加

Gemini API を使った記事要約機能を実装。
```

形式が間違っている場合、pre-commit がエラーを出します。

## 参考

- pre-commit: https://pre-commit.com/
- pytest-cov: https://pytest-cov.readthedocs.io/
- Conventional Commits: https://www.conventionalcommits.org/
