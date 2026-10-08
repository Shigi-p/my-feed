# UI コードリファクタリング計画

**作成日**: 2026-10-08  
**ステータス**: 提案中  
**対象**: Web UI（`src/my_feed/web/templates/`、スタイリング）

---

## 背景・目的

現在の Web UI は M2（ローカル完成）で機能的には完成しているが、コード面で以下の課題がある：

- CSS が `base.html` の `<style>` タグ内に全て埋め込まれている（約170行）
- スタイルと HTML が分離されておらず、保守性に懸念
- アクションボタン部分など、繰り返し記述されているコードがある
- 今後の UI 改善（デザイン調整）を見据え、コード基盤を整えておきたい

**目的**: 見た目を変えずに、コード構造を整理し、将来の UI 改善を容易にする。

---

## 方針

### 1. HTML と CSS の分離

- `base.html` 内の `<style>` タグを削除
- 外部ファイル `src/my_feed/web/static/css/style.css` を作成
- FastAPI の `StaticFiles` マウントで配信

### 2. SCSS の導入

- **ツール**: `dartsass-python`（Python ベース、`pip install` で完結）
- **ソース**: `src/my_feed/web/static/scss/style.scss`
- **出力**: `src/my_feed/web/static/css/style.css`（Git 管理しない）
- **ビルド**: 開発時は watch モード、本番は起動前ビルド

#### SCSS のメリット
- ネスト記法でセレクタ階層が見やすい
- 変数を CSS カスタムプロパティと併用（`:root` の変数はそのまま、追加の内部変数を SCSS で定義）
- 将来的に部分ファイル（`_variables.scss`, `_components.scss`）への分割が容易

### 3. コンポーネント化（重複削除）

**方針**: Jinja2 の `{% include %}` と `{% macro %}` を使い分ける

| 対象 | 方法 | 理由 |
|-----|------|------|
| **ページ構造・セクション** | `{% include %}` | 1ページに1回、親のスコープをそのまま使う |
| **繰り返し UI パーツ** | `{% macro %}` | 異なるデータで複数回呼ぶ、引数が明確 |

#### 具体的な対象

**現状の重複箇所**:
- アクションボタン（お気に入り追加/解除、MD ダウンロード）
  - `_item_list.html` 内で各アイテムごとに記述
  - `favorites.html` でも類似の構造

**リファクタリング後**:
- `templates/macros.html` を作成
- `{% macro action_buttons(item, run_id, is_favorite, favorite_id, next_url) %}` を定義
- `_item_list.html` と `favorites.html` から呼び出し

**将来の拡張候補**（今回は対象外）:
- スコア表示の `{% macro score_badge(score) %}`
- ソース名の `{% macro source_label(source) %}`

---

## 詳細設計

### ディレクトリ構造（変更後）

```
src/my_feed/web/
├── static/
│   ├── scss/
│   │   └── style.scss          # SCSS ソース（Git 管理）
│   └── css/
│       └── style.css           # ビルド出力（Git 管理しない）
├── templates/
│   ├── base.html               # <link rel="stylesheet"> に変更
│   ├── macros.html             # 新規作成
│   ├── _item_list.html         # マクロを import して使う
│   ├── favorites.html          # マクロを import して使う
│   └── ... (他は変更なし)
└── app.py                      # StaticFiles マウント追加
```

### `.gitignore` 追加

```
src/my_feed/web/static/css/
```

### `pyproject.toml` への依存追加

```toml
[project]
dependencies = [
    # ... 既存 ...
    "dartsass>=0.3.0",
]
```

### 開発フロー

#### 開発時（watch モード）

```bash
# ターミナル1: SCSS watch
uv run python -m dartsass src/my_feed/web/static/scss:src/my_feed/web/static/css --watch

# ターミナル2: サーバー起動
uv run my-feed serve
```

#### 本番起動前（手動ビルド）

```bash
uv run python -m dartsass src/my_feed/web/static/scss:src/my_feed/web/static/css
uv run my-feed serve
```

**注**: 将来的に `my-feed serve` コマンド内で自動ビルドを組み込む選択肢もあるが、今回は明示的な手動ビルドとする（シンプル・透明性重視）。

---

## 実装ステップ

### Step 1: 環境準備
1. `dartsass-python` を `pyproject.toml` に追加
2. `uv sync` で依存インストール
3. `.gitignore` に `src/my_feed/web/static/css/` を追加

### Step 2: CSS 分離
1. `src/my_feed/web/static/scss/style.scss` を作成
2. `base.html` の `<style>` 内容を `style.scss` にコピー
3. SCSS ビルドを実行して `style.css` を生成
4. `app.py` に `StaticFiles` マウントを追加
5. `base.html` の `<style>` を削除、`<link rel="stylesheet">` に変更
6. ローカルで動作確認

### Step 3: コンポーネント化
1. `templates/macros.html` を作成
2. `action_buttons()` マクロを定義
3. `_item_list.html` を書き換え（`{% import %}` + マクロ呼び出し）
4. `favorites.html` を書き換え
5. ローカルで動作確認（見た目が変わっていないこと）

### Step 4: 動作確認・テスト
1. `pytest tests/test_m2_web.py` が通ることを確認
2. 各ページの表示を目視確認（`/`, `/runs`, `/favorites`, `/runs/{run_id}`）
3. お気に入り追加/解除が動作することを確認

### Step 5: ドキュメント更新
1. `README.md` の開発セクションに SCSS ビルドの説明を追加
2. この計画書を最終化

---

## トレードオフ・懸念事項

### SCSS 導入のトレードオフ

**メリット**:
- ネスト記法で可読性向上
- 将来的なファイル分割が容易
- CSS の保守性向上

**デメリット**:
- ビルドステップが増える（開発時に watch 起動が必要）
- 初見の開発者が SCSS ビルドを忘れる可能性

**対策**:
- README に明記
- 将来的に `my-feed serve --watch` のようなコマンドを追加する選択肢を残す

### コンポーネント化の懸念

**懸念**: マクロの引数が増えると呼び出しが複雑になる

**対策**:
- 今回は必要最小限の引数に留める
- 将来、引数が5個を超えるようなら dict で渡す方式を検討

---

## 非機能要件

- **互換性**: 見た目が変わらないこと（リファクタリングのみ）
- **テスト**: 既存の `test_m2_web.py` が全て通ること
- **レスポンシブ**: 既存のメディアクエリを維持

---

## 将来の展望（今回は対象外）

このリファクタリング後、以下の改善が容易になる：

- AI 要約の視認性向上（背景色・パディング）
- スコア表示の工夫（バッジ化、数値を隠す）
- ボタンラベル改善
- タブレット対応（メディアクエリ追加）
- ダークモード対応（CSS カスタムプロパティの切り替え）

---

## チェックリスト

実装完了前に確認すること：

- [ ] 全ページが正常に表示される
- [ ] お気に入り追加/解除が動作する
- [ ] Markdown ダウンロードが動作する
- [ ] `pytest tests/test_m2_web.py` が通る
- [ ] SCSS watch モードが動作する
- [ ] README にビルド手順が記載されている
- [ ] `.gitignore` に CSS 出力が含まれている

---

## 承認

この計画に問題がなければ、実装を開始します。
