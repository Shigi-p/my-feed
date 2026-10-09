# AGENTS.md — AIエージェント向けガイド

このリポジトリでエージェント（や人）と進めるときの基本姿勢と、情報の入口。

使い方: [README.md](./README.md)
未着手: [GitHub Issues](https://github.com/Shigi-p/my-feed/issues)

---

## 1. 基本姿勢

- **計画 → 承認 → 実装**の順を崩さない。いきなりコードを出さない
- 全体の流れ・変更箇所・トレードオフを先に示し、「実装してください」と言ったあとだけ、**小さいステップ**で進める
- **判断が必要なときだけ聞く。** 機械的な修正は任せ、方針・トレードオフ・意図が分かれる点だけ確認する
- **承認ポイントを意図的に置く。** 該当 Issue と、契約が変わるなら先の契約 PR
- **コードより理由。** 「なぜこの形か」「別案との差」を優先する
- **日本語で、短く、事実ベース。** 相槌や過剰な褒めは不要
- **方針の変更は git に残す。** 生きているガイドは直す。未着手は Issues

---

## 2. 新しいタスクを受けたら

1. 計画を示す（流れ・変更箇所・トレードオフ・不明点）
2. 必要なときだけ次を読む

| 知りたいこと | 参照先 |
|------------|--------|
| 使い方 | [README.md](./README.md) |
| 未着手の仕事 | [GitHub Issues](https://github.com/Shigi-p/my-feed/issues) |
| 実装ルール | [docs/guides/implementation.md](./docs/guides/implementation.md) |
| コードの読み順 | [docs/guides/reading-order.md](./docs/guides/reading-order.md) |
| レビュー観点 | [docs/guides/pr-review.md](./docs/guides/pr-review.md) |

3. 承認されたら小さく実装する

---

## 3. 判断を求めるタイミング

- 方針・トレードオフが分かれる点
- 契約（型・Protocol）の意味が変わりそうなとき
- 外部 API の選択・セキュリティ・認証
- 新しいツール・依存の導入

---

## 4. コミット前

- [ ] 計画（または Issue）と一致しているか
- [ ] [実装ルール](./docs/guides/implementation.md) を守っているか
- [ ] [レビュー観点](./docs/guides/pr-review.md) の該当項目を確認したか
- [ ] テストは書いたか（該当する場合）
