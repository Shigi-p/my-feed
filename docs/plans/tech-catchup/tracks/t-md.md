# T-Md — Markdown 出力トラック

| 項目 | 内容 |
|------|------|
| 依存 | **C0 のみ**（偽 `ScoredItem` で開発） |
| 合流先 | M2（必須）、CLI からの書き出しは M1 後でも可 |
| ゴール | Gemini / ChatGPT に貼れる bundle / single Markdown を純関数で生成できる |

---

## 1. 目的

リストを壁打ち用プロンプト素材に変換する。  
LLM API は使わない（ルールベース抜粋 + 定型テンプレ）。

---

## 2. スコープ

### やること

- 抜粋整形（1〜3 行）
- 「なぜ今見るか」一文
- 壁打ち用の問い定型ブロック
- `render_bundle` / `render_single`
- スナップショットテスト
- CLI から `.md` 書き出し（または関数のみ先に完成し、CLI は M1 結合時）

### やらないこと

- LLM API
- Drive アップロード
- Web の DL ボタン実装（T-Web が関数を呼ぶ）

---

## 3. 各項目の必須要素

| 要素 | 初期の作り方 |
|------|----------------|
| タイトル / URL / 出典 | フィールドそのまま |
| 抜粋 | HTML 除去 → 最大 3 文 or 文字上限 |
| タグ | あれば列挙、なければ省略 |
| 見る価値 | scorer / source / score からテンプレ文 |
| 壁打ち問い | 定型 2〜3 問（タイトル埋め込みは任意） |

### bundle 見出し例

```markdown
# my feed — YYYY-MM-DD HH:mm
- scorer: hybrid
- count: 10
```

末尾に「Gemini への貼り付け導入」短文を付けてよい。

---

## 4. タスク分解

### T1. ViewModel + excerpt / value_line / prompts

- [ ] 純関数化
- [ ] 空入力でも落ちないテスト
- **完了**: ダミー ScoredItem から文字列部品が出せる

### T2. bundle / single

- [ ] フォーマット固定
- [ ] スナップショットテスト
- **完了**: fixtures から見た目確認できる

### T3. CLI 接続（任意・早めで可）

- [ ] `--out-md` or `render-md`
- **完了**: ファイルまたは stdout に出せる

### T4. 実地確認

- [ ] Gemini に貼って壁打ちできることを確認
- **完了**: 使い方を README に短く書く

---

## 5. 完了条件

- [ ] bundle / single が契約どおりの純関数で提供される
- [ ] 必須要素が揃う
- [ ] LLM 非依存
- [ ] T-Web が DL にそのまま使える

---

## 6. worktree

- `cursor/t-md-<suffix>`
