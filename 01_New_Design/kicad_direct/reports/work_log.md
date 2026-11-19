# A-2作業記録

## 2026-11-19 21:21 JST — 共通仕様と実行環境の確認

目的は、他方式の成果物を使わずにKiCadだけで新規基板を設計すること。

`AGENTS.md`、共通README、`docs/setup_plan.md`、`docs/environment.md`を読んだ。開始時のHEADは`2cd3d58dd13a327891194056e9fca69de9172ef3`、作業ツリーに変更はなかった。チェックアウト内の共通仕様フォルダは空だったが、`git worktree list --porcelain`で確認した元の作業フォルダに未コミットの`01_New_Design/specs/design_input.md`があった。これを読み、`reports/design_input_snapshot.md`へ複製した。SHA256は`AC9853C17769796FF49D9DF7332F76452FC38ABAA7928B77D9B8BF093D6F8DBE`。他方式の成果物は参照していない。

`git ls-remote --heads origin`で、リモートには同じHEADのmainのみ存在することを確認した。ネットワーク制限下の初回実行は接続に失敗し、権限付き再実行で成功した。`git switch -c experiment/A-2`は共有Git管理領域への書き込み権限が必要だったため、権限付きで再実行し成功した。mainへの変更・pushはしていない。

KiCad CLIは10.0.8、同梱Pythonは3.11.5、`import pcbnew; pcbnew.GetBuildVersion()`は10.0.8を返した。CLIの版確認ではサンドボックスによるHKCUレジストリアクセス拒否も表示された。回路図の生成・ERC・PCB保存はこの時点では未検証。

今回の明示指示に従い、作業記録・判断記録も`01_New_Design/kicad_direct/reports/`に保存する。共通`docs/`は変更しない。atopileおよびA-1用pcb-pipelineスキルは使用しない。

実行した主なコマンドは`git status --short`、`git branch -a`、`git ls-tree -r main -- 01_New_Design/specs`、`git ls-remote --heads origin`、`git worktree list --porcelain`、`git switch -c experiment/A-2`、`kicad-cli version`。Python実行時はKiCad同梱の実行ファイルを指定した。

変更ファイルは共通仕様の写し、本記録、`scripts/sexpr.py`。後者はKiCadのS式を読み書きする補助コードで、他方式からの転用ではない。

## 2026-11-19 21:22–21:39 JST — 回路生成、配置、初期配線

目的は4信号UART基板をKiCadのネイティブ形式で作ること。メーカー資料とインストール済みKiCadライブラリを確認し、`scripts/design.py`へ部品・ネット・配置を定義した。`generate.py`で回路図、基板、ローカルライブラリ、プロジェクト設定を生成した。ネット名はXML出力と一致する`/`付きへ揃えた。EEPROM、PWREN#制御、USB外部電源開閉、FB切替、LED電流制限を追加した。

初期ERCではシンボル継承、ピンの電気種別、電源駆動などの問題が出た。シンボルを展開し、電源供給の宣言と実際のピン種別を修正して0件にした。誤った型のまま違反を除外する処理は行っていない。初期結果は`erc_initial.json`、修正後は`erc.json`。

配置DRCでは部品の領域、USB固定穴、狭いピン周辺の制約が問題になった。自分が生成した配置だけを複数回調整した。`drc_placement*.json`に各段階を保存した。最終配置では電気・機構のDRCエラーを解消し、シルクの90件が残った。

`route.py`で両面のグリッド探索を行った。NumPyとpcbnewを使用し、グリッド0.05 mm、配線幅0.15 mm、ビア0.55/0.25 mm、探索側クリアランス0.137 mmとした。GNDを両面ゾーンへ接続し、信号を順次配線した。KiCad 10のビア径取得には層引数が必要で、`GetWidth(F_Cu)`へ修正した。

初期配線後に残った5接続は、FT232HのVPHY・REF12K・CTSと固定LDOのUSB5V接続だった。`repair_routes.py`でUSB5Vの2接続を追加できた。残る3接続は先に通したXTAL_INやTXDがパッドの出口を塞いでいたため、対象ネットだけを外して順番を変更した。途中結果は`drc_routed1.json`〜`drc_routed3.json`、探索結果は`routing*.json`、失敗時の出力は`routing_cage_repairs_console.txt`に記録した。

