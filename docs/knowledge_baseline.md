# 初期セットアップで確認した前提知識

確認日は2026-11-19。リポジトリの`7b0453f`を基準とし、ローカルに残っていた前回の作業ログも読んだ。今回は環境構築のみを行う。

## 実験の目的と独自ルール

新規設計では、自然言語で与えた仕様からAIが回路とPCBを作る過程を評価する。まずatopile方式を試し、KiCad直接編集方式との比較も残す。既存設計の修正では、人間の設計の指定箇所だけを変更し、それ以外の部品・ネット・配置・配線を保てるかを評価する。両者では、生成できる範囲と既存設計を守れる範囲を分けて測る。

このプロジェクトでは`AGENTS.md`を優先する。既存設計は複製して操作し、人間の編集後に全体を再生成しない。原本と作業コピーは公開Gitから除外する。記録は議論、決定、実作業に分け、ERC/DRCの合格と電気特性・RF/EMC・熱・製造性・実機動作の確認を区別する。発注や外部サービスへの設計送信には明示承認が必要である。

上流スキルはMITライセンスのコピーで、取り込み元は`203b4d32f1ad74f0d2046530431bcb9db47a2eef`。今回の調査では上流ファイルを変更しない。上流の経験則は、このPCで再現した結果としては扱わない。

## スキルの工程と受け渡すデータ

`.ato`から`ato build`で部品・ネットを含む`.kicad_pcb`とBOMを得る。配置表でフットプリントを配置し、`finish.py`のpre処理で層・固定配線・禁止領域などを用意する。配線前のDRCを経て不要な既存配線を除き、pcbnewからDSNを出す。Freeroutingが作ったSESを取り込み、post処理で配線の整理・ベタ・ステッチングを行い、シルクと最終DRCを確認する。その後にガーバー、ドリル、BOM、実装座標を作る。

前段と後段の境界はネット付きPCBと型番付きBOMであり、前段をKiCadなどに置き換える余地がある。atopile方式は編集可能な`.kicad_sch`を出さず、補助スクリプトはネット表やSVGを作る。SVG回路図とKiCad回路図を同一視しない。`make all`には`make fab`が含まれないため、BOMや実装座標の更新忘れにも注意する。

## 今回の対象ツール

| ツール | 指定版 | 役割 |
| --- | --- | --- |
| KiCad | 10.x、既存の10.xを優先 | PCB、DRC、画像・製造データ出力 |
| KiCad同梱Python / pcbnew | KiCad実体に適合する版 | 配置・編集、DSN書き出し、SES取り込み |
| atopile | 0.15.8 | 回路記述、部品選定、ERC、PCBとBOMの生成 |
| uv | 指定なし、既存版を優先 | atopile用の独立したPython環境とコマンド管理 |
| Freerouting | 2.1.0 JAR | DSNからSESへの自動配線 |
| Eclipse Temurin | Java 21 JDK | JAR実行と構造確認 |

スキルはatopile 0.15.8をCLI版として固定している。後継版への移行は今回の対象外。`ato auth login`の認証はインストールやヘルプ表示とは別に扱う。

## 補助スクリプトの静的確認

全20ファイルについて説明、import、引数、書き込み箇所とシェル依存を確認した。この確認段階ではスクリプトを実行していない。Pythonは標準ライブラリとpcbnew、および同梱のpcbkitを使用する。

