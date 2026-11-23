# PCB同期 作業ログ

2026-11-23 16:19 JST〜16:49 JST。最初のネットリスト出力から報告書作成まで約29分。事前のWorktree・ルール確認と最終Git反映はこの計測に含めない。

## 準備

最新origin/main（664b58595ea96c4748b9fb23c9c8510a20b18b27）のAGENTS.md、design-workspace-management、schematic-designの検証規則と共通設計入力を確認。回路図描画は変更せず、KiCad CLI/APIでPCBだけを同期する方針を採用した。板厚は当初仕様1.0mmより後のユーザー指定1.6mmを優先。報告の文章にはyomiyasuを適用した。

`git fetch origin`、`git worktree list --porcelain`、各Worktreeの`git status --porcelain`で基準を確認。承認済み設計はfffbcdbe41bad236baee48d88cf96b95f27421f4。固定Worktreeとmainにはプロジェクト設定の未コミット編集があり、それぞれ保護した。managed worktreeを同コミットから作成し、codex/a2-pcb-syncへ切り替えた。

環境はWindows / PowerShell 7.6、KiCad 10.0.8と同梱Python・pcbnew。画像変換にNode.js / Sharpを使用。atopile、全体の設計生成、製造データの出力は実行していない。

## 実施順序

1. `sch export netlist --format kicadxml`でapproved.xmlを保存。旧PCBとプロジェクト設定をbeforeへ保存し、ERC・DRC・端子属性を比較した。
2. synchronize.pyで部品集合・属性・パッドネットを同期。残すフットプリントのUUIDを保持し、交換品も元フットプリントUUIDを継承した。旧パッド配線は電源名の更新と必要な局所除去に限定した。
3. place_local.pyで新規・交換部品のみ位置を検討。コートヤード干渉と周辺配線を確認し、C1/C2/C11/C12/D1の移動とC23/D5/R17/TP配置を確定した。
4. 変更部品近傍の配線を座標・UUIDで確認し、targeted_copper.pyで対象19本を除去。route_local.pyで未配線端点間のみ配線。元route.pyから関数定義を読み込んだが、全面配線のメイン処理は呼び出していない。
5. 旧U3/U6等の行き止まりをplan_stubs.pyで調べ、選別した25オブジェクトをfinish_copper.pyで除去。残った+3V3の2接続を局所配線した。
6. finish_labels.pyで旧枝4本を除去し、D5のGNDビアをパッド外へ配置。15部品の参照番号表示を調整した。最後に不要な旧PWR_EN/VPLL枝17本をUUID指定で除去し再充填した。
7. ERC/DRCと独立属性検証を実行。KiCad SVGから表裏・配置・拡大PNGを作成し目視確認した。輪郭寸法は線幅を含む描画境界でなく、Edge.Cutsの中心線で22×50mmを確認した。

## 検証コマンド

以下は作業ディレクトリ`01_New_Design/kicad_direct/`を基準とした主要コマンド。実行ファイルはKiCad 10.0/binのkicad-cli.exeとpython.exeを使用した。

```text
kicad-cli sch export netlist --format kicadxml -o reports/pcb_sync/approved.xml a2_usb_uart.kicad_sch
kicad-cli sch erc --format json --severity-all -o reports/pcb_sync/after/erc_final.json a2_usb_uart.kicad_sch
kicad-cli pcb drc --schematic-parity --refill-zones --save-board --format json --severity-all -o reports/pcb_sync/after/drc_final.json a2_usb_uart.kicad_pcb
python reports/pcb_sync/scripts/verify_sync.py
python reports/pcb_sync/scripts/export_views.py
node reports/pcb_sync/scripts/render_views.cjs
git diff --check
```

## 検証の経過

|段階|DRC違反|未配線|回路図不一致|
|---|---:|---:|---:|
|drc_sync|119|12|3|
|drc_placed|53|14|3|
|drc_cleared|35|20|3|
|drc_routed1|33|3|0|
|drc_cleaned|18|2|0|
|drc_routed2|18|0|0|
|drc_finished|2|0|0|
|drc_final|0|0|0|

## エラー・再試行

KiCadの初回CLIはサンドボックス内のレジストリアクセスに失敗したため、許可された環境で再実行した。pcbnewのビア幅取得には層引数が必要で、引数なしの呼出しを中断して修正。UUID属性の直接代入もAPIに対応しないためSetUuidへ変更した。

補助ファイルinspect.pyがPython標準inspectを隠し、診断JSONが一時上書きされた。inventory_board.pyへ改名し、保存済みの変更前PCBから基準JSONと差分を再生成した。CADへの追加変更はない。配置候補探索と文字配置探索では解がない段階で保存せず、局所探索範囲・間隔を調整して再実行した。PNG切出しはSVGの解像度解釈を修正し、一旦PNGへ変換してから切り出した。

DRC分類だけによる配線一括削除案は自動承認レビューに拒否され、実行しなかった。座標・UUIDを確認した対象の明示リストと基板ハッシュ照合へ変更して実施した。保存を含み得るスクリプトの診断再実行も拒否されたため、読み取り専用診断で確認後に必要な編集を別途実施した。

独立検証では外形の描画境界が線幅を含むため寸法判定に失敗した。Edge.Cuts中心線の座標で検証するよう直し、外形形状の変更がないことを再確認した。DRC除外や回路図の修正による対処はしていない。

最終結果と未検証事項は[README](README.md)に記載。製造データ、main、固定Worktree、レビュー済みブランチの設計は変更していない。

## 最終確認

619件の既存A-2ファイルが基準Git blobと一致した。main・固定Worktreeのプロジェクト設定は開始時のSHA256を維持。新規レポートの相対リンク、補助Pythonの構文、git diff --checkを確認した。日本語の最終推敲を実施し、リンターが挙げた時系列手順の箇条書きと画像の「解像度」は必要な表現として保持した。
