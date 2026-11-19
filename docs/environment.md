# Windowsセットアップ環境

確認日は2026-11-19。主ツールの導入は完了したが、atopileはネイティブモジュールの命令セット不一致で起動できない。公開文書のユーザー別パスは`%USERPROFILE%`、`%LOCALAPPDATA%`、`%APPDATA%`で表し、詳細な生ログはGit管理外の`.setup-local/`へ保存した。

## 導入前の環境

Windows 11 Home 25H2、ビルド26200.9457、OSとプロセスはx64。PowerShellは7.6.5。通常の実行プロセスは管理者権限なし。サンドボックス内ではCIM照会が拒否され、権限付き照会でWindows 11 Homeを確認した。レジストリのProductNameは旧表記のWindows 10 Homeだった。

| 項目 | 導入前の検出結果 | 配置・補足 |
| --- | --- | --- |
| winget | 1.29.380 | `%LOCALAPPDATA%\Microsoft\WindowsApps\winget.exe` |
| Git | 2.46.0.windows.1 | `C:\Program Files\Git\cmd\git.exe` |
| Python / py | 3.11.9 | pythonは`C:\Program Files\PyManager\python.exe`経由、pyは`C:\Windows\py.exe`。Python311の実体も存在 |
| uv / ato | PATH上に見つからず | ユーザーの`.local\bin`にも該当なし |
| Java | Oracle 17.0.12 | `C:\Program Files\Common Files\Oracle\Java\javapath\java.exe`が優先 |
| jar | Temurin 11.0.14.1 | `C:\Program Files\Eclipse Adoptium\jdk-11.0.14.101-hotspot\bin\jar.exe` |
| KiCad | 6.0.7、8.0.4 | `C:\Program Files\KiCad\6.0`、`8.0`。10.xなし |
| kicad-cli | PATH上に見つからず | KiCad 8.0のbinに存在 |
| make | PATH上に見つからず | 追加依存候補 |
| bash | PATH上に見つからず | `C:\Program Files\Git\bin\bash.exe`は存在 |
| Freerouting | 指定JARなし | `%USERPROFILE%\tools`に既存配置なし |

PATHには既存のJava 17へのOracleリンク、Temurin 11、Git cmd、Python、WindowsAppsなどが含まれる。KiCad 10、uv、ato、Git Bashは含まれていなかった。Javaとjarの版が異なるため、試験ではJava 21の実体を明示する。既存ツールの削除やPATH全体の置換は行わない。

## 導入元の確認

`winget show`で`KiCad.KiCad`の10.0.8、`astral-sh.uv`の0.13.9、`EclipseAdoptium.Temurin.21.JDK`の21.0.13.9を確認した。

