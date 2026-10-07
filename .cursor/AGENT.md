# AI エージェント開発ガイドライン

このファイルは AI エージェント（Claude / Cursor Agent）がコード変更を行う際に **必ず従うべきルール** をまとめたものです。

---

## 1. コード変更時の必須チェック

### 1.1 クラス変数 vs インスタンス変数の厳守

❌ **やってはいけないこと:**

```python
class Example:
    CONSTANT_VALUE = 100  # クラス変数（大文字）
    
    def method(self):
        return self.constant_value  # ❌ 未定義のインスタンス変数を参照
```

✅ **正しい実装:**

```python
class Example:
    CONSTANT_VALUE = 100  # クラス変数
    
    def method(self):
        return self.CONSTANT_VALUE  # ✅ クラス変数を参照（self.経由でもアクセス可能）
```

または

```python
class Example:
    def __init__(self):
        self.constant_value = 100  # インスタンス変数（小文字）
    
    def method(self):
        return self.constant_value  # ✅ インスタンス変数を参照
```

**ルール:**
- クラス変数は大文字スネークケース（`_CONSTANT`）で定義し、`self._CONSTANT` または `ClassName._CONSTANT` でアクセス
- インスタンス変数は小文字スネークケース（`_variable`）で定義し、`self._variable` でアクセス
- **参照時の大文字小文字を絶対に間違えない**

### 1.2 リファクタリング時の設定パラメータ保全

❌ **やってはいけないこと:**

```python
# Before
def create_model(temperature=0.5, max_tokens=1000, thinking_level="minimal"):
    return Model(temp=temperature, tokens=max_tokens, thinking=thinking_level)

# After（thinking_level が消失）
def create_model(temperature=0.5, max_tokens=1000):
    return Model(temp=temperature, tokens=max_tokens)  # ❌ thinking 設定が失われた
```

✅ **正しいリファクタリング:**

```python
# 全パラメータを保持し、使用箇所も更新
def create_model(temperature=0.5, max_tokens=1000, thinking_level="minimal"):
    return Model(
        temp=temperature,
        tokens=max_tokens,
        thinking=thinking_level  # ✅ すべてのパラメータを引き継ぐ
    )
```

**ルール:**
- リファクタリング前後で機能的同等性を保つ
- パラメータや設定項目を「静かに削除」しない
- 削除が必要な場合は **明示的に理由を説明し、ユーザー承認を得る**

### 1.3 テスト実行の必須化

❌ **やってはいけないこと:**

- コード変更後、テストを実行せずに完了報告
- テストが壊れていることに気づかない
- モック/フィクスチャだけで実際のクラスインスタンス化をテストしない

✅ **必ず行うこと:**

```bash
# 変更後は必ず関連テストを実行
pytest tests/test_module.py -v

# 可能なら全テストスイートを実行
pytest
```

**ルール:**
- **コード変更を push する前に必ずテストを実行する**
- テストが失敗した場合は修正してから push
- 新規クラス/関数には対応するテストケースを追加
- モックだけでなく、**実際のクラスインスタンス化をテストする**

---

## 2. エラーハンドリングと可観測性

### 2.1 エラー時の詳細情報出力

❌ **不十分なエラーログ:**

```python
except Exception as exc:
    logger.warning("Failed to process")  # ❌ 何が起きたか不明
```

✅ **詳細なエラーログ:**

```python
except Exception as exc:
    logger.warning(
        f"Failed to process item {item.id}: "
        f"{type(exc).__name__}: {exc}",  # 例外クラス名 + メッセージ
        exc_info=True  # スタックトレース出力
    )
```

または開発時：

```python
except Exception as exc:
    logger.exception(f"Failed to process item {item.id}")  # 自動的に exc_info=True
```

**ルール:**
- 例外をキャッチする場合は **必ず詳細を記録**
- 最低限 `type(exc).__name__`: `{exc}` を含める
- デバッグが必要な場合は `exc_info=True` または `logger.exception()` でスタックトレースを出力
- ユーザーに伝わらない「silent failure」を避ける

### 2.2 エラー伝播の原則

**ルール:**
- ライブラリ層での例外は適切にラップして上位層に伝える
- パイプライン処理など「部分的失敗を許容する」場合のみ、例外を握りつぶして継続
- それ以外の場合は **fail fast（早期失敗）** を原則とする

---

## 3. 設定管理の原則

### 3.1 設定の二重管理を避ける

**ルール:**
- **技術的パラメータ（temperature, max_tokens など）**:
  - コード内に定数として定義（`_CONSTANT`）
  - ユーザーが変更すべきでない値
  
- **ユーザー設定（enabled, model, paths など）**:
  - `config.toml` / `config.local.toml` で管理
  - ユーザーが環境に応じて変更する値

- **機密情報（API キー、トークンなど）**:
  - `.env` ファイル（git 管理外）または環境変数
  - 絶対にハードコードしない

### 3.2 設定の優先順位

明確な優先順位を定義：

```
1. 環境変数（最優先）
2. .env ファイル
3. config.local.toml（個人設定）
4. config.toml（デフォルト設定）
5. コード内定数（フォールバック）
```

---

## 4. PR レビュー前の自己チェックリスト

変更を push する前に必ず確認：

- [ ] 全ての変数参照（`self.xxx`）が実際に定義されているか確認した
- [ ] クラス変数とインスタンス変数の命名規則に従っているか確認した
- [ ] リファクタリングで設定パラメータが失われていないか確認した
- [ ] 関連するテストを実行し、すべて通過することを確認した
- [ ] 新規追加したクラス/関数にテストケースを追加した
- [ ] エラーハンドリングで詳細情報（例外クラス名、メッセージ）をログ出力している
- [ ] 機密情報（API キー等）がコードやログに漏れていないか確認した
- [ ] 設定項目が適切な場所（コード定数 vs config.toml vs .env）に配置されているか確認した

---

## 5. コミットメッセージとドキュメント

### 5.1 コミットメッセージ

```
<タイプ>: <簡潔な説明>

<詳細な説明（必要に応じて）>

- 変更理由
- 影響範囲
- 破壊的変更がある場合は明記
```

### 5.2 コード内ドキュメント

**ルール:**
- 自明なコメント（`# ループを回す`）は不要
- **非自明な意図、制約、トレードオフ**のみをコメントとして記載
- 公式ドキュメントからの引用や警告（例: "DO NOT CHANGE: Gemini 3.x default is 1.0"）は積極的に残す

---

## 6. このガイドラインの更新

- 新しいバグパターンが見つかった場合、このファイルに追加する
- 定期的に見直し、プロジェクト固有のルールを洗練させる

---

**最終更新:** 2026-10-07  
**対象:** my-feed プロジェクト全般
