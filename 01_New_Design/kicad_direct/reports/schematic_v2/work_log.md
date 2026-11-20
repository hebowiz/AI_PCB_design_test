# A-2 回路図V2 作業ログ

## 2026-11-20 19:24 JST — 開始と基準の保存

AGENTS.mdを確認し、origin/mainをfetchした。最新コミットから独立Worktreeとexperiment/A2-schematic-v2を作成した。mainの回路図はV0と同一で、V1の変更は取り込まれていない。V0を保存し、V1の回路図・画像・検証結果・時間記録を比較用に読み取り専用の資料として複製した。V2の編集入力はV0だけとする。記録は指定されたreports/schematic_v2/へ集約する。

開始時刻は2026-11-20 19:24:02 JST。Windows、PowerShell 7.6、KiCad 10.0.8と同梱Pythonを使用する。yomiyasuのdomains/tech.mdはルートに存在しなかったため、関連ファイルの所在を再確認する。


## 2026-11-20 19:25–19:29 JST — V0保存と初回作図

V0回路図を保存し、KiCad CLIでXML、ERC、白黒PDFを出力した。pdftoppmで4200 × 2970のPNGへ変換した。V0のERCは0件。V1の固定コミットから回路図、PDF、PNG、ネットリスト、ERC、作業ログを比較用フォルダへ保存した。AGENTS.mdの共通ログ指示に対し、今回の明示された変更範囲と保存場所を優先し、共通docs/は変更しない。

V0シンボルを解析し、端子位置・ネットを読み取って新規のlayout_v2.pyを作成した。V1の編集結果は入力に使わず、50 mil単位で配置を組み直した。既存sexpr.pyを読書き補助としてインポートした。作図の判断は比較レポートに記録した。

初回のCLI出力は読み込みエラーになった。フィールド揃えに非対応のcenterキーワードを指定したことが原因で、省略による中央揃えに直した。再出力ではERC警告1件を検出した。交差後のRXD配線にRTS名を置いていたため、ラベルを正しい配線へ移した。実線化でラベルがなくなった局所ネットは自動名へ変わっていたので、元の名前を識別ラベルとして残した。途中成果物は最終結果として扱っていない。

## 2026-11-20 19:30–19:33 JST — 第1・第2回の画像確認

PDFを5600ピクセル幅で描画し、全体とUSB・発振、UART、VIO、EEPROM、出力電源を拡大した。D1の値と本体、U1内部電源線と他ピンのラベル、PWREN_NとC17のGND、J2の電源名と信号線、SW3と図枠の重なりを修正した。下側の電源回路を8グリッド上へ移し、注記も図枠内に収めた。初回拡大画像とERC/XMLをiterations/01_*に保存した。

第2回の画像確認では、LEDの値の揃え方、REF12Kの名前と水晶GND線の近接を修正した。R11はVIOを上側へそろえ、抵抗の下端からRXDへの接続を折り返す形にした。初期検討中のR12上下配線も、抵抗を迂回して短絡しない経路へ直している。第2回画像はiterations/02_*に保存した。修正後のERCは0件、出力日時以外のXML全体がV0と一致した。

## 2026-11-20 19:34–19:40 JST — 最終検証と比較資料

verify_v2.pyでV0/V1/V2の属性・ライブラリ・ネットを比較した。V0/V2はdesign/dateだけを除く全XMLが一致した。62シンボルの属性とUUID、埋込み定義を保持し、58部品・58ネット・207端子が一致した。ERCは前後0件。V1のERCは保存済みの0件を参照し、今回の再実行とは区別した。

既存A-2の107ファイルをGit blobで比較し、対象回路図以外の変更は0件だった。他ディレクトリに追跡済みファイルの変更もなかった。部品番号・定数・型番・フットプリント、PCB、BOM、製造データ、ライブラリ、元の生成スクリプトは変更していない。

verify_v2.pyでは35組の端子対について、ネットラベルを使わず配線だけで追えるかも調べた。V0/V1/V2で0/14/32組だった。これを理解度の点数や全回路の網羅率とは扱わず、端子対の一覧と残ったラベル接続を保存した。

