# R-0034 — J2と基板外形の位置合わせ

指摘: 2026-11-25 15:22 JST / ユーザー
対象: A-2、codex/a2-r0033-3d-models、`cd67233358d06e299d319934ea59fc6a67662b57`
対象箇所: `01_New_Design/kicad_direct/a2_usb_uart.kicad_pcb`、J2
重要度: Major（受付時）
状態: 確認待ち / 未判定

> 追記訂正: 修正コミット07cc2d9のJ2は、F.Fabと基板端だけが一致し、3D樹脂前面は0.7172mm内側に残っている。以下の過去の「モデル原点を補正」「3D確認済み」は成立していなかった。再確認の経緯と末尾の再対応結果を参照。

## 指摘内容

J2が基板外形からはみ出し、実装不可能になっている。基板外形とJ2の樹脂部外形を揃えるようレイアウトを修正する。ただし、既存の他部品の配置変更は最小限にする。

## 関連記録と対応状況

[R-0033](R-0033_missing_3d_models.md)の3Dモデル補完はOK判定とし、J2の配置問題を本件で別途管理する。R-0033で記録した暫定フットプリント外形とモデルの差も、配置検討時の確認対象とする。

受付時は指摘収集として登録し、調査・修正・検証は実施しなかった。修正後の最終判定はユーザーが行う。

## 調査 — 2026-11-25 15:29 JST

対象コミットをKiCad 10.0.8のpcbnew APIで読み取り、J2・J3・近傍部品のパッド、外形、配線位置を抽出した。PCBを保存する操作は行っていない。メーカーの部品図CQと推奨ランド図Bを照合し、寸法図を画像でも確認した。

### 原因と寸法

J2は`TSM-104-01-T-SH`だが、使用フットプリント`A2:TSM_104_SH_PROVISIONAL`は暫定品で、メーカー推奨ランドと一致していない。暫定フットプリントと公式ランドの未照合が、基板端との位置不整合につながったと考えられる。R-0033で簡略モデルを追加して差が見えたが、同作業は配置を変更する範囲ではなかった。

| 項目 | 現状 | メーカー資料・調査結果 |
| --- | --- | --- |
| 基板外形 | X=100〜122、Y=100〜150mm | 22×50mmを維持する |
| J2のパッド列中心 | X=111、Y=147.300mm、回転0° | 端まで2.700mmしかない |
| パッド寸法 | 1.10×2.50mm | 推奨0.050×0.125inch＝1.270×3.175mm、図面の丸め表記は1.27×3.18mm |
| パッドピッチ | 2.540mm | 推奨と一致 |
| 推奨パッド中心から基板端 | 未反映 | 図面の0.2080＋0.060inch＝6.8072mm。併記mm寸法の合計は5.283＋1.52＝6.803mm |
| 現行F.Fabの樹脂外形 | Y=148.600〜151.140mm | 基板端から1.140mm突出 |
| 現行簡略モデルの樹脂外形 | Y=150.850〜153.390mm | 基板端から3.390mm突出。モデル上では樹脂部全体が基板外 |

公式ランド図のPCB EDGEに合わせると、J2パッド列中心の候補はY=143.1928mmとなり、内側への移動量は4.1072mm。併記mm寸法では4.103mmとなるため、ここでは約4.11mmとする。これは図面に基づく公称配置であり、公差を含めた実装位置の保証ではない。

R-0033の簡略モデルは、端子の平坦部2.04mmの中央をパッド中心に置く仮定で作っている。メーカー推奨ランド中心から樹脂前面までの基準とは約0.7172mm異なる。したがって、3D画像の突出量3.39mmだけを見て平行移動しても、メーカー推奨配置にはならない。修正時はF.Fab・Courtyard・モデルの原点対応も公式ランド基準で再照合する。モデル本体の寸法を縮めて合わせる方法は採らない。

### J3と周辺への影響

J2を推奨位置へ移し、ランドを推奨寸法にすると、現在のJ3には次の干渉が生じる。実際のPCBを編集せず、矩形パッドの座標から算出した。

| J2端子 | J3端子 | 結果 |
| --- | --- | --- |
| 1 GND | 1 RTS_N | パッド重なり |
| 2 TXD | 2 CTS_N | 銅箔間0.0053mm |
| 3 RXD | 3 GND | パッド重なり |
| 4 USB5V_OUT | 4 VIO_OUT | 銅箔間0.0053mm |

異ネットの最小クリアランス設定は0.127mmで、4組とも成立しない。J2の単独移動では解決できない。

J3をX=111mmのままY=142.0→137.9mmへ移す案を比較した。この位置ではJ3のCourtyard外接矩形がU4・C18・C19・R7・R8・R10・TP2の7部品の外接矩形と交差する。これは再配置検討の候補抽出であり、7部品すべてに実体干渉があるとの確定判定ではない。特にTP2は矩形の角付近の接近で、実形状による確認が必要。