| ファイル | 入力と出力・変更対象 | 主な依存 |
| --- | --- | --- |
| `sanitize_pcb.py` | PCBのネット・ビア保護表記をatopileが読める形式へ上書き変換 | Python標準 |
| `dedupe_uuids.py` | PCBの重複UUIDを再発行して上書き | Python標準 |
| `prune_fp_lib_table.py` | 存在しないフットプリントライブラリ参照を削除 | Python標準 |
| `place.py` | PCBと配置表または座標指定を読み、配置を上書き | pcbnew |
| `finish_board.py` | PCB、pre/post、設定Pythonを読み、段階別に上書き | pcbkit、subprocess |
| `pcbkit.py` | 形状・座標・ゾーン・固定配線などの共通処理。単独CLIではない | pcbnew |
| `unroute.py` | 非ロック配線とpostで作ったベタを削除 | pcbnew、pcbkit |
| `export_dsn.py` | PCBを読みDSNを新規出力 | pcbnew |
| `import_ses.py` | PCBとSESを読みPCBを上書き | pcbnew |
| `route.sh` | DSNからSESとrouter.logを出力。一時設定を作る | Bash、Java、Python、mktempなど |
| `check_route.py` | ルータログの未接続数・違反を検査 | Python標準 |
| `place_labels.py` | PCBのシルク・Fabを変更して上書き | pcbnew |
| `check_overlap.py` | PCBの部品外形の重なりを表示 | pcbnew |
| `check_models.py` | PCBの3Dモデルずれ・実装属性を検査 | pcbnew |
| `gerber_layers.py` | PCBから製造レイヤ名を標準出力 | Python標準 |
| `fab_files.py` | 座標CSVとBOM、任意のPCB・除外部品指定からBOM/CPLを出力 | Python標準 |
| `netlist_diagram.py` | PCBと任意のBOMからMarkdown/Mermaidネット表を出力 | pcbnew |
| `schematic.py` | 接続を照合してSVGを出すライブラリ | Python標準 |
| `kicad_python.sh` | pcbnewを読み込めるPythonのパスを出力 | Bash |
| `preview_svg.sh` | SVGからPNGを作成 | Bash、librsvg。代替はmacOS専用qlmanage |

## 失敗しやすい条件

KiCad 10の保存形式とatopile 0.15.8の読込形式が異なるため、再ビルド前に変換が要る。部品差し替えでネットが欠落する事例、再生成による部品番号変更、フットプリント内のカスタム銅の消失、重複UUIDが上流に記載されている。配置はatopileのインスタンス名を使い、BOMとパッドの接続を確認する。`.package`や値だけの指定では意図する部品寸法にならない事例もある。

特に`unroute.py`はロック配線を保持する一方、`finish_board.py`のpre処理はロック配線を削除して設定から作り直す。上流の「固定すれば保護できる」という説明を全工程に拡張してはいけない。人間が編集した既存設計へこの工程を一括適用しない。

Freeroutingの違反数が0でも接続が残ることがある。配線前の外形・配置・クリアランス、配線後のゾーン再充填と未接続を確認する。DSNに伝わらない規則、等長・インピーダンス・RF・高電圧などは別途検討する。DRCでは部品実体の干渉、極性、BOMの正しさ、回路性能まで保証できない。上流の製造可能性に関する断定も、このプロジェクトでは別途確認が必要なものとして扱う。

## Windowsで確認する事項

上流はmacOS/Linux向けである。`kicad_python.sh`の自動探索にはWindows標準パスがなく、`KICAD_PYTHON`指定が必要になる可能性がある。pcbkitにはフットプリントの環境変数による上書きがある。MakefileはBash構文と`timeout`、`seq`、`zip`などを使い、空白を含む実行パスの引用にも不足がある。

PythonのABI、pcbnewのDLL解決、atopileのWindows向け配布と依存関係、Git BashからJavaへ渡すパス、CRLF、Pythonの既定文字コードを調べる。DSN/SESはAPIの存在確認と実ファイルの変換試験を分け、今回は設計を作って試さない。WSL2の有効化や再起動は事前報告が必要である。実機での確認結果は`environment.md`へ記録する。

## 未決定事項と読んだ資料

新規回路の仕様、既存設計の対象と保護範囲、設計の正本、評価指標の具体的な合格基準は未決定である。既存設計のバックアップ先も、実データを受け入れる前に決める。

`AGENTS.md`、`README.md`、`THIRD_PARTY_NOTICES.md`、議論・決定・作業ログ、`report_outline.md`、`setup_plan.md`を読んだ。スキル本体、`examples/Makefile`、参照文書の`atopile.md`、`pcbnew.md`、`routing.md`、`design-rules.md`、`finish-config.md`、`fab/README.md`と`scripts/`を確認した。

## push前に取り込んだ追加方針

GitHubの`f3e951f`で、設計手段と検証内容が4ケースに整理された。新規設計はA-1のatopile + KiCad、A-2のKiCad直接編集、A-3のEasyEDA Proを共通仕様で比較する。既存KiCad設計の修正はB-2だけで扱い、atopileやEasyEDAによる再生成を適用しない。

更新された`AGENTS.md`、`setup_plan.md`、議論・決定ログと、追加の`comparison_matrix.md`、`easyeda_setup.md`を確認した。EasyEDA Proの導入・CLI検証は追加計画であり、今回記録したKiCad・atopile・Freeroutingの導入結果には含まれない。A-3用のフォルダと手順書は取り込んだが、EasyEDAのインストールや公式CLI文書の調査は未実施である。
