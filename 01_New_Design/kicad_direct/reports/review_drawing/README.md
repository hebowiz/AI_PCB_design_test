# R-0009〜R-0013 作図修正

ユーザーの「一括修正を」に基づき、調査で提示した5件を修正した。指示の送信時刻は取得できていない。基準は承認済みの`codex/a2-review-capacitors`、`886ad5428d4be98768ccc8bb942aa2f54f23d942`。独立した設計Worktreeを再利用し、新規ブランチ`codex/a2-review-drawing`で局所編集した。既存版とmainの設計は変更していない。

## 対応結果

| ID | 実施内容 | 確認結果・残課題 |
| --- | --- | --- |
| R-0009 | 12番ピン用に+3V3表示を分離。電源表示→C3の上端分岐→12番ピンの順に描き、C3からGNDへ縦配置。C4も24番ピン側で同じ関係に整理 | 左戻りの給電分岐を解消。C3/C4の定数・接続・対応ピンを維持 |
| R-0010 | USB5V→C1分岐→C23分岐→40番ピンの順へ配線を整理。C1/C23を水平電源線からGNDへ縦配置 | コンデンサを並列のまま維持。C23をICへの引込み側に配置 |
| R-0011 | #FLG07を+3V3の水平線上へ移動し、折れ曲がりから離した | FLAG自身の縦線と配線の重なりを解消。接続点とERC上の電源宣言を維持 |
| R-0012 | USBの上側経路・右側折返し、水晶の折返し列の内外を整理 | 水晶2→0交差、USB3→1交差。USBのJ1近傍1か所は非接続交差として残す。D1/D5/J1の配置・属性は維持 |
| R-0013 | U4周辺、帰還抵抗・SW1、出力SW3、手動5VのSW2を寄せ、注記・電源/GND/FLAGの位置を整理 | 電源・GND・FLAGを含む部品中心位置の広がりを横264.16→167.64mm、縦146.05→87.63mmへ縮小。文字と配線の重なりを拡大図で調整 |

R-0013の数値は図面上の中心位置の範囲であり、文字・図形の外形を含む占有面積やPCB寸法ではない。横方向は約36.5%、縦方向は40%の縮小。用紙は単一A2のまま。周囲のUART、EEPROM、LED、電源制御ブロックを不要に移動していない。

USBの残る交差はJ1からの短い引出し部分にある。交差点に接続点を追加しておらず、D+/D−の端子対応も維持する。交差0を目的としたコネクタ・ESD部品の再配置や大きな迂回は今回行っていない。UARTの意図した非接続クロスも維持した。

## 電気的同一性と保護対象

[verification.json](verification.json)の11項目と、[drawing_audit.json](drawing_audit.json)の12項目はすべて合格した。55実部品、193端子、54ネットが変更前後で一致する。部品番号、値、型番、フットプリント、その他の属性、DNP・BOM設定、既存シンボルUUID、埋込みシンボル定義を維持した。追加したのは同じ+3V3ネットを示す電源記号#PWR0177だけである。

KiCad XMLネットリストについて、部品・ライブラリ部品・ネットごとの端子属性を正規化して比較し、一致を確認した。出力日時、出力元パス、ネットコードや列挙順のような生成差分は比較対象から外し、ネット名と各端子の対応・ピン機能・電気種別を比較した。[変更前](canonical_netlist_before.json)と[変更後](canonical_netlist_after.json)を保存している。

ERCは変更前後ともエラー0件、警告0件。single_global_label、four_way_junction、simulation_model_issue、footprint_filterの既存無視設定を維持し、新規の除外は加えていない。PCB未変更のためDRCは再実行していない。

基準コミットのA-2に存在する529ファイル中、変更した既存ファイルは回路図1個だけ。PCB、BOM、Gerber、ライブラリ、既存生成スクリプト、過去のレポートを含む528ファイルは不変である。今回用スクリプトは本フォルダに追加し、既存の全体生成スクリプトを実行していない。

## 図面確認

初回出力後、C1/C23の対応注記が水晶の説明文へ近づいていたため位置を調整した。SW1の定数とFB_3V3ラベルの接近も解消し、さらにラベルが隣のFB_2V5の縦線に重ならないよう左寄せから右寄せに変更した。SW3は2回目の配置でVIO出力へさらに寄せた。

修正後のPDF・PNGは計3回出力した。全体図、電源ピン、FLAG、USB/水晶ペア、電源ブロックを拡大して確認した。小さく表示すると細線が見えにくいことがあるため、FLAGの水平配線は専用の拡大画像でも確認した。部品の近接配置と回路図の短い線分を、PCB配線長や実装品質の保証とは扱わない。

## 成果物

[修正前PDF](before/schematic.pdf)、[修正後PDF](after/schematic.pdf)、[修正前PNG](before/schematic.png)、[修正後PNG](after/schematic.png)、[全体確認画像](after/overview.png)。比較画像は[電源ピン](comparison_power_pins.png)、[FLAG](comparison_flag.png)、[ペア配線](comparison_pairs.png)、[電源ブロック](comparison_power_block.png)。各版の拡大図、XMLネットリスト、ERC JSON、回路図スナップショットもbefore/afterに保存した。

[export_manifest.json](export_manifest.json)は出力時の生バイトに対するSHA-256。[commands.json](commands.json)にはKiCad CLIとpdftoppmの実行コマンド・終了コード・標準出力を記録した。Gitの改行変換後にはXMLの生バイトハッシュが変わる場合がある。

[change_drawing.py](change_drawing.py)は今回用の局所編集・出力・検証スクリプト。無引数では基準回路図とのバイト一致を要求し、編集済みの回路図へ重ねて適用できない。再出力と再検証は次のコマンドを使う。

```powershell
& "$env:LOCALAPPDATA/Programs/KiCad/10.0/bin/python.exe" 01_New_Design/kicad_direct/reports/review_drawing/change_drawing.py --export-after
& "$env:LOCALAPPDATA/Programs/KiCad/10.0/bin/python.exe" 01_New_Design/kicad_direct/reports/review_drawing/audit_drawing.py
```

## 作業ログと状態

2026-11-22 20:30:16 JSTにブランチ作成時刻を記録。AGENTSと共通レビュー運用を確認し、基準版の座標を調査して編集した。20:32に初回出力、20:34に注記とSW3配置を調整、20:36に帰還ラベルの位置を調整して最終ERC・接続比較を完了した。20:37までに全体と拡大図の最終確認、座標監査とハッシュ照合を完了。ここまで約7分で、文書化・台帳反映・コミット・pushの時間はmain作業ログへ記録する。

環境はWindows、PowerShell 7.6、KiCad 10.0.8、同梱Python 3.11.5、Poppler 26.07.0。KiCadコマンドは全回正常終了した。日本語本文はyomiyasuで最終推敲した。

5件とも修正・検証後の確認待ちで、最終判定は未判定。従来のR-0001〜R-0008のOK判定は維持する。PCB/BOMの既存未反映事項、実機評価、製造承認は今回の作図修正では完了していない。
