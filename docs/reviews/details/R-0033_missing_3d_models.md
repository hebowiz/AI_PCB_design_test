# R-0033 — 3Dモデルの補完

指摘: 2026-11-25 14:28 JST / ユーザー
対象: A-2、22a74e75bdd508a28644a9df42fda8d10793d63e
状態: 確認待ち / 未判定

## 指摘内容

USBコネクタ、ライトアングルピンヘッダ、TVSダイオード等は未実装ではなく3Dモデルがない。メーカー公式から入手できるものを反映し、公式が使えなければ代替手段を検討する。

## 作業範囲

別ブランチcodex/a2-r0033-3d-modelsで3Dモデル参照を補完する。回路・銅箔・配置・DNP設定は維持する。最終判定はユーザーが行う。

## 調査・対応

J1とD1/D5は参照先STEPが存在せず、J2とR17はモデル参照がなかった。TP1/TP2は銅箔パッドのためモデル不要で、C11/C12のDNPは元の設定を維持した。

J1はMolex公式製品ページからSTEP AP242を取得し、端子・位置決めピンを基準に座標変換して反映した。SamtecのJ2公式モデルはメール入力、TIが案内するUltra LibrarianのTVSモデルは登録が必要だったため、いずれも登録せず公式寸法図に基づく独自の簡略STEP/VRMLで補完した。R17はKiCad標準の1608Mモデルを関連付けた。

USB公式モデル本体は公開再配布条件が未確認のためローカル保存とし、Gitには参照・出典・SHA-256・復元手順を記録した。固定Workspaceと既存設計ブランチは変更していない。

## 検証と残課題

58フットプリントを確認し、このPCでは56部品のモデル参照が全件解決した。PCBおよびローカルライブラリ3ファイルはmodel式以外の全トークンが一致し、回路図・設定・カスタムルール・BOM・製造データは不変。ERC・DRC・未配線・回路図整合性は0件で、除外を追加していない。斜視・上面・側面・拡大画像を確認し、初回のUSB上下反転を修正した。

J2は公式図面CQの2.04mm平坦部を既存パッドに合わせると本体後端Y=3.55mmとなり、暫定F.FabのY=1.30mmと2.25mm異なる。モデルを変形して合わせず、メーカー推奨ランドとの照合を残した。簡略モデルの成形細部、寸法公差、実機嵌合・機構干渉は未検証。

修正コミット: `cd67233358d06e299d319934ea59fc6a67662b57`（codex/a2-r0033-3d-models）。最終判定はユーザー待ち。作業時間は約17分。

## 証跡

- [調査・検証レポート](https://github.com/hebowiz/AI_PCB_design_test/blob/cd67233358d06e299d319934ea59fc6a67662b57/01_New_Design/kicad_direct/reports/3d_models/README.md)
- [変更後3D画像](https://github.com/hebowiz/AI_PCB_design_test/blob/cd67233358d06e299d319934ea59fc6a67662b57/01_New_Design/kicad_direct/reports/3d_models/after.png) / [変更前後比較](https://github.com/hebowiz/AI_PCB_design_test/blob/cd67233358d06e299d319934ea59fc6a67662b57/01_New_Design/kicad_direct/reports/3d_models/comparison.png)
- [保全検証](https://github.com/hebowiz/AI_PCB_design_test/blob/cd67233358d06e299d319934ea59fc6a67662b57/01_New_Design/kicad_direct/reports/3d_models/integrity.json) / [DRC](https://github.com/hebowiz/AI_PCB_design_test/blob/cd67233358d06e299d319934ea59fc6a67662b57/01_New_Design/kicad_direct/reports/3d_models/drc.json) / [ERC](https://github.com/hebowiz/AI_PCB_design_test/blob/cd67233358d06e299d319934ea59fc6a67662b57/01_New_Design/kicad_direct/reports/3d_models/erc.json)
- [取得元・モデル種別](https://github.com/hebowiz/AI_PCB_design_test/blob/cd67233358d06e299d319934ea59fc6a67662b57/01_New_Design/kicad_direct/reports/3d_models/sources.json)
