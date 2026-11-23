# AI PCB Design Test

AIによる回路・基板設計の実地検証プロジェクト（開始: 2026-11-19）。

## 3つの設計手段 × 2つの検証内容

**設計手段**
1. atopile + KiCad（配置・自動配線にFreerouting等を併用）
2. KiCad単独で回路図・PCBを直接作成・編集
3. EasyEDA Proで回路図・PCBを直接作成・編集

**検証内容**
- **A: 新規設計** — 1・2・3すべてで実施。同一の要求仕様を与え、結果と工程を比較する。
- **B: 既存KiCad設計の修正** — **2のみ**で実施。既存の人間設計を保護しながら変更する。

| 設計手段 | A: 新規設計 | B: 既存KiCad修正 |
| --- | --- | --- |
| 1. atopile + KiCad | A-1 | 対象外 |
| 2. KiCad | A-2 | B-2 |
| 3. EasyEDA Pro | A-3 | 対象外 |

検証ケースは合計4つ。詳しい評価項目は `docs/comparison_matrix.md`。

## KiCadで最新A-2を開く場所

**固定ローカルWorktree（ローカルCodexによる初回セットアップが必要）**

```text
<リポジトリ>/workspaces/A-2/01_New_Design/kicad_direct/a2_usb_uart.kicad_pro
```

`main/01_New_Design/kicad_direct/`にあるA-2回路図は初期設計であり、R-0016まで修正された最新版ではありません。固定Worktreeはリポジトリ内に作りますが、Gitの`workspaces/`をignoreするためGitHub上には表示されません。詳細は[固定ワークスペース運用](docs/design_workspaces.md)を参照。

## ディレクトリ
- `01_New_Design/specs/` — A-1/A-2/A-3に共通の要求仕様
- `01_New_Design/atopile/` — A-1の成果物
- `01_New_Design/kicad_direct/` — A-2の成果物
- `01_New_Design/easyeda/` — A-3の成果物
- `02_Design_Modification/` — B-2だけの作業（KiCad既存設計修正）
- `docs/` — 議論、決定、作業、ツール環境、評価

## スキル・出典

`.agents/skills/pcb-pipeline/` に [nobkat/auto-pcb-skill](https://github.com/nobkat/auto-pcb-skill) の `pcb-pipeline` スキルを、試験用に取り込んでいます（MIT License）。出典、取得リビジョン、ライセンスについては `THIRD_PARTY_NOTICES.md` を参照してください。

Codexからの利用: `$pcb-pipeline`。

回路図作図用の独立追加スキル：`.agents/skills/schematic-design/`（電気的同一性・品質確認）、`.agents/skills/schematic-style-standard/`（V3系の作図スタイル）。回路図を作成・修正する自然言語の指示で、共通スキルと標準スタイルを自動適用する（手動のスキル名指定は不要）。既存の`pcb-pipeline`を改変せず、別スタイルを将来追加できる構成。

**注意:** オリジナルはmacOS/Linux向け。Windows環境での実行可否・必要な変更は未検証。スキルを配置しただけではatopile/KiCad/Freerouting/Java等はインストールされません。

レビュー議事録の自動整理と品質チェックには、独立スキル[design-review-records](.agents/skills/design-review-records/SKILL.md)を適用します。回路設計・回路図・PCB・製造のレビュー台帳は共通で、変更履歴と技術的な判断を保持します。

## 記録と安全

- `AGENTS.md`: Codexの作業ルール
- `docs/discussion_log.md`: 議論・技術的仮説
- `docs/decision_log.md`: 決定と判断理由
- `docs/work_log.md`: 実施作業・結果・検証証跡
- `docs/report_outline.md`: 後日レポート化するための章立て
- [回路図・基板図の横並び比較（ユーザーレビュー前）](docs/initial_3way_review.md)
- [3方式の統合レポート](docs/design_integration_report.md)
- [将来構想：設計ノウハウを蓄積するAI設計エージェント（改訂前提）](docs/future_design_agent_vision.md)
- [A-2 V3-polish 回路図レビュー候補版の一次確認](docs/a2_schematic_v3_polish_assistant_review.md)

設計結果はERC/DRCだけで妥当と判断せず、部品・回路・RF/EMC・熱・製造性・実機動作を別途確認すること。

## 参考

- [検討の発端となった記事](https://note.com/energylab/n/nd24d482f28ca)
- [auto-pcb-skill](https://github.com/nobkat/auto-pcb-skill)

## EasyEDA Proの導入

A-3ではEasyEDA Proのデスクトップ版と公式CLI/Extension APIを使う。導入・確認方法は `docs/easyeda_setup.md`。使用ツールの導入状況と実際の動作検証は別に記録する。

- 公式: https://prodocs.easyeda.com/en/api/guide/cli.html
- AI向け手順: https://prodocs.easyeda.com/storage/texts/api/guide/cli-for-ai.md
