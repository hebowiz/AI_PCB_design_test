# A-1・A-2・A-3のmain統合レポート

実施日: 2026-11-19 JST

3方式の設計成果物を比較レビューできる状態に統合した。設計・製造データは元ブランチと同一で、回路やPCBの修正、再生成、製造発注は行っていない。このマージは設計品質の承認を意味しない。

## 対象とマージ履歴

開始時に`AGENTS.md`、共通の比較・時間記録、各方式の結果レポートと作業記録を確認した。`git fetch origin`で取得した`origin/main`の`5ef2baaa837fcd1a4bb1279cf71ab36a0de5443d`を統合の起点とした。

| 順序 | 対象ブランチ | 取得したコミットID | マージコミットID |
|---|---|---|---|
| 1 | `experiment/A-1` | `b4554f39007ae487521bddb4a3a652fb7d2f4933` | `4b9987326458ff9f2d0cca745550fb6b9e907f48` |
| 2 | `experiment/A-2` | `82993f6f010827e1861288bc8b744ad53e044e3e` | `445462a402da50ffa92f981d304e8723feebea35` |
| 3 | `experiment/A-3` | `a2c3f3b8a4a8beaaf4ce4d3d6dc167b805f3444a` | `a117156b80c507b443cce93d336c9c9cdad31870` |

専用Worktreeの`integration/a1-a2-a3`で、上表の固定コミットを順に`git merge --no-ff`した。3回とも競合はなく、各マージコミットの第2親は対象ブランチのコミットと一致した。元の実験ブランチは残し、履歴の書換えやforce pushは行っていない。

成果物を統合したコミットは`a117156b80c507b443cce93d336c9c9cdad31870`である。本書と共通作業ログは、その後の記録用コミットに含める。公開後の最終コミットIDとリモートとの一致結果は、作業完了時の報告に記載する。

## 作業中のファイルの保護

確認時点で3つの実験Worktreeは変更なしで、対応するチャットは待機中だった。元のmain作業フォルダには未追跡の`01_New_Design/specs/design_input.md`があったため、専用Worktreeでマージと検証を行った。この未追跡ファイルは追加・変更・移動していない。内容のSHA256は開始時とマージ後で一致した。

元のmainにはリモートの共通文書更新が2コミット未反映だった。最新の`origin/main`を起点にすることで、`docs/initial_3way_review.md`、`docs/experiment_elapsed_time.md`と既存作業ログの追記を保持した。

## ファイル件数

件数は起点のmainとの差分を`git diff --name-status`で集計した。リネームと削除はない。

| 範囲 | 追加 | 変更 | 削除 |
|---|---:|---:|---:|
| A-1 `01_New_Design/atopile/` | 149 | 0 | 0 |
| A-2 `01_New_Design/kicad_direct/` | 107 | 0 | 0 |
| A-3 `01_New_Design/easyeda/` | 131 | 2 | 0 |
| 成果物の合計 | 387 | 2 | 0 |
| 今回の共通記録 | 1 | 1 | 0 |
| 記録を含む合計 | 388 | 3 | 0 |

A-3の既存ファイルの変更は`README.md`と`scripts/.gitkeep`で、どちらもA-3ブランチに含まれる変更をそのまま保持した。今回新たに編集したのは本書と`docs/work_log.md`だけである。各方式の変更は自方式のフォルダ内に収まっている。

## Git上の整合性

各対象コミットと成果物統合コミットに対し、`git ls-tree -r`で全ファイルのパス、mode、object種別、blob SHAを比較した。CADや製造データに加え、ライブラリ、画像、スクリプト、試行途中の記録、作業ログも比較対象に含めた。全393ファイルが一致し、欠落、余分な追加、内容変更、属性変更はいずれも0件だった。以下のtree SHAもそれぞれ一致した。