- [KiCad公式Windows配布](https://www.kicad.org/download/windows/)
- [uv公式インストール手順](https://docs.astral.sh/uv/getting-started/installation/)
- [Temurin公式配布](https://adoptium.net/temurin/releases/?version=21)
- [Freerouting 2.1.0公式リリース](https://github.com/freerouting/freerouting/releases/tag/v2.1.0)

## 事前調査で分かったWindows固有の注意点

Git Bash 5.2.26は既存の実行ファイルを直接指定すると起動した。Bash内にはGNU timeoutとseqがあるが、make、zip、rsvg-convertは見つからなかった。Windows標準のtimeout.exeはGNU timeoutの代替にはならない。

チェックアウト済みの3本の`.sh`はCRLFだが、このGit Bashではすべて`bash -n`が成功した。`kicad_python.sh`も実行できた。上流Makefileは空白を含むKiCadのパスを引用していない。`kicad_python.sh`の自動検出はmacOS/Linux向けなので、Windowsでは適合するPythonを明示する必要がある。これらは主ツールの導入とは別の実行手順の課題である。

[atopile 0.15.8のPyPIメタデータ](https://pypi.org/project/atopile/0.15.8/)はPython `>=3.14,<3.15`を要求し、Windows x64向けの`cp314` wheelを提供している。既存Python 3.11へ上書き導入せず、uvが用意する専用環境を使う。

## 導入結果

| 対象 | 使用版 | 配置先 | 判定 |
| --- | --- | --- | --- |
| KiCad | 10.0.8 | `%LOCALAPPDATA%\Programs\KiCad\10.0` | 導入・CLI起動OK |
| KiCad同梱Python | 3.11.5 | 同上の`bin\python.exe` | pcbnew 10.0.8のimport OK |
| uv | 0.13.9 | `%USERPROFILE%\.local\bin\uv.exe` | 導入・起動OK |
| atopile専用Python | 3.14.10 | `%APPDATA%\uv\python\cpython-3.14.10-windows-x86_64-none\python.exe` | 直接指定で起動OK |
| atopile | 0.15.8 | 環境は`%APPDATA%\uv\tools\atopile`、入口は`%USERPROFILE%\.local\bin\ato.exe` | 導入のみOK、CLI起動失敗 |
| Eclipse Temurin JDK | 21.0.13+9 | `C:\Program Files\Eclipse Adoptium\jdk-21.0.13.9-hotspot` | Java・jar起動OK |
| Freerouting | 2.1.0、build-date 2025-04-12 | `%USERPROFILE%\tools\freerouting-2.1.0.jar` | JAR構造・本体起動OK、配線未試験 |

KiCadは公式インストーラのユーザー向け標準配置、uvは公式PowerShellインストーラの標準配置、Javaは公式MSIの標準配置を使用した。Freeroutingはセットアップ計画指定の場所に置いた。KiCad 6/8、既存Python、Java 11/17は削除していない。

Codexアプリ内の実行では、Windowsイベントにuv環境の実体として`%LOCALAPPDATA%\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Roaming\uv\...`が記録された。uv自身は上表の`%APPDATA%`パスを返す。アプリの外から起動する通常の端末で、同じ環境が見えるかは未検証である。uv管理のPythonマイナーバージョン用ジャンクションは、対象の実体が存在していてもuvの検出でエラーになった。原因の断定はしていない。

uvインストーラはユーザーPATHへ`.local\bin`を追加した。既に開いている端末には再起動かプロセス内PATHの更新が必要である。KiCadとJava 21は実行ファイルを直接指定して検証した。既存Javaの優先順位を手動で変更していない。

## KiCadと補助スクリプトの確認

`kicad-cli version`は10.0.8、`kicad-cli pcb export --help`は終了コード0だった。標準ライブラリは`share\kicad`配下にあり、直下項目数はfootprints 155、symbols 224、3dmodels 105、template 58だった。この数は個々の部品数ではない。

同梱Pythonで`import pcbnew`に成功し、`ExportSpecctraDSN`と`ImportSpecctraSES`が呼出可能な関数であることを確認した。`export_dsn`、`import_ses`、`pcbkit`もimportでき、17本のPythonスクリプトを構文解析できた。`KICAD_FOOTPRINT_DIR`を指定するとpcbkitのライブラリ探索も成功した。一般のPython 3.11.9やatopile用3.14へpcbnewをコピーしていない。

`kicad_python.sh`の自動探索は失敗したが、`KICAD_PYTHON`に同梱Pythonを指定すると終了コード0で正しいパスを返した。実際のPCBを使うDSN/SES変換、DRC、レンダリング、GUIの操作試験は未実施である。

```powershell
$setupKiCad = Join-Path $env:LOCALAPPDATA 'Programs\KiCad\10.0'
& "$setupKiCad\bin\kicad-cli.exe" version
$env:KICAD_PYTHON = "$setupKiCad\bin\python.exe"
$env:KICAD_FOOTPRINT_DIR = "$setupKiCad\share\kicad\footprints"
& $env:KICAD_PYTHON -c "import pcbnew; print(pcbnew.GetBuildVersion())"
```

## atopileの起動障害

初回の`uv tool install "atopile==0.15.8"`は、Python 3.14を取得した後も3.11.9を選択し、版要件を満たせず失敗した。`--python 3.14`ではuv管理下のマイナーバージョンリンク検出に失敗した。取得済みPythonの実行ファイルを直接指定すると、123パッケージと`ato`、`faebryk`をインストールできた。`uv tool list`と`importlib.metadata.version('atopile')`は0.15.8を返した。

```powershell
$setupAtoPython = Join-Path $env:APPDATA 'uv\python\cpython-3.14.10-windows-x86_64-none\python.exe'
& "$HOME\.local\bin\uv.exe" tool install --python $setupAtoPython 'atopile==0.15.8'
```

導入後の`ato --help`と`ato --version`は、いずれも`-1073741795`で異常終了した。Windowsイベントは`pyzig.cp314-win_amd64.pyd`の例外`0xc000001d`、オフセット`0x444e4`を示した。`python -X faulthandler -c "import pyzig"`でもIllegal instructionを再現した。

CPUはIntel Core i7-12700。.NETのintrinsics検査ではAVX2がtrue、AVX512FとAVX512DQがfalseだった。既存のVisual Studio Build Tools付属dumpbinで配布モジュールを逆アセンブルすると、障害位置にEVEX形式の`vpbroadcastq ymm0,rbx`があり、ほかにもzmmレジスタを使う命令が多数あった。同じ0.15.8 Windows wheelがAVX-512非対応CPUでimport時に落ちる問題は、[上流Issue #1838](https://github.com/atopile/atopile/issues/1838)にも報告されている。実測した障害位置とCPU機能から、配布バイナリの命令セット不一致と判断した。認証の不足によるエラーではない。

`ato auth login`は未実行で、認証状態も未確認。CLI起動を修復した後、認証が必要ならユーザーによるブラウザ操作を行う。ビルドや部品APIの接続は試していない。

| 対応候補 | 利点 | 今回の扱い |
| --- | --- | --- |
| 同じ0.15.8をWindowsでbaseline CPU向けに再ビルド | Windows環境を維持できる | Zig等のビルド依存、ソースと生成物の検証が別途必要。未実施 |
| Linux / WSL2で0.15.8を使用 | 上流スキルのシェル環境に近い | Linux側の配布・KiCad連携を別途検証する。WSL2の有効化は事前承認が必要 |
| 他バージョンへ変更 | 修正版があれば候補になる | 0.15.8固定条件を変えるため採用していない |

WSL2への移行が必須とは、まだ判断していない。OS機能、仮想化設定、再起動の操作は行っていない。

## JavaとFreeroutingの確認

Java 21とjar 21.0.13の版表示、および`jar tf`が成功した。JARには`META-INF/MANIFEST.MF`と`app/freerouting/Freerouting.class`がある。

JAR取得元は[公式2.1.0リリースのJAR](https://github.com/freerouting/freerouting/releases/download/v2.1.0/freerouting-2.1.0.jar)。サイズは66,978,394バイトで公式APIのasset sizeと一致した。SHA256は`2c07d58f75dac03782664081e7a58b41c25400d871a9fcf166a2ea6fe60d5def`。リリースAPIにdigestはなかったため、この値は取得ファイルの再現用ハッシュであり、公開済みハッシュとの照合結果ではない。

`route.sh`のJava起動形式を確認し、追加の`-help`、`-da`、`--user_data_path`は[2.1.0の引数処理](https://github.com/freerouting/freerouting/blob/v2.1.0/src/main/java/app/freerouting/settings/GlobalSettings.java)で確認してから使用した。PowerShellでは`'-Djava.awt.headless=true'`を引用する必要があり、引用しない初回はクラス名の解釈エラーになった。環境変数`FREEROUTING__USER_DATA_PATH`では読込時に警告が出たため、引数で設定した。

最終実行ではv2.1.0を表示して終了コード0になった。ヘルプ本文は`command_line_help`というキーのみで、完全な引数一覧は表示されなかった。設定の再読込時には`currentLocale`の警告もあった。本体の起動確認として記録し、配線の成功とは扱わない。

```powershell
$setupJava = 'C:\Program Files\Eclipse Adoptium\jdk-21.0.13.9-hotspot\bin\java.exe'
$setupRouterData = Join-Path (Get-Location).Path '.setup-local\freerouting-smoke'
& $setupJava '-Djava.awt.headless=true' -jar "$HOME\tools\freerouting-2.1.0.jar" -help -da -l en '--gui.enabled=false' "--user_data_path=$setupRouterData"
```

上流`route.sh`は作業ディレクトリへ設定JSONを置くが、[2.1.0の起動コード](https://github.com/freerouting/freerouting/blob/v2.1.0/src/main/java/app/freerouting/Freerouting.java)は既定のユーザーデータ領域から設定を読む。実配線前には設定の参照先とヘッドレス実行方法を合わせる必要がある。この問題はWindowsだけの制約とは限らない。

## 残る課題と証跡

主ツールの導入に加え、全工程を上流Makefileのまま実行するにはGNU make、zip、画像プレビュー用librsvgなどが不足している。追加導入かPowerShell手順への置換が必要で、今回は導入していない。Bash/Python/Java間のパス表記、空白の引用、文字コード、改行、Freerouting設定の参照先も実配線前に整える。上流スキルのファイルには変更を加えていない。

`.setup-local/`にはKiCad・uv・atopileの導入ログ、atopile依存パッケージ一覧、pyzig障害イベントと逆アセンブル結果、KiCad/Pythonの確認ログ、Java版表示、JARエントリとFreerouting起動ログを保存した。公開用には本書へ必要な結果を転記した。

今回の終了範囲はインストールと非設計の起動確認まで。回路・PCB生成、既存設計の編集、ERC/DRC、製造データ生成、発注は実施していない。記録の保存は、追加のユーザー指示に基づく作業完了時のコミット・push方針に従う。
