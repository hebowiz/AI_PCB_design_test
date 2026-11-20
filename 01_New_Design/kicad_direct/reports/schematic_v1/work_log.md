# A-2 回路図視認性改善 v1 作業ログ

## 2026-11-20 17:41–17:43 JST — 作業場所と修正前の状態を固定

目的は、回路を変えずに回路図の読みやすさを改善すること。AGENTS.mdとA-2の既存回路図・設計記録を確認した。他方式の設計成果物は参照していない。

Codexの`create_worktree`でmainから独立Worktreeを作成した。操作IDは`b39bf72d-d7d7-42b6-a22c-d73e5859b5bf`。作業場所は`C:/Users/hebow/.codex/worktrees/a2-schematic-v1/99_AI_PCB_design_test`。そこで`git switch -c experiment/A2-schematic-v1 main`を実行した。開始コミットは`6491a464c2eb8ea2d876a913f37be9590db316d8`。元のA-2 Worktreeは使い回していない。

対象の回路図を`before/a2_usb_uart.kicad_sch`へ複製した。KiCad CLIでXMLネットリスト、ERC、PDFを出力し、pdftoppmでPNGへ変換した。修正前のERCは警告・エラー0件。実行環境はWindows、PowerShell 7.6、KiCad 10.0.8、KiCad同梱Python 3.11.5。

## 2026-11-20 17:44–17:48 JST — 機能別の配置と配線表現

修正前はICと受動部品が離れ、多くの接続をネット名だけで追う必要があった。A2横1ページは維持し、USBからUARTへの信号経路を上段、補助回路を中段、電源回路を下段に整理した。機能を示す見出しと短い動作注記を追加した。

`layout.py`は修正前回路図のシンボルを移動・回転し、フィールドの表示位置を調整する。部品データは回路図、端子ネットは修正前のXMLから取得した。元の設計生成スクリプトは使用せず、書き換えていない。S式の読書きだけに既存の`sexpr.py`を利用した。

帰還抵抗、負荷容量、電源フィルタ、EEPROM、電源制御、LEDは実線で結んだ。離れた機能間や交差を避けたい信号にはラベルを残した。初回の変更後ERCは0件。端子ネットの比較も差分0件だった。その後、出力日時だけを除いたXML全体も一致することを確認した。

## 2026-11-20 17:49–17:53 JST — PDF・PNGの目視修正

PDF検査の手順に従い、PDFをPNGへ描画して全体と主要ブロックを確認した。初回は色付き図面だったが、公平に比べるため前後とも白黒出力へ統一した。PNGはともに4200 × 2970ピクセル。

拡大図で、横向き抵抗の文字が縦向きになる箇所、180度回転部品の文字反転、R4の文字と本体の重なり、U5の電源線と部品名の重なりが見つかった。文字角度と揃え方を調整し、LED・フェライトの文字にも余白を追加した。修正用ツール呼出しを一度組み立て損ねてJavaScript構文エラーになったが、その呼出しではファイルを変更していない。次の呼出しで修正した。

配線幅が0の描画では実線が薄かったため0.1524 mmへ指定し、分岐点を直径0.762 mmで表示した。同じネットで重なる線は分割・重複除去し、実際に分岐する場所に接続点を付けた。変更後のERCを再実行し、引き続き0件だった。

## 2026-11-20 17:54–17:56 JST — 一致確認と記録

`verify.py`でXML全体を比較し、`design/date`だけを除いて完全一致した。58ネット、207端子、58部品を含む。部品の値・型番・フットプリント・番号を含むプロパティとUUIDも一致した。埋込みシンボル定義は変更していない。

mainの既存A-2ファイルを照合し、対象回路図以外の107ファイルは変更なしだった。対象にはPCB、製造データ、元の生成・配線スクリプト、プロジェクト設定、ライブラリ、過去のレポートを含む。結果は`comparison.json`と`protected_files.csv`に保存した。

比較PDF・PNG、主要ブロック拡大図、元の回路図、前後のXML・ERC、補助スクリプト、評価レポートをこのフォルダへ保存した。日本語文書はyomiyasuスキルの観点で推敲し、リンターで確認した。共通docs/への追記は自動承認審査で指定作業領域外として拒否されたため、実施していない。記録はA-2配下の本フォルダに集約した。拒否された呼出しではファイル変更はなかった。

未解決事項は、第三者による視認性評価、A2縮小表示での細部の読みやすさ、U1の既存ピン配置、元の設計が持つ電気・機構の検証残件。今回の作業ではPCB変更や製造データ再生成を行っていない。

## 主な実行コマンド

`<stage>`は`before`または`after`。前後のXMLは同じ入力パスから、それぞれの編集時点に出力した。

```powershell
kicad-cli sch export netlist --format kicadxml -o reports/schematic_v1/<stage>/netlist.xml a2_usb_uart.kicad_sch
kicad-cli sch erc --format json --exit-code-violations -o reports/schematic_v1/after/erc.json a2_usb_uart.kicad_sch
kicad-cli sch export pdf --black-and-white -o reports/schematic_v1/<stage>/schematic.pdf a2_usb_uart.kicad_sch
pdftoppm -scale-to 4200 -png -singlefile schematic.pdf schematic
python reports/schematic_v1/verify.py
```

実際にはKiCad同梱の実行ファイルを絶対パスで指定し、リポジトリのルートからA-2までの相対パスを引数に渡した。修正前PDFの白黒再出力だけは保存済みの複製を入力にした。ネットリスト比較用の入力パスは変えていない。
