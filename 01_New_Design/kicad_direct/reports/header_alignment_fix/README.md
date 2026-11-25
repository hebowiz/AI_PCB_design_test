# R-0034 — J2の3D端合わせ再対応

基準: 07cc2d9ab3d8d41842a378ee1c1a4df9c263ae0a。専用ブランチcodex/a2-r0034-header-layout。ユーザーの再対応指示に基づく修正候補で、最終判定は未実施。

## 変更内容と原因

前回はF.Fabだけが基板端と一致し、3D樹脂前面は0.7172mm内側に残っていた。pcbnewのf.Models()から取得したモデルに値を設定しても、フットプリントへ書き戻されていなかった。前回の「3Dでも一致」という報告を訂正する。

今回はPCBとローカルフットプリントのJ2モデルオフセットを、(0,0,0)から(0,-0.7172,0)mmへ直接変更した。対象のmodel式を一意に特定し、その他のバイトが不変であることを検査した。配置・配線・パッド・ネット・ゾーン・モデルの形状と倍率は変更していない。既存生成スクリプトを再実行していない。

## 保存後の検証

| 項目 | 結果 |
| --- | --- |
| PCBとライブラリの再読込値 | モデルYオフセット=-0.7172mm |
| 樹脂部のPCB座標 | Y=147.460000012〜150.000000012mm |
| F.Fab外形 | Y=147.4600〜150.0000mm |
| 基板端 | Y=150.0000mm |
| 差 | 約0.000000012mm。VRML小数表記の丸め範囲、判定許容値0.000001mm内 |
| ERC | 0件 |
| DRC・未配線・回路図不一致 | 各0件 |
| 電気・配置データ | 3Dオフセット以外のファイル内容が完全一致 |
| 保護対象 | 回路図、プロジェクト設定、ルール、製造データ、既存生成スクリプト、固定Workspaceは変更なし |

数値は[alignment.json](checks/alignment.json)、検査結果は[DRC](checks/drc.json)・[ERC](checks/erc.json)。保存したPCBを別プロセスのKiCad CLIでレンダリングし、[上面](images/top.png)・[上面拡大](images/top_detail.png)・[斜視](images/oblique.png)を目視した。上面で樹脂前面と基板端の一致を確認した。斜視では高さによる投影差があるため、画像輪郭だけで一致を判定していない。

## 作業ログ

2026-11-25 20:31 JST開始。2026-11-25 20:33 JST記録。KiCad 10.0.8 / Windows / Pythonを使用。
操作はscripts/fix_alignment.py、kicad-cli pcb render --side top --quality high、pcb render --rotate 30,0,0、pcb drc --schematic-parity --severity-all --format json、sch erc --severity-all --format json。出力ログをchecks/に保存した。画像の切り出しはPillowを使用。初回ヘルプ表示は権限制限でレジストリ警告を出したが、承認されたCLI実行で検証・出力は完了した。

修正スクリプトは基準版一致を前提とし、完成版へ再実行すると保護用assertで停止する。最終確認は保存後にLoadBoard/FootprintLoadで再読込して行った。日本語記録はdesign-review-recordsとyomiyasuの方針で整理した。

## 残る確認

R-0034の人間レビューは未実施。簡略モデルの公称寸法での一致であり、実物の公差・嵌合相手・実装工程は未検証。前回変更した電源周辺のレビューも継続する。固定Workspaceは更新していない。