最終の局所図で固定LDOの電源フラグとUSB5V名の近接が残っていたため、ラベルだけを線上で移動した。export_v2.pyでXML/ERC/PDF/PNGを出し直し、全コマンドの終了コード0と空のstderr、入力・出力SHA256を保存した。再比較は合格した。最終の拡大図で文字位置を確認した。

比較文書を保存するツール呼出しでJavaScriptの文字列記号を誤り、構文エラーが1回出た。その呼出しは実行されずファイル変更はなかった。文字列を修正して再実行した。

## 主なコマンドと実行方法

~~~powershell
git fetch origin main
git switch -c experiment/A2-schematic-v2 origin/main
kicad-cli sch export netlist --format kicadxml -o reports/schematic_v2/before/netlist.xml a2_usb_uart.kicad_sch
kicad-cli sch erc --format json --exit-code-violations -o reports/schematic_v2/before/erc.json a2_usb_uart.kicad_sch
kicad-cli sch export pdf --black-and-white -o reports/schematic_v2/before/schematic.pdf a2_usb_uart.kicad_sch
python reports/schematic_v2/layout_v2.py --apply
python reports/schematic_v2/export_v2.py
python reports/schematic_v2/verify_v2.py
python reports/schematic_v2/render_details.py
~~~

実際の実行ではKiCad同梱PythonとCLIを絶対パスで指定した。設計ファイルと出力先には、リポジトリルートからA-2までのパスを付けた。最終出力の完全な引数・日時・結果はexport_log.jsonに保存した。独立WorktreeはCodexのcreate_worktreeで作成し、場所はC:/Users/hebow/.codex/worktrees/a2-schematic-v2/99_AI_PCB_design_test。作業開始時のorigin/mainは77f0fd37e0d04b10f6831f88b8f035a009238701だった。

日本語文書はyomiyasuで最終推敲し、同梱リンターで確認した。初回に見つからなかったtech.mdはreferences/domains/tech.mdで確認した。数値、型番、コマンド、実行ログの文体は変更しない。

残課題は単一シート縮小時の細字、USBの迂回、UART交差、U1電源ピンへのラベル接続、人間による読解評価。元の電気・機構の未検証事項は継続して残る。ユーザーの設計レビュー・承認は受けていない。

## 2026-11-20 19:41 JST — 成果物完成

最終の日本語レポートと作業ログはyomiyasuの観点で推敲し、リンターの指摘は0件だった。4本の補助スクリプトの構文検査に合格した。V1比較資料は参照元コミットとバイト単位で一致した。図面座標メタデータは下側回路の移動後の値へ揃えた。成果物完成までの経過は17分14秒。コミット・pushの時間は別途記録する。

## 2026-11-20 19:43 JST — コミットとpushの検証

生成物のバイト列をGitでも保持するため、比較資料の改行変換を無効にした。空白検査がJSON、次いでハッシュTXTのCRLFを指摘したため、ファイルを変換せず、CRを行末として扱う属性を追加した。2回の指摘を解消し、git diff --cached --checkは合格した。

設計と資料を2538acc5acb3925dacd2563b000af9ca855604ccへコミットし、git push --set-upstream origin HEAD:refs/heads/experiment/A2-schematic-v2が成功した。push後にコミット内のSHA256も確認したところ、先にステージしたERC JSONがLFのまま格納されていることを検出した。回路図と検査結果の内容に変更はないが、証跡のバイト列を一致させるため、A-2の新規報告フォルダだけにgit add --renormalizeを適用した。

修正した証跡をd4db6f6c6a81693623fd654aac36ed763a08ac7fへコミット・pushした。インデックスとコミット内のXML/ERC/PDF/PNG、およびV1参照資料のハッシュは全件一致した。git ls-remoteで専用ブランチとHEADが一致した。リモートmainは77f0fd37e0d04b10f6831f88b8f035a009238701、V1はbeba27eed1f1c2a94be86ccc24ce8ffe5ae3d5e6のまま。作業ツリーはクリーンだった。この記録を追加コミットして同じ専用ブランチへpushする。mainへはマージしていない。
