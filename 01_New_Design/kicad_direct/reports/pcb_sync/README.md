# A-2 承認済み回路図のPCB同期

R-0001〜R-0016を反映した回路図にPCBを同期した。これは人間によるPCBレビューの候補版で、PCB・製造の承認は未実施。

基準コミットは`fffbcdbe41bad236baee48d88cf96b95f27421f4`、作業ブランチは`codex/a2-pcb-sync`。基準回路図とプロジェクト設定は変更していない。固定Worktreeとmainにあった未コミット編集も保持した。

## 同期と検証

|項目|同期前|同期後|
|---|---:|---:|
|PCB部品数|58|58（5追加・5削除）|
|ERC違反|0|0|
|物理DRC違反|0|0|
|未配線|0|0|
|回路図とのDRC不一致|142|0|
|部品属性・端子ネット照合|不一致あり|58部品・197回路図端子、エラー0|

KiCad 10.0.8のCLIとpcbnewで検証した。DRCは既存設定を維持し、除外を追加していない。既存のignored checksは`missing_courtyard`、`track_not_centered_on_via`、`tuning_profile_track_geometries`、`footprint_filters_mismatch`、`footprint_type_mismatch`。この範囲はDRC合格に含めない。基板外形22×50mm、板厚1.6mm、2層、全フットプリントの表面配置を確認した。

新設C23/D5/R17/TP1/TP2、削除U3/U6/C20/C21/R16、承認済みのコンデンサ・水晶・ESD部品変更を反映した。R17の両端をTP1/TP2へ接続し、SW2〜J2間の0Ωを介した電源経路を確認。R17は過電流保護を行わず、PPTCへの無条件の置換互換もない。

既存部品の移動は5部品、既存配線・ビアの93.93%を形状のまま保持した。USBコネクタ・外部ヘッダ・スイッチの配置、基板外形、GNDゾーン輪郭を維持している。全体の再生成・全面再配線は行っていない。

## レビュー資料

|内容|資料|
|---|---|
|部品・ネット・配置・配線差分|[差分一覧](difference.md)、[全差分JSON](schematic_pcb_difference.json)|
|整合性・保全|[integrity.json](integrity.json)、[preservation.json](preservation.json)|
|ERC / DRC / 未配線 / 回路図照合|[ERC](after/erc_final.json)、[DRC](after/drc_final.json)|
|全体画像|[表面](after/front.png)、[裏面・反転表示](after/back.png)、[部品配置](after/placement.png)|
|拡大画像|[USB・電源](after/usb_power.png)、[FT232H](after/ft232h.png)、[R17・TP1・TP2](after/jumper_testpoints.png)|
|変更前|[表面](before/front.png)、[裏面](before/back.png)、[元PCB](before/a2_usb_uart.kicad_pcb)|
|作業経緯・コマンド|[作業ログ](work_log.md)|

全体の表裏、部品配置図と3箇所の拡大図を確認した。局所配線の再検証を繰り返し、D5のGNDビアをパッド外へ移し、変更部品とその周辺の部品番号表示を整理した。画像はKiCadのSVGをPNGへ変換したもので、裏面は反転表示。

## PCBレビューに残す事項

|対象|確認事項・制約|
|---|---|
|USB D+/D−|インピーダンス、対内結合、リターン経路、ビア非対称を未評価。総配線長はD+ 7.9452mm・D− 8.0156mm、ビア数は2・0だが、分岐を含む総銅箔長なので遅延やスキューの合格判定には使えない。|
|実装パッド内ビア|新規ビアがR14.1、R17.1/2、TP1.1、TP2.1に重なる。TP2は2箇所。はんだ吸い込み、充填・キャップ処理、測定接触面をレビューする。既存分を含む座標一覧はintegrity.json。|
|D1/D5とGND|D5のGNDビアは径0.50mm・穴0.25mm、短い接続線でパッド外に設置した。ESD電流経路・寄生インダクタンス・レジスト開口の製造余裕は未評価。|
|電源・発振|C23はU1.40近傍、C1/C2は旧U3周辺に配置。電源ループ、GND帰路、C11/C12のDNP位置、Y1の寄生容量と発振条件はPCBレビュー・実機評価が必要。|
|ヘッダ・スイッチ・測定点|既存位置を維持。コネクタの正式ランド寸法、嵌合・操作空間、R17取り外し後のTPへのプローブ接近性は未確認。|
|シルク|DRC上の重なりは解消。C12など離して表示した参照番号の対応、実寸での読みやすさをレビューする。|

BOM・Gerber・ドリル・実装座標は旧版のままで、今回のPCBに対応しない。PCBレビュー完了後に正式更新する。固定フォルダへの反映は人間の承認後とし、未コミット編集の扱いも確認してから行う。

## 補助スクリプトの扱い

`scripts/`は今回の段階的編集と検証の記録。編集スクリプトを完成PCBに順次実行してはいけない。途中状態のバックアップ・UUID・ハッシュに依存するため、完全な一括再現手順ではない。特に`stub_cleanup_plan.json`は最終段階の計画であり、旧段階の`finish_copper.py`に再使用しない。

読み取り検証は`verify_sync.py`、画像出力は`export_views.py`と`render_views.cjs`。既存の設計生成スクリプトは変更していない。
