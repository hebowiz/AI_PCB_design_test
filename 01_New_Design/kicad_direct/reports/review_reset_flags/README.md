# R-0014・R-0015 作図修正

ユーザーの「一括修正を」に基づき、R2/C22の近接配置とPWR_FLAGの上向き統一を実施した。送信日時は未確認。承認済みの`7f0941b45309ad069e947849772c3ecf7c1d1e61`を基準に、独立した既存Worktreeを再利用し、新規ブランチ`codex/a2-review-reset-flags`で局所編集した。

## 対応内容

| ID | 変更 | 結果・判断理由 |
| --- | --- | --- |
| R-0014 | R2を横向きにしてU1左側へ移し、C22をその右側のRESET_N分岐から下向きGNDへ縦配置。+3V3・GND・文字・接続点を追従させ、実線を短縮した | U1.34からの図面上の水平距離はR2が137.16→44.45mm、C22が137.16→34.29mm。ピン直近の電源パスコンを動かさず、RCとU1の対応を追いやすくした。C3/C4の対応注記だけを移動して干渉を避けた |
| R-0015 | #FLG05と#FLG06を180度から0度へ回転 | 全7個が上向き。端子位置・ネットは維持。SW2のUSB5V_OUTとSW3のVIO_OUTの水平線上に上向き記号を表示した |

R2=10kΩ、C22=100nFと既存型番を維持した。RESET_NはR2とC22の分岐からU1.34 RESET#まで実線接続であり、ラベルによる省略へ置き換えていない。水平距離は回路図上の部品中心とピン端点との差で、PCB上の距離・経路長ではない。今回の位置は電源パスコンとの干渉を避けた配置で、U1との距離を最小化するための全面再配置はしていない。

図面のレビュー状態注記2か所は今回のIDへ更新した。他の電源・UART・USB・発振・EEPROM・LED回路の部品配置は維持した。元のV3-polishおよび承認済み設計ブランチへ変更を加えていない。

## 検証

[verification.json](verification.json)の全項目が合格。55実部品・193端子・54ネットの接続と、部品番号・値・型番・フットプリント・その他属性が前後で一致する。全シンボルの参照番号・既存UUID、埋込みシンボル定義、DNP・BOM設定も一致。R2/C22・対応電源/GND・対象FLAG以外のシンボルインスタンスは位置・文字を含め不変。

XMLネットリストは部品・ライブラリ部品・ネット名・端子属性を正規化して完全一致した。生成日時、出力元パス、ネットコード、列挙順の生成差分だけを除外した。[比較前](canonical_netlist_before.json)と[比較後](canonical_netlist_after.json)を保存している。

ERCは前後ともエラー0件・警告0件。既存無視設定single_global_label、four_way_junction、simulation_model_issue、footprint_filterを維持し、新規除外はない。回路図以外の既存A-2ファイル562個は不変。PCB、BOM、Gerber、ライブラリ、既存生成スクリプト・過去成果物は変更していない。PCB未変更のためDRCは再実行していない。

## 図面確認と作業ログ

2026-11-22 20:59:33 JSTに開始。21:02に初回出力し、全体・RESET周辺・FLAG周辺を確認した。R2を回転した際、Reference/Valueが縦表示になり、移したC4注記も配線と重なったため、21:03に文字方向と注記位置を修正した。21:04にレビューID注記を更新して最終出力し、全体図と拡大図を確認した。修正後のPDF・PNG出力は計3回。設計修正と検証は約5分、文書・台帳保存を含む所要時間はmain作業ログに記録する。

環境はWindows、PowerShell 7.6、KiCad 10.0.8、同梱Python 3.11.5、Poppler 26.07.0。コマンドは正常終了。[commands.json](commands.json)に実行コマンド・時刻・終了コードを記録した。日本語本文はyomiyasuで推敲した。

## 成果物と再確認方法

[修正前PDF](before/schematic.pdf)・[PNG](before/schematic.png)、[修正後PDF](after/schematic.pdf)・[PNG](after/schematic.png)、[RESET周辺](after/reset.png)、[FLAG周辺](after/flags.png)を保存した。比較画像は[RC移動の全体比較](comparison_reset_before_context.png)、[U1近傍](comparison_reset.png)、[FLAG](comparison_flags.png)。before/afterには回路図スナップショット・XMLネットリスト・ERC結果も保存している。

[change_reset_flags.py](change_reset_flags.py)は今回用の局所編集と検証補助スクリプト。既存の生成スクリプトを再実行していない。無引数では基準回路図のバイト一致を要求し、編集後の再適用を拒否する。再出力だけなら`--export-after`を指定する。`export_manifest.json`は出力時の生バイトハッシュで、Gitの改行変換後にはXMLのハッシュが変わる場合がある。

2件とも修正後の確認待ち・未判定。ユーザーの最終判定を待つ。PCB/BOMへの過去の設計変更反映、実機評価、製造承認は今回の作図修正では完了していない。
