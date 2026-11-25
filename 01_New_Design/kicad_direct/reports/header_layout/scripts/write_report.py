from pathlib import Path
import json,datetime
r=Path.cwd();out=r/'01_New_Design/kicad_direct/reports/header_layout';x=json.loads((out/'integrity.json').read_text());now=datetime.datetime.now().astimezone().strftime('%Y-%m-%d %H:%M JST')
body='''# R-0034 — J2/J3のランド照合と局所配置修正

基準は`cd67233358d06e299d319934ea59fc6a67662b57`。専用ブランチ`codex/a2-r0034-header-layout`の修正候補で、ユーザーの最終判定は未実施。

## 調査結果と採用寸法

J2だけを内側へ動かすとJ3と干渉するため、両コネクタのランドをメーカー図面で確認した。J3の現行ランドは選定品の推奨寸法・端子配置と一致せず、そのまま採用する根拠が不足していた。

| 項目 | 修正前 | 修正後・根拠 |
| --- | --- | --- |
| J2、TSM-104-01-T-SH | 1.10×2.50mmランド | 推奨図Bの0.050×0.125inch＝1.27×3.175mm |
| J2パッド列中心Y | 147.300mm | 143.1928mm。0.2080＋0.060inch＝6.8072mmを基板端から確保 |
| J2樹脂外形Y | モデル150.85〜153.39mm | 147.46〜150.00mm。基板端Y=150mmと樹脂前面を一致 |
| J3、TSM-104-01-T-SV | 列方向幅1.00×尾部方向長さ2.51mm | 推奨図Dの0.050×0.135inch＝1.27×3.429mm |
| J3千鳥中心 | ±1.655mm | ±1.4605mm。外側ランド端の距離0.250inch＝6.35mmから算出 |
| J3中心Y | 142.0mm | 137.9mm。ピッチ2.54mm、ピン番号・接続は維持 |

J2の簡略モデルは平坦部中央をランド中心に置いていたため、モデル原点を公式の推奨ランド基準へ0.7172mm補正した。モデルの寸法を縮めて合わせてはいない。J3はメーカーの上面視図を180°回した向きで1番端子を左側に置き、奇数番の尾部を基板内側へ向けた。汎用モデルでは表現が一致しないため、公式寸法に基づく独自の簡略STEP/VRMLを追加した。LC/Aオプションのない型番なので、オプション穴・切り欠きは追加していない。

J3のフットプリント関連付けだけを`A2:TSM_104_SV`へ変更した。回路図の接続・値・型番・ピン機能は変更していない。既存の汎用ランドに関するNote属性は履歴保全のため残しており、今回の選定根拠は本書と新しいライブラリの説明を参照する。

## 配置・配線の変更

移動・回転した実部品はJ2、J3、U4、C18、C19、R7、R8、R10、R12の9個。49個は位置・回転を維持した。TP1/TP2/R17、USBコネクタ、FT232H、水晶、SW1/SW2/SW3は移動していない。座標は[integrity.json](integrity.json)、撤去・追加・編集した銅箔のUUIDは[copper_diff.json](copper_diff.json)に記録した。

J3との干渉を避けるため可変電源周辺を左側へ移し、U2のGND帰路を確保するためR12を横向きで下側へ移した。J3のCourtyardは樹脂部と各ランドの外周に0.25mmを加えた形状とし、外接矩形だけでは接触候補だったTP2を移動せずに収めた。9個が移動数の数学的最小値であるとは検証していない。

既存銅箔をできるだけ残して局所接続を復旧した後、仮配線の迂回と重複を見直した。VIOの約48.65mmの迂回は約10.71mmへ短縮。狭い通路は既存VIO分岐と同じ0.15mmを使用し、余裕のある部分を0.20〜0.30mmへ拡幅した。0.15mm区間は約1.70mmで、USB5V配線ではない。幅の試行と結果は[vio_widths.json](vio_widths.json)に残した。

試行で追加したGND補修29アイテムは、1個ずつ撤去して全DRC・未配線0件を維持できるものだけを採用し、28個を撤回した。結果は[ground_prune_validation.json](ground_prune_validation.json)。一括撤去案は自動承認審査で接続喪失リスクを理由に拒否されたため、この逐次検証方式へ変更した。原版GNDの一括削除は行っていない。

総配線長は808.25→878.90mm。変更部品とコネクタへの経路変更で増えており、全基板の配線長最適化を達成したとは扱わない。[ネット別比較](net_lengths.json)に増減を示す。全面再配線は行っていない。

## 検証

| 検査 | 結果・証跡 |
| --- | --- |
| ERC | 0件。[final_erc.json](checks/final_erc.json) |
| DRC / 未配線 / 回路図との不一致 | 0 / 0 / 0件。[final_drc.json](checks/final_drc.json) |
| 回路図のネット、端子番号・機能・電気種別 | 前後一致。部品属性差分はJ3のFootprintのみ（通常欄と重複するfields欄） |
| PCBの実部品・端子接続 | 58フットプリント、値・型番などの属性、全パッドのネット一致 |
| USB差動線・水晶線 | UUID、座標、層、幅、ビアを維持 |
| 外形・構成 | X100〜122、Y100〜150mm、22×50mm、1.6mm、2層。6ゾーンを保持し再フィル |
| 非45°線分 | 0件。[non45_segments.json](non45_segments.json) |
| IC短辺中央以外の引き出し / 同一ネットの不自然なパッド接触 | 0 / 0件。[escape_audit.json](escape_audit.json)、[grazing_pad_contacts.json](grazing_pad_contacts.json) |
| 90°以上の曲がり | パッド・ビア接触および分岐点を除く2線分の曲がりは0件。分岐点の角度は別扱い。[all_turns.json](all_turns.json) |
| プロジェクト・カスタムルール | `.kicad_pro`と`.kicad_dru`は基準とSHA-256一致。除外・設定の追加なし |
| 保護対象 | 回路の電気的内容、BOM、Gerber、既存生成スクリプトは変更なし。mainのCAD・既存設計ブランチ・固定Workspaceは更新していない |

[検証集計](integrity.json)と前後ネットリスト[before.net](checks/before.net) / [after.net](checks/after.net)を保存した。途中のDRCファイルには試行時の不合格も残している。最終結果は`final_*`を参照する。

## 図面確認

- [前後の表面比較](images/comparison.png)
- [表面配線](images/front.png) / [裏面配線（裏面視）](images/back.png)
- [表面の拡大](images/front_detail.png) / [裏面の拡大](images/back_detail.png)
- [3D斜視](images/after_3d.png) / [上面](images/after_top.png) / [コネクタ付近の拡大](images/after_top_detail.png)

KiCadの全体図・拡大図・3Dを複数回確認した。J2樹脂部の端合わせ、J3の千鳥ランドと端子、近隣部品の実装領域を確認し、R7/R8の文字位置も修正した。J2/J3の簡略モデルはメーカーCADではなく、公差・はんだ・端子曲げの細部を省略している。

## 残る確認事項

ユーザーによるR-0034最終判定、実物のピン1方向と嵌合相手の空間、公差・リフロー条件・実装治具の確認は未実施。U4/C18/C19の移動後の電源・GND帰路と配線長増分は、PCBレビューでも確認する。DRC合格だけで電源特性や製造性を保証しない。製造データは旧版のまま。

固定Workspaceは更新していない。今回の候補は専用ブランチでレビューし、固定フォルダへの反映は別途指示後に行う。

## 作業経緯と再現時の注意

KiCad 10.0.8、Windows、pcbnew API/CLI、Python、FreeCAD 0.20を使用。`before/`に基準CADを複製し、`candidate/`で配置と局所配線を試行した。既存の設計生成スクリプトは再実行していない。補助スクリプトは[scripts/](scripts/)に保存したが、試行順序に依存するものを含み、一括再実行用ではない。既存UUIDを保護するため、完成版へ再実行しないこと。基準CADはGitの上記コミットから復元できる。

初期の経路選択ではポートの閉塞、GND領域の分離、短い段差や重複が発生した。全端子の引き出しを先に確保し、R12の向き・配置を見直して復旧した。SOT-23の移動で生じた斜め引き出しは短辺中央へ戻した。KiCad APIのフィールド型、SWIGオブジェクト保持、ビア幅の層指定、ネットリストのFootprint重複出力を確認して検査を修正した。SDKの終了時に表示されたSWIG所有権警告と、権限制限下のCLI設定読み取り警告は作業ログに記録し、別プロセスで再読込・最終検証した。

作業記録: 2026-11-25 15:36 JSTから開始。最終記録日時と所要時間は下記。

## メーカー資料

- [J2 製品ページ](https://www.samtec.com/products/tsm-104-01-t-sh)、[推奨ランド図B](https://suddendocs.samtec.com/prints/tsm-1xx-xx-xxx-sh-xx-xxx-x-xx-footprint.pdf)、[部品図CQ](https://suddendocs.samtec.com/prints/tsm-1xx-xx-xxx-sh-xx-xxx-x-xx-mkt.pdf)
- [J3 製品ページ](https://www.samtec.com/products/tsm-104-01-t-sv)、[推奨ランド図D](https://suddendocs.samtec.com/prints/tsm-1xx-xx-xx-sv-xx-xxx-xx-footprint.pdf)、[部品図CG](https://suddendocs.samtec.com/prints/tsm-1xx-xx-xxx-sv-xx-xxx-x-xx-mkt.pdf)

メーカーPDFは確認用にローカル保存し、公開リポジトリには転載していない。レポート内のPDF/PNGは今回の設計から生成した図面。
'''
elapsed=round((datetime.datetime.now()-datetime.datetime(2026,11,25,15,36)).total_seconds()/60)
body+=f'\n最終記録: {now}。経過時間: 約{elapsed}分。\n'
(out/'README.md').write_text(body,encoding='utf-8')
with (r/'docs/work_log.md').open('a',encoding='utf-8') as f:f.write(f'''\n## {now} — R-0034 J2/J3ランド・配置修正候補\n\nJ3の現行パッドも確認するユーザー指示に基づき、基準cd672333から`codex/a2-r0034-header-layout`を作成。SamtecのSH/SV推奨ランドと部品図を照合し、J2/J3と電源周辺の9部品を局所再配置した。回路図はJ3 Footprintだけ変更。全58部品の属性・端子ネット、USB/水晶経路、22×50×1.6mm/2層を保護。BOM/Gerber・既存生成スクリプト・固定Workspaceを更新していない。\n\n操作: KiCad 10.0.8 pcbnew API、`kicad-cli sch export netlist`、`sch erc`、`pcb drc --schematic-parity --severity-all`、`pcb export pdf`、`pcb render`、FreeCAD/Pythonによる簡略モデル作成、pypdfium2/Pillowによる図面確認。ERC/DRC/未配線/回路図不一致0件、非45°線分0件、IC非中心引き出し0件。GND補修の一括撤回は自動審査で拒否されたため、限定UUIDを1個ずつDRC検証して28個を撤回。VIO迂回を約49→11mmへ短縮。試行・APIエラーと修正の経緯、変更ファイルと検証証跡は[レポート](../01_New_Design/kicad_direct/reports/header_layout/README.md)。経過約{elapsed}分。\n\n設計レビュー・機構公差・実装条件・電源実測は未確認。共通台帳の最終判定はユーザーが行う。design-workspace-management/design-review-recordsの運用、yomiyasuの日本語最終校正を適用。\n''')
# Add model provenance without altering pre-existing model records.
with (r/'01_New_Design/kicad_direct/models/README.md').open('a',encoding='utf-8') as f:f.write('''\n## R-0034：J3の専用簡略モデル\n\n`TSM_104_01_T_SV_simplified.step/.wrl`はSamtecのSV部品図CG・推奨ランド図Dから独自に作成した簡略形状。メーカーCADではない。J3の1番端子を左、奇数番の尾部を基板内側へ向ける配置に対応する。生成スクリプトと寸法根拠は[header_layout](../reports/header_layout/README.md)を参照。J2は既存モデル形状を維持し、PCB/フットプリント側のモデルオフセットで公式ランド基準へ合わせた。\n''')
print(now,elapsed)
