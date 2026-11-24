# PCB配線品質の調査証跡

対象は`5596d3bc8802687b89b21fd9c57e1117ec9382e5`。CADは読み取りのみ。[調査・修正計画](../../batches/2026-11-24_R-0028_R-0032_investigation.md)に判断と限界を記載した。

## 計測結果

| ファイル | 内容 |
| --- | --- |
| [summary.json](summary.json) / [assessment_summary.json](assessment_summary.json) | 全体集計、候補の分類、計画範囲 |
| [net_lengths.csv](net_lengths.csv) / [nets.json](nets.json) | 全39ネットの線長、ビア、幅、各検出数 |
| [unique_lengths.json](unique_lengths.json) | 同一層の重複中心線を除いた線長 |
| [detours.json](detours.json) | 端子対、経路長、直線距離、座標、配線UUID |
| [turns_ge90.json](turns_ge90.json) | 90°以上の転向座標、角度、層、UUID |
| [cycles.json](cycles.json) | 閉路候補、経路座標、UUID |
| [open_leaf_candidates.json](open_leaf_candidates.json) / [leaf_assessment.json](leaf_assessment.json) | 葉端候補と接続部・GNDの分類 |
| [duplicate_overlap.json](duplicate_overlap.json) | 同一層中心線の重複区間 |
| [pad_near.json](pad_near.json) | 同一ネットpad–trackの近接候補、距離、座標、UUID |
| [normal_short_edge_extensions.json](normal_short_edge_extensions.json) | 正常な短辺延長領域として分離した組 |
| [pad_corridors.json](pad_corridors.json) | 隣接ICパッド間を通る配線 |
| [usb5v_widths.json](usb5v_widths.json) / [usb5v_thin_segments.json](usb5v_thin_segments.json) | 電源幅集計、全細線の座標・UUID・近傍パッド |
| [proposed_scope.json](proposed_scope.json) | A/B/P別の対象ネット・UUID。撤去命令ではない |
| [geometry.json](geometry.json) | 調査元の配線、ビア、パッド輪郭 |
| [preservation.json](preservation.json) | 設計保全・台帳構造検査 |

線長は配線線分の中心線長の合計で、ビアの垂直長とゾーンを含まない。端子間グラフ経路はパッド・ビアの接触節点を統合するので、単純な線分合計とは異なる。各候補を直ちに確定違反とせず、報告書の分類に従う。

## 全体図と拡大図

- [表面・ゾーン表示あり](native_front.png)、[裏面・ゾーン表示あり](native_back.png)。基準コミットに含まれるKiCad出力をコピーし、Git blobを照合した。[出典](image_provenance.json)。
- [EEPROMの迂回](01_eeprom_detour.png)
- [+3V3の転向](02_turns.png)
- [PWREN_Nの枝と並列経路](03_control_stub.png)
- [VIO・帰還の閉路](04_power_loops.png)
- [U2のパッド間通過](05_interpad.png)
- [U4.1への近接](06_ldo_pad_near.png)
- [USB5V系の全経路](07_usb5v_routes.png)
- [USB5V_OUTの裏面葉端](08_output_stub.png)

拡大図は実座標・線幅・パッド輪郭から生成した技術図。赤は表面、青は裏面、灰色は他ネット、金色は注目ネットのパッド。ゾーンは非表示で、表面から見た座標に統一した。08は裏面銅箔のみ表示する。表面TP2との位置の重なりを電気的接続と誤認しないこと。[図の範囲・層](figures.json)。

## 再現手順

Windows / KiCad Python 10.0.8、shapely 2.2.0、networkx 3.6.1、Pillowを使用。追加ライブラリは一時フォルダ`%TEMP%/a2-pcb-quality-packages`へインストールした。既存の設計生成スクリプトは実行していない。

```powershell
& 'C:/Users/hebow/AppData/Local/Programs/KiCad/10.0/bin/python.exe' audit.py 'C:/Users/hebow/.codex/worktrees/a2-pcb-review/99_AI_PCB_design_test/01_New_Design/kicad_direct/a2_usb_uart.kicad_pcb'
& 'C:/Users/hebow/AppData/Local/Programs/KiCad/10.0/bin/python.exe' assess_and_plot.py
```

[audit.py](audit.py)は入力PCBが基準コミットのblobと一致することを確認して読み込み、保存処理を呼ばない。[assess_and_plot.py](assess_and_plot.py)はJSONから分類・図を作る。入力パスとKiCad環境が異なる場合は引数またはスクリプトの画像参照先を合わせる。[verify_records.py](verify_records.py)で台帳と設計保全を検査する。補助スクリプトはこのレビュー用の試作であり、承認済み設計スキルではない。

初期のパッド間検査は非隣接パッドを含めて誤検出したため、間にパッドがある組を除外した。転向検査は次数2点に限定し、閉路・葉端は銅箔の重なりを別分類した。正常接続と候補の照合、表裏全体図および8枚の拡大図を確認し、図の見出し重なりも修正した。
