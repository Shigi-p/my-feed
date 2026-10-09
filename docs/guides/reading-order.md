# コードの読み順

ステータス: **草案**
対象: このリポジトリの処理の流れを、コードから理解したい人（とエージェント）

関連: [implementation.md](./implementation.md)（書くときのルール）、[`models.py`](../../src/my_feed/models.py)（型の正本）、[sources.md](../notes/sources.md)（取得手段の理由）

---

## 1. このドキュメントの使い方

型やフィールドをここに写さない。コードが正本。ここでは **見る順番** と、各停留所で何を確認する／見ないかだけを書く。

各停留所は次の形:

1. ファイル
2. この停留所で答える問い
3. 注目する点（3つ以内）
4. 今は見ないもの
5. 次へ進む条件

ソース実装から入ると、JSON のキーに引っ張られて全体が見えない。共通型 → 目次 → 差分の大きい実例、の順にする。

---

## 2. 停留所

### 2.1 用語集 — `src/my_feed/models.py`

**問い:** このプログラムがやり取りする単位は何か。

注目:

- `Item` と `ScoredItem` は別型。スコアは Item を壊さず包む
- `metrics` が `dict` なのは、ソース横断の共通指標が無いという意思
- `PipelineResult.status` と `source_errors` は対。1ソース失敗を結果として残す

今は見ないもの: 各ソースの JSON キー、スコア計算、Web

次へ進む条件: 「横断比較してよい値は `ScoredItem.score` だけ」と言えてから次へ

### 2.2 目次 — `src/my_feed/pipeline/run.py`

**問い:** 取得・順位・切り出し・要約は、どの順で、誰が切るか。

`run_pipeline` の上から下が、そのまま実行順。他ファイルの目次でもある。

注目:

- `fetch` の例外はループ内で止め、他ソースは続ける
- `strategy.score(items)[: config.top_n]` — Top N を切るのは scoring ではなく pipeline
- 要約はスコアの**後**、Top N に対してだけ。`get_scorer` ではなく `build_scorer(name, config)`（設定が効く理由）

今は見ないもの: Gemini のプロンプト、各アダプタのパース

次へ進む条件: 「層は Protocol を満たせば差し替えられる」が、この関数の呼び出し順と対応して見える

### 2.3 取得の契約と対比 — `sources/base.py` → 実例2つ

**問い:** バラバラな外部データを、同じ `Item` にどう寄せるか。

先に [base.py](../../src/my_feed/sources/base.py)。約束は `fetch() -> list[Item]`。ソース全体の失敗は例外、本当に0件なら `[]`。

実例は対比のために2つだけ見る。

| ファイル | 何の典型か |
|----------|------------|
| [zenn.py](../../src/my_feed/sources/zenn.py) | JSON。`likes` がある。`published_at` がある |
| [github_trending.py](../../src/my_feed/sources/github_trending.py) | HTML。`stars_today`。`published_at` が無い |

注目:

- どちらも最終成果は同じ `Item`
- 1件のパース失敗は `continue`、ソース全体の破損は `raise`
- `metrics` に何を入れ、何を諦めたか

今は見ないもの: `qiita.py` / `gigazine.py` の全文、HTML 正規表現の細部、HTTP ヘルパ

次へ進む条件: 「外部の形は違っても、scoring が見るのは `Item` だけ」と言えてから次へ。残り2ソースは、あとで [sources.md](../notes/sources.md) と突き合わせれば足りる

### 2.4 横断比較 — `scoring/base.py` → `normalize.py` → `hybrid.py`

**問い:** 横断比較してよい値は、どこで、何をして生まれるか。

strategy の種類より、**正規化が先**を見る。禁止ルール（生のいいね数で横断しない）の実装場所。

注目:

- [normalize.py](../../src/my_feed/scoring/normalize.py) はソースごとに正規化する。キー優先順は `likes` → `stocks` → `stars_today` → `stars` → `forks`
- 欠損は 0 でも 1 でもなく中立値（既定 0.5）。GIGAZINE は人気成分が常にこれ
- [hybrid.py](../../src/my_feed/scoring/hybrid.py) は足し算ではなく掛け算。GitHub は `published_at` が無いので recency も中立値になる

今は見ないもの: `fake` スコア（生 likes。テスト用の例外）、`recency_math.py` の式の導出

次へ進む条件: 「GIGAZINE の人気」と「GitHub の新しさ」が、なぜどちらも中立値になるかを自分で辿れる

### 2.5 永続化の境界 — `src/my_feed/store/base.py`

**問い:** 実行のスナップショットと、人が残したい記事は、なぜ別ストアか。

SQL は見なくてよい。2つの Protocol の入力型を見る。

注目:

- RunStore は `PipelineResult` 丸ごと。あとから Markdown やお気に入りにできる
- FavoriteStore は `Item` だけ。スコアは捨てる
- `remove` の引数は `favorite_id`（`Item.id` ではない）。`favorite_id_for` は読み取り専用

今は見ないもの: `sqlite.py` のスキーマ全文。分かればよいこと: 結果は JSON で丸保存している

次へ進む条件: 「お気に入り判定のために `add` してはいけない」が、`favorite_id_for` の存在理由として見える

### 2.6 出口は欲しいものだけ

ここまでで「一覧がどう選ばれるか」は終わる。先に進むのは、知りたい出口があるときだけ。

| 知りたいこと | 見るファイル | 見なくてよいもの |
|--------------|--------------|------------------|
| 貼り付け文書 | [output/markdown.py](../../src/my_feed/output/markdown.py) のセクション構成 | `formatters.py` の文言 |
| 画面の導線 | [web/app.py](../../src/my_feed/web/app.py) のルート（特に `POST /runs`） | Jinja の見た目 |
| AI要約 | [summarizer/base.py](../../src/my_feed/summarizer/base.py) の「失敗は None」 | プロンプト全文・モデルパラメータ |

Web は pipeline を再実装しない。`create_run` が `run_pipeline` → `save_run` → リダイレクト、が分かれば層の境界は確認できる。

---

## 3. このドキュメントを更新するとき

次のときだけ直す。フィールド追加だけでは直さない。

- 層が増えた／減った
- 停留所の「次のファイル」が変わった
- 型に現れない約束が変わった（例: 欠損値の扱い、ID の意味）

契約（Protocol / `models`）を変える PR では、読み順の矢印がまだ正しいかを見る。手順は [implementation.md §5](./implementation.md#5-契約変更のルール)。

---

## 変更履歴

| 日付 | 内容 |
|------|------|
| 2026-10-09 | 初版。図や型表ではなく、コードを見る順番と注目点を固定する |
