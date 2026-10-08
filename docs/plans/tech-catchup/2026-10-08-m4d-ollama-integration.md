# M4-D 拡張 — Ollama統合によるコストゼロ要約

| 項目 | 内容 |
|------|------|
| 日付 | 2026-10-08 |
| 依存 | M2完了（Gemini要約が既に動作） |
| 参考 | [ryochin/stingray](https://github.com/ryochin/stingray) |
| ゴール | 自宅PCでollamaを使った要約が選択可能。出先ではGeminiを利用 |

---

## 1. 背景・モチベーション

### 現状（M4-D完了時点）
- Gemini 3.5 Flash Lite で要約が動作（1記事0.1円）
- URL Contextで記事URLから直接取得・要約
- コストは実用的だが、頻繁に使うと積み上がる

### 改善提案
- **自宅PC利用時**: ollama（ローカルLLM）でコストゼロ運用
- **出先**: Geminiにフォールバック（必要な時だけコスト発生）

### 設計方針
- デフォルトはGemini（出先でコードを触れないため）
- 自宅PCでは環境変数 `SUMMARIZER_BACKEND=ollama` で切り替え
- ローカル実行を維持（サーバー常時稼働は不要）

### 参考実装
stingray（RSSリーダー + ollama要約）から以下を参考：
- 本文抽出ロジック（`content_snippet`）
- Ollama API呼び出しパターン
- 推奨モデル（`gemma4:e4b`）

---

## 2. 技術的な相違点と取り込む設計

### stingray vs my feed のアーキテクチャ差分

| 観点 | stingray | my feed | 取り込み |
|------|----------|---------|---------|
| **実行モデル** | サーバー常時稼働（cron） | オンデマンド実行 | 維持（変更なし） |
| **要約タイミング** | fetch時→DB保存→表示 | fetch→score→Top N要約 | 維持（変更なし） |
| **本文取得** | 事前抽出して`content_snippet`に保存 | Gemini URL Contextが自動取得 | **✅ 採用**（ollama用） |
| **並行処理** | asyncio + Semaphore | 同期処理 | 🔄 将来検討 |
| **永続化** | PostgreSQL | SQLite | 維持（変更なし） |

### 今回実装する設計

#### ✅ A. 本文抽出（必須）
- `Item.content_snippet: str` フィールド追加
- 各Source adapterで本文を抽出（300-500文字）
- ollama要約時にこれを使用（URL再取得不要）

**実装場所**:
- `models.py`: `Item` モデル拡張
- `sources/content_extractor.py`: 本文抽出ユーティリティ（新規）
- `sources/{zenn,qiita,gigazine}.py`: 本文抽出ロジック追加

**メリット**:
- ollamaでURL再取得が不要
- Geminiとの併用可能（Geminiは`content_snippet`を無視）
- パフォーマンス向上

#### ✅ B. Backend切り替え（必須）
- `summarizer.backend`: `"gemini"` | `"ollama"`（デフォルト: `"gemini"`）
- 環境変数 `SUMMARIZER_BACKEND` で上書き可能

**設定例**:
```toml
[summarizer]
enabled = true
backend = "gemini"  # デフォルト
model = "gemini-3.5-flash-lite"
ollama_model = "gemma4:e4b"

[summarizer.ollama]
base_url = "http://localhost:11434"
timeout = 120
```

**切り替え方法**:
```bash
# 自宅でollama利用
SUMMARIZER_BACKEND=ollama uv run my-feed serve

# 出先でGemini（デフォルト）
uv run my-feed serve
```

#### 🔄 C. 並行処理（将来検討）
- 現状: 順次実行（10記事×5秒=50秒）
- 将来: asyncio + Semaphore（10記事→15秒程度）
- 影響範囲が大きいため、今回は見送り

---

## 3. 実装計画

### Phase 1: 本文抽出基盤（PR #1）

**変更ファイル**:
```
src/my_feed/models.py
src/my_feed/sources/content_extractor.py  # 新規
tests/test_content_extractor.py           # 新規
```

**実装内容**:
1. `Item.content_snippet: str = ""` 追加
2. `extract_content_snippet(html: str, max_chars: int = 500) -> str` 実装
   - BeautifulSoup4で本文抽出
   - script/style/nav除去
   - シンプル実装（stingray参考）
3. 単体テスト追加

**Exit Criteria**:
- [ ] `Item.content_snippet` が追加されている
- [ ] `extract_content_snippet` が動作する
- [ ] テストが全てパスする
- [ ] 既存機能に影響がない（後方互換性）

---

### Phase 2: Source adapter統合（PR #2）

**変更ファイル**:
```
src/my_feed/sources/zenn.py
src/my_feed/sources/qiita.py
src/my_feed/sources/gigazine.py
tests/test_sources_*.py
```

**実装内容**:
1. 各adapterで本文HTMLを取得
2. `extract_content_snippet` で抽出
3. `Item.content_snippet` に設定
4. fixturesベースのテスト更新

**Exit Criteria**:
- [ ] Zenn/Qiita/Gigazineで`content_snippet`が抽出される
- [ ] 既存のfetch処理に影響がない
- [ ] テストが全てパスする

---

### Phase 3: Ollama Summarizer実装（PR #3）

**変更ファイル**:
```
src/my_feed/summarizer/ollama.py          # 新規
src/my_feed/config.py
config.example.toml
tests/test_summarizer.py
```

**実装内容**:
1. `OllamaSummarizer` クラス実装
   - `content_snippet` を使用
   - Ollama API (`/api/generate`) 呼び出し
   - stingrayのプロンプトパターン参考
2. `SummarizerConfig` 拡張
   - `backend: Literal["gemini", "ollama"]`
   - `ollama_model: str`
   - `OllamaConfig` 追加
3. config.example.toml更新
4. fixturesベースのテスト

**Exit Criteria**:
- [ ] `OllamaSummarizer` が動作する
- [ ] ollama接続失敗時は警告してスキップ
- [ ] テストが全てパスする

---

### Phase 4: Pipeline統合とドキュメント（PR #4）

**変更ファイル**:
```
src/my_feed/pipeline/run.py
README.md
docs/notes/sources.md  # ollama利用ガイド追加
```

**実装内容**:
1. `_build_summarizer` を `backend` で分岐
   - `backend="gemini"`: `GeminiSummarizer`
   - `backend="ollama"`: `OllamaSummarizer`
   - 環境変数 `SUMMARIZER_BACKEND` で上書き
2. README更新
   - ollamaセットアップ手順
   - backend切り替え方法
   - 推奨モデル（`gemma4:e4b`）
3. 結合テスト

**Exit Criteria**:
- [ ] Gemini/Ollama両方が動作する
- [ ] 環境変数で切り替え可能
- [ ] ドキュメントが整備されている
- [ ] 既存の全テストがパス

---

## 4. テスト戦略

### 単体テスト
- `extract_content_snippet`: HTML → テキスト抽出
- `OllamaSummarizer`: mock使用（実際のollama不要）

### 結合テスト
- Gemini要約（既存）
- Ollama要約（opt-in、`MY_FEED_OLLAMA=1`）
- backend切り替え

### 回帰テスト
- 既存のfetch→score→要約フローに影響なし
- Geminiのみ使う場合も問題なし

---

## 5. 非機能要件

### パフォーマンス
- 現状: 順次実行（許容範囲内）
- 将来: 並行処理で高速化（別PR）

### エラーハンドリング
- ollama接続失敗: 警告表示して要約スキップ
- Gemini APIエラー: 既存と同様（ログ出力）

### セキュリティ
- ollama: localhost接続のみ（ローカル実行前提）
- Gemini: APIキー管理は既存と同様

---

## 6. ドキュメント更新

### README.md
```markdown
### AI要約機能（デフォルト: Gemini）

**出先・通常利用**:
```bash
export GEMINI_API_KEY="your-key"
uv run my-feed serve
```

**自宅PCでコストゼロ運用**:
```bash
# ollama起動
ollama serve &
ollama pull gemma4:e4b

# ollamaモードで起動
SUMMARIZER_BACKEND=ollama uv run my-feed serve
```
```

### docs/notes/ollama-setup.md（新規）
- ollamaインストール手順
- 推奨モデル（`gemma4:e4b`）
- トラブルシューティング

---

## 7. 判断ログ

| 項目 | 判断 | 理由 |
|------|------|------|
| **デフォルトbackend** | Gemini | 出先でコードを触れないため |
| **切り替え方法** | 環境変数 | 設定ファイル編集不要で柔軟 |
| **並行処理** | 見送り | Protocol変更の影響範囲が大きい |
| **自動フォールバック** | 見送り | 手動切り替えで十分 |
| **推奨モデル** | gemma4:e4b | stingray実績あり、軽量 |

---

## 8. リスクと対策

| リスク | 影響 | 対策 |
|--------|------|------|
| ollama未インストール | 要約失敗 | 明確なエラーメッセージ表示 |
| 本文抽出失敗 | 要約品質低下 | 空の場合はタイトルのみで要約 |
| Gemini品質低下 | 既存ユーザー影響 | 後方互換性を維持 |

---

## 9. 完了条件

- [ ] Phase 1-4 の全PR がマージされている
- [ ] Gemini/Ollama両方が動作する
- [ ] 環境変数で切り替え可能
- [ ] ドキュメントが整備されている
- [ ] 既存の全テストがパス
- [ ] 新規テストがカバレッジを維持

---

## 10. 参考リンク

- [stingray リポジトリ](https://github.com/ryochin/stingray)
- [Ollama 公式](https://ollama.com/)
- [gemma4 モデル](https://ollama.com/library/gemma4)
