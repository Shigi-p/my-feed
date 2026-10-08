# T-Src — 取得トラック

| 項目 | 内容 |
|------|------|
| 依存 | **C0 のみ** |
| 合流先 | M1（必須）、M2 |
| ゴール | 4 ソースの Adapter が `list[Item]` を返せる |

---

## 1. 目的

外部からの取得と共通 `Item` への正規化だけを担う。
スコアも Markdown も UI も扱わない。

---

## 2. スコープ

### やること

- `SourceAdapter` 実装: Zenn / Qiita / GIGAZINE / GitHub Trending
- レジストリ登録
- 1 エントリ失敗時のスキップ
- fixtures ベースのパーステスト（ネットワーク無し推奨）
- 取得経路の短い調査メモ（必要なら `docs/notes/`）

### やらないこと

- スコアリング
- Top N 選定
- Web / DB / Markdown 本テンプレ

---

## 3. 各ソース方針

| ソース | 第1候補 | metrics 例 | 備考 |
|--------|---------|------------|------|
| Zenn | 公開フィード / API | likes 等 | スクレイピングは最終手段 |
| Qiita | 公開 API or RSS | likes / stocks | レート制限・トークン要否を着手時確認 |
| GIGAZINE | サイト RSS | なし可 | **フィルタなし**（口は M3） |
| GitHub Trending | 非公式 HTML 等 | stars / forks（取れる範囲） | **隔離**。壊れても他に影響しない |

エラー方針:

- Adapter 内の一時障害 → 例外（pipeline 側で捕捉）
- 真に 0 件 → 空リスト
- エントリ単位パース失敗 → その件だけスキップ

---

## 4. タスク分解

### T1. Adapter 実装枠の確認

- [ ] C0 の `base.py` / registry に接続
- **完了**: Fake 以外のモジュールを追加できる

### T2〜T5. ソースごと

- [ ] Zenn
- [ ] Qiita
- [ ] GIGAZINE
- [ ] GitHub Trending
- **各完了**: `fetch()` が 1 件以上、または意図的スキップ理由がログに出る

### T6. 障害耐性

- [ ] Trending 擬似障害でも他ソースのテストが通る
- **完了**: 隔離がテストで示せる

---

## 5. 完了条件

- [ ] 4 Adapter がレジストリにある
- [ ] 設定の `enabled_sources` で読み込める（C0 設定を利用）
- [ ] ネットワーク無しパーステストが主なソースで用意されている
- [ ] M1 が実 fetch を繋げる状態

---

## 6. worktree

- `cursor/t-src-<suffix>`
- ソースごとにコミットを分けるとレビューしやすい
