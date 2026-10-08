# 並行トラック（Tracks）

C0 契約に対して、能力ごとに実装する単位。
原則 **1 worktree = 1 トラック**。他トラックの完成を待たない。

| ID | ファイル | 依存 |
|----|----------|------|
| T-Src | [t-src.md](./t-src.md) | C0 |
| T-Score | [t-score.md](./t-score.md) | C0 |
| T-Md | [t-md.md](./t-md.md) | C0 |
| T-Web | [t-web.md](./t-web.md) | C0（Store/Markdown は Fake 可） |
| T-Store | [t-store.md](./t-store.md) | C0 |

親: [../delivery-model.md](../delivery-model.md)