| 方式 | 比較ファイル数 | 元ブランチと統合後で一致したtree SHA |
|---|---:|---|
| A-1 | 150 | `d302ff1ee5e34f49314aa8e0b151fa59c126ae65` |
| A-2 | 108 | `1e18a4ad8cc47005536787d31af266653117912d` |
| A-3 | 135 | `ba66fac631fb9aed45b4ae46460e1a1beb448920` |

成果物統合時点では、3方式のフォルダ外にある既存66ファイルもすべて起点と一致した。その後の共通記録では作業ログに追記し、既存部分を保持した。比較レポートと時間記録には変更を加えていない。

`02_Design_Modification/`のtree SHAは起点・統合後とも`17133700b71ed9ff703dcf3fb91e13bbd33588bf`で、内容は変わっていない。Git管理外の原本や作業用設計にも操作していない。

## 成果物の保存状態

以下は保存済みファイルと検証記録の確認結果である。今回はCADアプリで開き直したり、ERC/DRC、配線、製造データ出力を再実行したりしていない。

| 確認対象 | A-1 | A-2 | A-3 |
|---|---|---|---|
| 編集可能なプロジェクト | `board/a1.kicad_pro`、`board/main.ato`、`board/parts/parts.ato` | `a2_usb_uart.kicad_pro` | `projects/A3-USB-UART/A3-USB-UART.eprj3` |
| 回路図と最終PCB | `board/a1.kicad_sch`、`board/a1.kicad_pcb` | `a2_usb_uart.kicad_sch`、`a2_usb_uart.kicad_pcb` | 同プロジェクトの`sch/Schematic1/P1.esch2`、`pcb/PCB1.epcb2` |
| ローカルライブラリ | `board/A1.kicad_sym`、`board/A1.pretty/`、`board/parts/` | `libraries/A2.kicad_sym`、`libraries/A2.pretty/` | 回路図・PCBファイルにSYMBOL、FOOTPRINT、DEVICEを内包 |
| ERC/DRC記録 | `reports/erc.json`、`reports/drc.json` | `reports/erc_final.json`、`reports/drc_final.json` | `reports/erc-final.json`、`reports/drc-final.json` |
| 接続検証 | `reports/connectivity.json`、`reports/netlist_check.json` | `reports/verification.json` | `reports/netlist-verification.json`、`reports/pcb-netlist-verification.json` |
| 製造レビュー用データ | `manufacturing/review-only/`、`manufacturing/A1-REVIEW-ONLY.zip` | `manufacturing_review/` | `exports/` |
| 作業履歴・判断 | `reports/work_log.md`、`decision_log.md`、`discussion_log.md` | 同左 | 同左 |
| 結果レポート | `reports/design_review.md` | `reports/result.md` | `reports/result.md` |

表内のパスは各方式のフォルダを基準とする。作業履歴・判断の3文書はいずれも各方式の`reports/`内にある。

A-1とA-2のライブラリテーブルにある`${KIPRJMOD}`参照6件は、すべて保存先が存在した。A-1には67個、A-2には18個の`.kicad_mod`がある。A-2のシンボルテーブルにはKiCad標準ライブラリの参照も残っている。A-3のPCBには27個のSYMBOL、17個のFOOTPRINT、27個のDEVICE文書、回路図には28個のSYMBOL、17個のFOOTPRINT、28個のDEVICE文書を確認した。A-3は別ファイルのライブラリが存在する形式として数えていない。

A-1の最終記録はERC違反0、DRC違反0、未配線0、接続検証エラー0だった。A-2もERC違反0、DRC違反0、未配線0、端子ネット不一致0だった。両方式のERCには4種類、DRCには5種類の無視設定が記録されており、0件という結果はその設定を含む条件での記録である。A-3はERC/DRCの`passed: true`、ratline 0、回路図・PCBそれぞれの185接続ピンの照合成功を保存している。

A-1とA-2は各8枚のGerberとPTH/NPTHの2種類のドリル、BOM、実装座標を保持した。A-1のレビュー用ZIPは16エントリ、A-3のGerber ZIPは15エントリで、どちらもCRC検査に成功した。A-3のZIPにはGerberとドリルが入り、BOMとPickPlaceは別ファイルで保存されている。A-3の`.csv`は既存の記録どおりUTF-16のタブ区切りで、再変換していない。