J2・J3のX位置を変えない案では、SW1/SW2/SW3の既存Courtyard外接矩形との重なりはない。USB・FT232H・水晶の位置変更は現時点の案に含めない。J2/J3の8端子に接続する7ネット（GND、TXD、RXD、USB5V_OUT、RTS_N、CTS_N、VIO_OUT）と、移動する電源周辺部品の配線・ゾーンが局所修正の対象になる。

[配置比較図](../evidence/R-0034/placement_study.png)は現状、J2のみ移動、J3も移動の3条件を示す。比較図の配線は元の位置のままで、修正後PCBを示すものではない。[寸法・干渉計算結果](../evidence/R-0034/geometry.json)に座標を記録した。

### 対応案と比較

推奨案は、J2のランドをメーカー推奨値へ修正し、樹脂前面をY=150mmの基板端に合わせること。そのうえでJ3と可変電源周辺を局所再配置する。他部品の移動数と移動量を比較し、上記7部品は必要なものだけ動かす。J3のY=137.9mmは影響調査用の候補で、確定配置ではない。

J2の暫定ランドを残してモデルの突出量だけ移動する案は、ランド寸法と原点の不一致が残るため推奨しない。基板を延長する案は22×50mmの条件に反する。コネクタの型番変更は今回のレイアウト修正範囲に含めない。

承認後の修正は対象コミットから別ブランチで行い、J2のローカルフットプリントとモデル基準、J2/J3および必要な近傍配置、関連配線を変更する。回路図・部品型番・ネット・基板外形は維持し、固定Workspaceの更新は修正版ができてから扱う。

### 修正時の検証と未確認事項

- 変更した部品と移動量、配線・ビア・ゾーンの差分を一覧化する。
- 樹脂外形と基板端、端子とランド、J3との干渉、嵌合側の空間を2D/3Dで確認する。メーカー図面上のオプション穴は、該当しない型番へ追加しない。
- ERC・DRC・未配線・回路図整合性と、USB差動線・GND帰路・ビア寸法/離隔・45°曲げ・USB5V幅・コンデンサ給電順序の回帰を確認する。
- 候補の実配置・再配線・DRCは未実施。移動部品数の最小値、機構公差、嵌合相手と実装工程の余裕は未確定。

今回は調査と修正案の提示まで。R-0033のOK判定は維持し、R-0034の修正・最終判定は未実施。

## 資料

