# 届け方モデル — 契約ハブ + 並行トラック

| 項目 | 内容 |
|------|------|
| 呼び名 | **契約ハブ + 並行トラック**（仮。しっくりこなければ後で改名可） |
| 目的 | IF（契約）を先に固め、取得・スコア・出力・UI・永続化を並行 worktree で進める |
| 線形 Phase との関係 | 旧 Phase 1〜5 は本モデルへ **移し替え済み**（`phases/` は廃止） |

---

## 1. なぜこの形か

一本の Phase 列だと「01 が終わるまで 03 に触れない」ように見える。
実際は **契約さえ固まれば**、UI は Fake パイプラインで着手できる。

このリポジトリではその並行を実験したいので、計画も次の三層で書く。

1. **契約ハブ（Contract Hub）** — 型と Protocol だけ先に固定
2. **並行トラック（Tracks）** — 能力ごとに worktree で実装
3. **合流マイルストーン（Milestones）** — 繋がって「使える断面」になった地点

```text
                 [C0 契約ハブ]
                      |
     +--------+-------+--------+--------+
     |        |       |        |        |
  [T-Src]  [T-Score] [T-Md]  [T-Web]  [T-Store]
     |        |       |        |        |
     +----[M1 CLI 縦切り]-----+ |        |
              |                |        |
              +-------[M2 ローカル完成]--+
                           |
                    [M3 運用改善]
                           |
                    [M4 公開・発展]
```

---

## 2. 層の定義

### 2.1 契約ハブ（C0）

- 実ネットワーク・本番 UI・本物 SQLite は不要
- `Item` / Adapter / Strategy / pipeline / render / store の **署名と意味** を固定
- 他トラックはここを import して進む
- 契約を壊す変更は、実装トラックより **C0 変更を先に出す**

詳細: [contracts/c0-contract-hub.md](./contracts/c0-contract-hub.md)

### 2.2 並行トラック

| ID | 名前 | 役割 | 詳細 |
|----|------|------|------|
| T-Src | 取得 | 4 ソースの Adapter 実装 | [tracks/t-src.md](./tracks/t-src.md) |
| T-Score | スコア | 正規化と複数戦略 | [tracks/t-score.md](./tracks/t-score.md) |
| T-Md | Markdown | 壁打ち用出力 | [tracks/t-md.md](./tracks/t-md.md) |
| T-Web | Web UI | 取得ボタン・一覧・DL 導線 | [tracks/t-web.md](./tracks/t-web.md) |
| T-Store | 永続化 | 履歴・お気に入り SQLite | [tracks/t-store.md](./tracks/t-store.md) |

各トラックは **C0 のみを必須依存**とする（他トラックの完成を待たない）。
T-Web は FakeSource / FakeScorer / メモリ Store で進めてよい。

### 2.3 合流マイルストーン

| ID | 名前 | 意味 | 詳細 |
|----|------|------|------|
| M1 | CLI 縦切り | 実ソースで Top 10 が 1 コマンド | [milestones/m1-cli.md](./milestones/m1-cli.md) |
| M2 | ローカル完成 | ブラウザで取得〜お気に入り | [milestones/m2-local.md](./milestones/m2-local.md) |
| M3 | 運用改善 | 設定化・失敗可視化 | [milestones/m3-ops.md](./milestones/m3-ops.md) |
| M4 | 公開・発展 | 認証 / Actions / AI / Drive 等 | [milestones/m4-optional.md](./milestones/m4-optional.md) |

マイルストーン PR の主役は「新機能」より **結合と Fake の除去**。

---

## 3. worktree 運用ルール（実験用）

1. **C0 より前に本実装トラックを切らない**
2. 推奨: **1 worktree = 1 トラック**（または 1 マイルストーン）
3. トラック PR は契約を壊さない。壊すなら C0 を先に変更
4. T-Web の本番接続は M2 の明示タスク（それまでは Fake 可）
5. 方針変更は日付付きメモを `docs/plans/tech-catchup/` に追加

ブランチ命名例:

- `cursor/c0-contract-hub-<suffix>`
- `cursor/t-src-<suffix>`
- `cursor/t-web-<suffix>`
- `cursor/m1-cli-<suffix>`

---

## 4. 旧 Phase からの移し替え

| 旧 | 新 |
|----|----|
| Phase 0 設計 | 本 PR（計画ドキュメント）+ [APPROVAL.md](./APPROVAL.md) |
| Phase 1 CLI | **C0** + **T-Src** + **T-Score** → **M1** |
| Phase 2 Markdown | **T-Md**（M2 前に合流） |
| Phase 3 Web + 履歴 | **T-Web** + **T-Store** → **M2** |
| Phase 4 運用改善 | **M3** |
| Phase 5 発展 | **M4** |

`phases/` ディレクトリは廃止し、中身は上記へ移動済み。

---

## 5. 推奨着手順（並行の始め方）

```text
1. C0 を短くマージ
2. 同時に T-Src / T-Score / T-Md / T-Web / T-Store を着手可
3. T-Src + T-Score が揃ったら M1
4. M1 + T-Md + T-Web + T-Store で M2
5. 運用しながら M3、必要なら M4
```

実験の肝: **C0 完了時点で T-Web を開始してよい**。

## 6. 開発環境（追記）

- **当面: ホスト上の uv**（`pyproject.toml` / `uv.lock`）
- **必要になったら Docker** を追加する（二者択一ではない。コンテナ内でも uv）
- C0〜M2 では Docker 必須にしない。検討タイミングは環境差分の実害または M4