## 設計完了状態と人間によるレビュー

3方式とも、編集可能な設計、最終検証記録、製造レビュー用出力、技術判断の記録がそろっている。製造承認済みとしては扱わない。既存レポートに記載された未検証事項を以下に残す。

| 方式 | 保存済みの状態 | 今後の主な確認事項 |
|---|---|---|
| A-1 | 51部品。atopile生成物と、KiCadで配線・修正した最終基板を区別して保持。失敗した配線試行も保存 | USB差動配線・90Ω条件、D+/D−のvia数差、発振器配線、via-in-pad、暫定コネクタ寸法、電源・6Mbps実動作。atomic部品のERC型と自動部品選定の検証範囲 |
| A-2 | 58部品。KiCad設計、最終ERC/DRC、207端子のネット照合記録、製造レビュー出力を保持 | USB差動配線とvia数差、J2/J3の寸法、EEPROM設定、電源・熱・6Mbps実動作 |
| A-3 | 53部品。EasyEDA Proネイティブ設計、保存・再読込の検証、製造出力の検査記録を保持 | USB差動配線とGND帰路、露出パッドのペースト、EEPROM設定、50mA運用条件と過負荷保護、6Mbps実動作 |

正式なレビューでは各方式の結果レポートと`docs/initial_3way_review.md`を参照し、部品データシート、実装部品、製造条件との適合を確認する。今回のマージでこれらの判断を変更していない。

所要時間は`docs/experiment_elapsed_time.md`の暫定値を保持した。A-1は約49分、A-2は約36分、A-3は約84分である。A-3の最終Gitコミットまでの約82分との区別、並行実施の経過時間と各方式の合計時間との区別も既存文書のままとした。今回の統合時間を設計時間に加算していない。

## 公開対象の確認と残課題

追加対象は指定された3つの実験ブランチにある成果物と今回の共通記録だけである。Git管理外の作業ファイル、認証設定、インストーラ、ローカルキャッシュは追加していない。テキスト、ZIP内のテキスト、UTF-16の出力を調べ、秘密鍵、GitHubトークン、JWT、認証値の代入に該当する候補は検出しなかった。この検査は既知の形式を対象とする静的検査である。

既に同じ公開リポジトリの実験ブランチにある次の4ファイルには、作業端末のユーザーディレクトリを含む絶対パスが残っていた。

- `01_New_Design/atopile/board/repair.dsn`
- `01_New_Design/kicad_direct/reports/export_log.txt`
- `01_New_Design/kicad_direct/reports/routing_cage_repairs_console.txt`
- `01_New_Design/kicad_direct/reports/schematic.net.xml`

今回は元のblobを保つという統合条件に従って変更していない。公開情報の整理を別途行う際の確認対象とする。パスの実値は本書に転載していない。A-3のネイティブデータに含まれる作成者などのUUIDも、そのまま保持した。

## 再確認方法

以下の比較で出力がなければ、記録用コミット後も各方式の成果物に差分はない。

```powershell
git diff --exit-code b4554f39007ae487521bddb4a3a652fb7d2f4933 main -- 01_New_Design/atopile/
git diff --exit-code 82993f6f010827e1861288bc8b744ad53e044e3e main -- 01_New_Design/kicad_direct/
git diff --exit-code a2c3f3b8a4a8beaaf4ce4d3d6dc167b805f3444a main -- 01_New_Design/easyeda/
git diff --exit-code 5ef2baaa837fcd1a4bb1279cf71ab36a0de5443d main -- 02_Design_Modification/ docs/initial_3way_review.md docs/experiment_elapsed_time.md
```

個別blob一覧、静的検査とZIP検査の詳細は、元の作業フォルダのGit除外領域`.setup-local/design-integration/`に保存した。公開レポートには比較対象の固定コミットとtree SHAを記載し、Git履歴だけでも再比較できるようにした。
