# 共通レビュー台帳

正本はmainの本ファイル。運用は[README](README.md)、個別詳細は[details/](details/)、ひな形は[詳細テンプレート](templates/review_detail.md)を参照する。

登録1件。発行済みIDは`R-0001`。過去レポートからの自動転記は行っていない。

| ID | 指摘日時 | 指摘者 | 対象工程 | 対象設計 | 対象箇所 | 重要度 | 指摘内容 | 対応内容 | 対応状況 | 対応後判定 | 判定者 | 判定日時 | 修正先 | 証跡 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [R-0001](details/R-0001.md) | 2026-11-22 17 JST | ユーザー | 回路設計 | A-2、experiment/A2-schematic-v3-polish、778ab8896a4f9b71efba0c45f701cbf2fdfc2cac | a2_usb_uart.kicad_sch、D1、U1.6/7、USB_D-/USB_D+ | Major | FT232HのDP/DM耐圧を調査し、D1で問題ないか確認する | Majorは暫定。承認に基づきD1/D5をESD321DPYR×2へ変更。ERC前後0件、期待したESD端子差分以外の属性・接続は一致。PCB・既存BOMは未更新、保護協調・実機試験は未検証 | 完了 | OK | ユーザー | 2026-11-22 17 JST | codex/a2-r0001-esd321、e4e46cf7f6c4286d6ff57e220f6d0643bf028347 | [詳細](details/R-0001.md)。指摘17:07 JST、OK判定17:36 JSTはいずれもユーザー回答で確認 |