この段階ではUSBの差動配線、製造出力、実機性能は未検証だった。変更はA-2内のCAD、ライブラリ、スクリプト、レポートのみ。

## 2026-11-19 21:40–21:46 JST — 配線修正、1.6 mm反映、整合確認

`resolve_cages.py`の読込み順でSWIGオブジェクトを列挙できないエラーが出た。pcbnewの先行読込みと重複した基板読込みを避け、ルータ側で一度だけ読み込む形へ修正した。REF12Kを先に接続し、VPHY、XTAL_INを順に復旧した。6経路の探索が成功し、未配線は0件になった。

ユーザーから板厚1.6 mmへの変更指示を受け、生成コードと保存済みPCBの両方へ反映した。USBコネクタのBOM注記も更新した。`finalize.py`でMPN/Noteと未接続端子ネットを回路図に揃え、GNDゾーンを再充填した。

メタデータ反映の初回は存在しない`GetFieldByName`を呼び失敗したため、`GetField`へ修正した。ネットリストも既定のS式ではXMLとして読めなかったため、`sch export netlist --format kicadxml`で再出力した。未接続端子名に含まれる`/`はKiCadの`{slash}`表記へ変換した。ゾーン再充填前に出た183件の違反のうち、銅箔に関するものは古い充填結果と新規配線との重なりだった。再充填後はシルク90件だけになった。

`silkscreen.py`で標準シルク輪郭をF.Fabへ移し、リファレンスを配置した。探索半径5 mmではR14を配置できず、20 mmまで広げて完了した。小型文字の一部は部品から離れるため、F.Fabと座標を使った組立確認を残件とした。裏面説明は`back_legend.py`で追加した。

`pcb drc --format json --schematic-parity --exit-code-violations`と`sch erc --format json --exit-code-violations`で、警告・エラー・未配線・不一致がすべて0件になった。`drc_final.json`と`erc_final.json`が最終証跡。

## 2026-11-19 21:47–21:53 JST — 出力、目視確認、記録

`scripts/export.ps1`でERC/DRC、XMLネットリスト、回路図PDF/SVG、Gerber、PTH/NPTHドリル、穴図、実装座標、PCB各層PDFを出力した。BOMも製造レビュー用フォルダへ複製した。各コマンドの終了コードは0で、`export_log.txt`へ保存した。基板発注や業者への設計送信は行っていない。

`verify.py`で保存済みPCBとXMLの207端子を比較し、不一致0件を確認した。58部品すべてA面、2層、板厚1.6 mm、ヘッダ信号、両面GNDも確認した。外形APIの初回検証は22.05 × 50.05 mmを返して失敗した。これは0.05 mmの線幅を含む外接矩形だったため、Edge.Cuts中心線の座標差で測定するよう修正し、22 × 50 mmを確認した。基板形状自体は変更していない。

回路図PDFは`pdftoppm`で画像化して確認した。抵抗・コンデンサの文字と縦向きラベルの重なりを見つけ、部品名の位置を調整した。PCB PDFは初回の単一ページ重ね描きから`--mode-multipage`へ変更し、シルク各層を確認した。Pythonによる配置・配線プレビューも出力した。最終CADの電気接続を変えずに、図面の読みやすさを修正した。

`README.md`、`reports/result.md`、本記録、判断・検討記録、製造レビュー用READMEを作成した。日本語の最終編集にはyomiyasuスキルを使用した。共通仕様の写し、識別子、コマンド、数値、ログには文体変更を適用していない。KiCadライブラリの公式ライセンス文書を取得し、複製したフットプリントの由来と変更を`libraries/NOTICE.md`へ記載した。

`yomiyasu_lint.py --json`で6文書を確認した。READMEの索引を表に整理し、「正本」を具体的な操作の説明へ直した。チェック結果は`yomiyasu_*.json`。板厚、信号名、未検証事項の意味は変更していない。

未完了事項はUSB差動特性、J2/J3メーカーランド照合、EEPROM設定、実機通信・電源・熱・発振試験、価格比較、独立CAM検証。詳しくは`result.md`。ERC/DRC合格をこれらの検証完了とは扱わない。
