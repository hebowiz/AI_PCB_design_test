# AI PCB Design Test

AIによる回路・基板設計の実地検証プロジェクト（開始: 2026-11-19）。

## 検証テーマ

1. **新規設計** — AIが回路・部品・PCB配置・配線・製造データまで生成する。まず atopile + KiCad + Freerouting のパイプラインを検証し、KiCad直接編集方式も比較する。
2. **既存設計の修正** — 人間が作成したKiCad回路図・PCBをAIが部分的に編集する。元の設計と変更禁止箇所の保全を重視する。

## スキル・出典

`.agents/skills/pcb-pipeline/` に [nobkat/auto-pcb-skill](https://github.com/nobkat/auto-pcb-skill) の `pcb-pipeline` スキルを、試験用に取り込んでいます（MIT License）。出典、取得リビジョン、ライセンスについては `THIRD_PARTY_NOTICES.md` を参照してください。

Codexからの利用: `$pcb-pipeline`。

**注意:** オリジナルはmacOS/Linux向け。Windows環境での実行可否・必要な変更は未検証。スキルを配置しただけではatopile/KiCad/Freerouting/Java等はインストールされません。

## 記録と安全

- `AGENTS.md`: Codexの作業ルール
- `docs/discussion_log.md`: 議論・技術的仮説
- `docs/decision_log.md`: 決定と判断理由
- `docs/work_log.md`: 実施作業・結果・検証証跡
- `docs/report_outline.md`: 後日レポート化するための章立て

設計結果はERC/DRCだけで妥当と判断せず、部品・回路・RF/EMC・熱・製造性・実機動作を別途確認すること。

## 参考

- [検討の発端となった記事](https://note.com/energylab/n/nd24d482f28ca)
- [auto-pcb-skill](https://github.com/nobkat/auto-pcb-skill)
