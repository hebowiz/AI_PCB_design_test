# A-1 atopile設計

TXD/RXD/RTS/CTSのUSB-UART基板です。ユーザー指示により板厚を1.6 mmへ変更しました。22×50 mm、2層、全部品を表面に配置しています。

最終ERC/DRCは違反0件、未配線0件です。ただし、USB差動配線、水晶周辺、ビアとパッドの重なり、機械寸法・実装条件の確認が残っています。製造承認済みではありません。詳細は[設計結果](reports/design_review.md)を参照してください。

| 成果物 | パス |
| --- | --- |
| 最終PCB | `board/a1.kicad_pcb` |
| プロジェクト・回路図 | `board/a1.kicad_pro`、`board/a1.kicad_sch` |
| atopile回路 | `board/main.ato`、`board/parts/parts.ato` |
| 接続・配置の原記述 | `scripts/design.py`、`board/design.json` |
| 回路図PDF | `reports/schematic.pdf` |
| 裸基板の画像 | `reports/board-top.png` |
| 表裏の配線図 | `reports/board-front.svg`、`reports/board-back.svg` |
| 検査結果 | `reports/erc.json`、`reports/drc.json`、`reports/connectivity.json` |
| 部品表・ピン接続 | `reports/bom.csv`、`reports/pin_net.csv` |
| 製造レビュー用 | `manufacturing/review-only/`、`manufacturing/A1-REVIEW-ONLY.zip` |
| 経緯 | `reports/work_log.md`、`reports/decision_log.md`、`reports/discussion_log.md` |

## 実行環境と再検査

atopileは`docs/atopile_recovery.md`で修復された0.15.8を使います。`scripts/ato.ps1`は共有Git管理ディレクトリから元リポジトリの`.setup-local/atopile-rebuild`を見つけ、設定・ログをA-1の`.local/`へ分離します。別の配置では`A1_ATOPILE_REBUILD`で指定できます。通常のPATHにある`ato`は使用していません。

KiCadは10.0.8、同梱Pythonは3.11.5、Freeroutingは2.1.0、Javaは21.0.13.9です。次のコマンドはリポジトリのルートから実行します。

```powershell
$cli = "$env:LOCALAPPDATA/Programs/KiCad/10.0/bin/kicad-cli.exe"
$py = "$env:LOCALAPPDATA/Programs/KiCad/10.0/bin/python.exe"
$env:PYTHONUTF8 = '1'
& $cli sch erc --format json --exit-code-violations -o 01_New_Design/atopile/reports/erc.json 01_New_Design/atopile/board/a1.kicad_sch
& $cli sch export netlist --format kicadxml -o 01_New_Design/atopile/reports/schematic.net.xml 01_New_Design/atopile/board/a1.kicad_sch
& $py 01_New_Design/atopile/scripts/check_connectivity.py
& $cli pcb drc --severity-all --format json --exit-code-violations -o 01_New_Design/atopile/reports/drc.json 01_New_Design/atopile/board/a1.kicad_pcb
& $py 01_New_Design/atopile/scripts/layout.py verify
& ./01_New_Design/atopile/scripts/manufacturing.ps1
```

製造出力スクリプトはファイルをローカルで生成するだけで、発注やアップロードはしません。出力の内容と使用条件は`manufacturing/README.md`を参照してください。

## 回路生成と配置・配線の再現範囲

`scripts/design.py`は原記述からatomic部品、BOM、接続マニフェストを生成します。続く`./01_New_Design/atopile/scripts/ato.ps1 build --verbose`は`board/layouts/default/default.kicad_pcb`を生成します。最終PCBとは別ファイルです。

`scripts/layout.py prep`は配置とUSB固定配線を作り、`board/a1.kicad_pcb`を上書きします。完成済みPCBや人が変更したPCBにそのまま実行しないでください。今回の最終配線はFreeroutingのSESを取り込んだ後、未接続とGND、サーマル接続を補修した結果です。生成から最終状態までを一度に再現する単一コマンドは用意していません。

初回DSN/SESは`board/a1.dsn`と`board/a1.ses`です。Freerouting単独の未配線0は、KiCad取り込み後の未配線0を意味しません。最終成果物は補修後の`board/a1.kicad_pcb`です。`repair.dsn`と`repair2.dsn`は完走しなかった追加配線の入力証跡です。

FreeroutingはA-1内の一時ディレクトリを作業ディレクトリにし、次の条件で実行しました。

```text
java -Xmx6g -Djava.awt.headless=true -jar freerouting-2.1.0.jar -de input.dsn -do output.ses -mp 30 -mt 2 -da -l en --gui.enabled=false --user_data_path=<A-1内の作業ディレクトリ>
```

`freerouting.json`ではGUIとoptimizerを無効にし、profileのemail/idを空にしました。パス数の指定に反して継続する挙動があったため、停滞した試行は中断しています。ログは`reports/router-attempt*.log`に保存しました。

最終フットプリントは`board/A1.pretty`に保存しています。元のatomic部品のフットプリントに対して、シルクを整理し、5パッドのGNDゾーン接続を直接接続へ変更しました。銅箔パッドの位置・番号・寸法は変更していません。ローカルライブラリとの照合も含めてDRCを実行しています。
