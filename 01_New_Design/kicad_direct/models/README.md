# A-2の3Dモデル

R-0033で不足していたモデルを補完しました。PCBのパッド・ネット・配置・配線・DNP設定は変更していません。

| 対象 | モデル | 種別と制約 |
| --- | --- | --- |
| J1 | vendor/Molex_480372200_aligned.step | Molex公式ページのSTEP AP242。端子面と位置決めピンを基準に座標変換したローカル専用ファイル |
| J2 | TSM_104_01_T_SH_simplified.wrl / .step | Samtec公式寸法図を参照した独自の簡略モデル。メーカー提供CADではない |
| D1/D5 | DPY0002A_simplified.wrl / .step | TI公式DPY0002A寸法図を参照した独自の簡略モデル。メーカー提供CADではない |
| R17 | KiCad標準R_0603_1608Metric.step | インストール済みKiCadライブラリの汎用1608Mモデル |

USBモデルは公開Gitでの再配布条件を確認できていないため、vendor/内にローカル保存しています。Git cloneだけではUSBモデル本体は揃いません。元のZIPはこのPCの`D:/download/196112090-659-480372200.zip`にあります。別のWorktreeへ移すときは、vendor/内の2つのSTEPもコピーし、sources.jsonのSHA-256と照合してください。

再取得は[Molex製品ページ](https://www.molex.com/en-us/products/part-detail/480372200)の「Documents & Resources → 3D Model → STEP AP242」から行います。ZIP内の480372200.stpをvendor/Molex_480372200.stepとして保存し、リポジトリルートからFreeCAD 0.20のPythonで`01_New_Design/kicad_direct/reports/3d_models/scripts/build_models.py`を実行します。生成時に回路図やPCBは読み書きしません。

独自モデルと生成コードにはCC0-1.0を適用します。メーカーのロゴ・刻印・詳細な成形形状は再現していません。メーカー資料やメーカーCADの権利は各権利者に帰属します。KiCadの汎用モデルは[CC-BY-SA 4.0とライブラリ例外](https://www.kicad.org/libraries/license/)に従います。

J2は既存フットプリントが暫定品です。モデルの外形とF.Fabのずれがあるため、3D表示ができることをランド適合の承認とは扱いません。詳しくは[調査・検証結果](../reports/3d_models/README.md)を参照してください。