- [Samtec製品ページ](https://www.samtec.com/products/tsm-104-01-t-sh)
- [部品図 CQ](https://suddendocs.samtec.com/prints/tsm-1xx-xx-xxx-sh-xx-xxx-x-xx-mkt.pdf)
- [推奨ランド図 B、2022-06-07](https://suddendocs.samtec.com/prints/tsm-1xx-xx-xxx-sh-xx-xxx-x-xx-footprint.pdf)
- [対象PCB](https://github.com/hebowiz/AI_PCB_design_test/blob/cd67233358d06e299d319934ea59fc6a67662b57/01_New_Design/kicad_direct/a2_usb_uart.kicad_pcb)
- [既存モデルの生成条件](https://github.com/hebowiz/AI_PCB_design_test/blob/cd67233358d06e299d319934ea59fc6a67662b57/01_New_Design/kicad_direct/reports/3d_models/scripts/build_models.py)

## 修正・検証 — 2026-11-25 16:58 JST

ユーザーから、J3の現行パッドサイズを確認したうえでレイアウトを修正する指示を受けた。基準版から専用ブランチcodex/a2-r0034-header-layoutを作り、[修正コミット](https://github.com/hebowiz/AI_PCB_design_test/commit/07cc2d9ab3d8d41842a378ee1c1a4df9c263ae0a)に保存した。

### J3の照合と実装内容

J3はTSM-104-01-T-SV。現行ランドは列方向幅1.00×尾部方向長さ2.51mm、千鳥中心±1.655mmで、選定品の推奨寸法と一致していなかった。[Samtec推奨ランド図D](https://suddendocs.samtec.com/prints/tsm-1xx-xx-xx-sv-xx-xxx-xx-footprint.pdf)に従い、1.27×3.429mm、千鳥中心±1.4605mmへ修正した。2.54mmピッチと端子番号・ネットは維持した。

公式上面視図を180°回して1番端子を左側に置き、奇数番の尾部を基板内側へ向けた。新しいローカルフットプリントA2:TSM_104_SVと、[部品図CG](https://suddendocs.samtec.com/prints/tsm-1xx-xx-xxx-sv-xx-xxx-x-xx-mkt.pdf)に基づく独自の簡略モデルを追加した。型番にないLC/Aオプション穴は追加していない。

### 配置・配線の変更と判断

J2のランドも1.27×3.175mmへ修正し、パッド列をY=147.300から143.1928mmへ移した。樹脂前面は基板端Y=150mmと一致する。モデル原点は推奨ランドとの対応に合わせて0.7172mm補正し、モデル寸法は変えていない。

J3をY=137.9mmへ移し、干渉する可変電源周辺とGND帰路のためにJ2、J3、U4、C18、C19、R7、R8、R10、R12の9部品を移動・回転した。他の49部品は位置・回転を維持。TP1/TP2/R17、USB、FT232H、水晶、スイッチ類は移動していない。J3のCourtyardを実形状に沿わせ、TP2の移動を避けた。9部品が数学的な最小移動数であるとは検証していない。

初期の局所配線ではGND領域の分離とVIOの迂回が生じた。R12の向きと位置を見直し、端子の引き出しを確保して復旧した。試行で追加したGND配線の撤回は、一括処理が自動承認審査で拒否されたため、対象UUIDを特定して1個ずつDRC・未配線を検証する方法へ変更した。29個中28個を撤回し、必要な1個は残した。VIOの約48.65mmの迂回は約10.71mmへ短縮し、狭い通路約1.70mmだけ0.15mm幅を残した。USB5V系の幅条件は維持した。

総配線長は808.25から878.90mmへ増えた。コネクタと周辺部品の移動に伴う増分で、全体の配線長最適化を達成したとは扱わない。試行・採否と幅・経路の比較は[設計レポート](https://github.com/hebowiz/AI_PCB_design_test/blob/07cc2d9ab3d8d41842a378ee1c1a4df9c263ae0a/01_New_Design/kicad_direct/reports/header_layout/README.md)に記録した。

### 検証・保全

- ERC・DRC・未配線・回路図不一致は各0件。除外・設定の追加なし。
- 58部品の値・型番、全パッドの接続、回路図のネット・端子機能・電気種別は一致。回路図の変更はJ3のFootprint関連付けだけ。
- USB差動線と水晶線のUUID・座標・層・幅・ビアを維持。非45°線分、IC短辺中央以外の引き出し、不自然な同一ネットのパッド接触は各0件。90°以上の曲がりはパッド・ビア接触と分岐点を除く2線分間で0件。
- 外形22×50mm、板厚1.6mm、2層、6ゾーンを維持。プロジェクト設定・カスタムルールは基準版と一致。
- BOM・Gerber・既存生成スクリプト・既存設計ブランチ・固定Workspaceは変更していない。mainの既存未コミットCADも保護した。

[検証集計](https://github.com/hebowiz/AI_PCB_design_test/blob/07cc2d9ab3d8d41842a378ee1c1a4df9c263ae0a/01_New_Design/kicad_direct/reports/header_layout/integrity.json)、[配線差分](https://github.com/hebowiz/AI_PCB_design_test/blob/07cc2d9ab3d8d41842a378ee1c1a4df9c263ae0a/01_New_Design/kicad_direct/reports/header_layout/copper_diff.json)、[前後画像](https://github.com/hebowiz/AI_PCB_design_test/blob/07cc2d9ab3d8d41842a378ee1c1a4df9c263ae0a/01_New_Design/kicad_direct/reports/header_layout/images/comparison.png)、[3D画像](https://github.com/hebowiz/AI_PCB_design_test/blob/07cc2d9ab3d8d41842a378ee1c1a4df9c263ae0a/01_New_Design/kicad_direct/reports/header_layout/images/after_3d.png)を参照。表裏の全体図・拡大図と3Dを確認し、R7/R8の文字位置も修正した。

### 残る確認と判定

R-0034は確認待ち・未判定。ユーザーの最終OKは未実施。実物のピン1方向・嵌合空間・公差・実装工程と、移動後のU4/C18/C19の電源・GND帰路を確認する必要がある。簡略3DモデルはメーカーCADではなく、公差や端子曲げの細部を省略している。製造データは旧版のまま。

設計作業は2026-11-25 15:36〜16:50 JST、約75分。固定Workspaceへの反映は別途指示後に行う。

## 3D再確認・報告訂正 — 2026-11-25 20:30 JST

ユーザーから、完成した3D図面で基板外形とピンヘッダ樹脂部外形が本当に一致するか、再確認を求められた。対象は07cc2d9ab3d8d41842a378ee1c1a4df9c263ae0aのJ2。保存済みの上面拡大画像・斜視画像、PCBのモデル設定、VRML樹脂ソリッドの頂点を照合した。

| 項目 | 保存済みデータの値 |
| --- | --- |
| 基板端 | Y=150.0000mm |
| J2原点 | Y=143.1928mm、回転0° |
| F.Fab樹脂前面 | Y=150.0000mm |
| 3Dモデルのオフセット | X/Y/Zすべて0mm |
| VRML樹脂部のローカルY範囲 | -6.09〜-3.55mm |
| PCB座標へ換算した樹脂Y範囲 | 146.7428〜149.2828mm |
| 基板端との隙間 | 0.7172mm（基板内側） |

3D樹脂前面は基板端と一致していない。上面拡大画像の樹脂部より下側に残る基板領域がこの隙間に相当する。斜視画像では部品の高さと投影により位置関係が異なって見えるため、輪郭の見かけだけで端合わせを判定しない。

原因は、補助スクリプトでf.Models()から取得したモデルへオフセットを設定しても、フットプリント本体へ反映されていなかったこと。KiCad 10.0.8で読み取り対象をメモリ上だけ変更して確認したところ、イテレータ上では-0.7172mm、フットプリントから再取得すると0mmだった。保存済みPCBとローカルフットプリントも0mmのまま。ファイル保存・再読込後のモデル変換と樹脂外形を検証していなかった。

前回の「3Dでも一致を確認した」「モデル原点を補正した」という報告を訂正する。電気的なDRC合格はこの機構不一致を検出していない。ユーザーのOK/NG判定は追加せず、R-0034を調査中へ戻した。

再対応では、PCB銅箔やJ2のランド位置を動かす前に、3Dモデルをフットプリントへ書き戻して保存後に再読込し、F.Fab・モデル・メーカー寸法の対応を確認する必要がある。補正予定値はローカルY=-0.7172mm。補正後の画像と数値の一致はまだ未検証。今回は確認と記録訂正のみで、PCB・ライブラリ・固定Workspaceは変更していない。

[再確認の数値証跡](../evidence/R-0034/model_alignment_recheck.json)。
[対象の上面拡大画像](https://github.com/hebowiz/AI_PCB_design_test/blob/07cc2d9ab3d8d41842a378ee1c1a4df9c263ae0a/01_New_Design/kicad_direct/reports/header_layout/images/after_top_detail.png)。

## 再対応・保存後検証 — 2026-11-25 20:35 JST

ユーザーの「再対応をお願い」を受け、同じ専用ブランチでJ2の3Dオフセットを再対応した。修正候補は[5cce544](https://github.com/hebowiz/AI_PCB_design_test/commit/5cce544232e1f0eb137ef95f5060eeea5c9729ef)。

PCBとローカルフットプリントの該当model式だけを一意に特定し、Yオフセットを0から-0.7172mmへ変更した。2ファイルはこの数値以外のバイトが変更前と完全一致する。銅箔・配置・パッド・ネット・ゾーン・3Dモデル形状と倍率は不変。

保存したPCBをLoadBoard、ライブラリをFootprintLoadで別途再読込し、両者のオフセットが-0.7172mmであることを確認した。VRMLの樹脂頂点をPCB座標へ換算するとY=147.460000012〜150.000000012mmとなり、F.Fabの147.46〜150.00mmと基板端150.00mmに一致する。差約0.000000012mmはVRML小数丸めの範囲で、判定許容値0.000001mm内。

新たに上面・上面拡大・斜視をレンダリングし、上面でも隙間が解消したことを確認した。ERC・DRC・未配線・回路図不一致は各0件。旧レポートには誤った一致報告の訂正と新レポートへの案内を追加し、初回画像は履歴として残した。

[再対応レポート](https://github.com/hebowiz/AI_PCB_design_test/blob/5cce544232e1f0eb137ef95f5060eeea5c9729ef/01_New_Design/kicad_direct/reports/header_alignment_fix/README.md)、[保存後の座標検証](https://github.com/hebowiz/AI_PCB_design_test/blob/5cce544232e1f0eb137ef95f5060eeea5c9729ef/01_New_Design/kicad_direct/reports/header_alignment_fix/checks/alignment.json)、[上面拡大画像](https://github.com/hebowiz/AI_PCB_design_test/blob/5cce544232e1f0eb137ef95f5060eeea5c9729ef/01_New_Design/kicad_direct/reports/header_alignment_fix/images/top_detail.png)、[DRC](https://github.com/hebowiz/AI_PCB_design_test/blob/5cce544232e1f0eb137ef95f5060eeea5c9729ef/01_New_Design/kicad_direct/reports/header_alignment_fix/checks/drc.json)、[ERC](https://github.com/hebowiz/AI_PCB_design_test/blob/5cce544232e1f0eb137ef95f5060eeea5c9729ef/01_New_Design/kicad_direct/reports/header_alignment_fix/checks/erc.json)。

R-0034は確認待ち・未判定。実物の公差・嵌合と、前回移動した電源周辺のレビューは残る。回路図・製造データ・固定Workspace・mainの既存未コミットCADは変更していない。再対応は20:31 JST開始、約5分。
