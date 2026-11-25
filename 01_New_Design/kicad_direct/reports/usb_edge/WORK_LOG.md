# R-0035 作業ログ

開始: 2026-11-25 21:01 JST。設計・画像・検証・記録の作成完了: 2026-11-25 21:23 JST。約22分。Git反映はこの後に実施。
環境: Windows、PowerShell 7.6、KiCad CLI/pcbnew 10.0.8、Python、Shapely/NetworkX/Pillow、pypdfium2。

1. 最新mainのルールとR-0035調査を確認。空き設計Worktreeで `git switch -c codex/a2-r0035-usb-edge 5cce544232e1f0eb137ef95f5060eeea5c9729ef`。mainの既存プロジェクト変更、固定Workspaceのプロジェクト変更と.historyは保護。
2. PCB/プロジェクト/回路図/ルールをreports/usb_edge/beforeとcandidateへ複製。J1を+Y0.60mm、干渉5部品を局所移動する初期案を検証。取付穴とUSB5V配線、Y1とU1/C11が干渉したため未採用。最初の候補DRCには候補側のライブラリ未複製による警告も含まれ、既存librariesとテーブルのコピーで解消した。
3. Y1の角度を保って右へ1.325mm移す案へ変更。C13/FB1とD2/R13も局所調整。C11は元の位置に戻した。USB5Vを右側裏面経路で接続し、水晶・ESD・GND帰路を復旧。局所DRCの77→62→25→1→0件は試行ごとのJSONに保存。検証除外は追加していない。
4. 重複した試行配線、5Vの折り返し、D1のGNDパッド側面への近接を修正。FB1出力を0.20mmへ拡幅。`kicad-cli pcb drc --format json --severity-all --schematic-parity`、`sch erc --format json --severity-all`、`sch export netlist --format kicadxml`を実行。
5. 属性・モデル・全パッド・ネット・外形・ゾーン設定・既存設定を照合。品質スクリプトで前後の配線長、曲がり、グラフ、パッド近接、USB5V幅、電源順序を比較。`projection_audit.py`、`reference_coverage.py`でUSB/水晶直下を検査。数値結果と検出器の限界はREADMEに記載。
6. `pcb export pdf --mode-single` と `pcb render --side top/right`で表裏・3Dを出力。全体と拡大図を複数回確認。最終候補を専用ブランチのPCBへコピーし、保存後の再読込・DRC・候補とのバイト一致を確認。
7. 補助スクリプトではinspect.pyという名前が標準inspectと衝突したため改名。比較APIのオブジェクト表示、LIB_ID.Formatの呼出し、ERCのシート別JSON構造も修正し、最終集計を再実行した。これらの初回失敗を検証合格に数えていない。

変更はPCBと本レポート・補助スクリプト・作業ログ。回路図・ライブラリ・元の生成スクリプト・製造データは不変。実機特性・実装公差・ユーザーの最終判定は未確認。design-review-recordsを適用し、日本語記録はyomiyasuの方針で推敲した。

