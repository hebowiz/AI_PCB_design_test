# A-2 KiCad直接設計

**現行設計前提条件は[specs/current_design_baseline.md](specs/current_design_baseline.md)を参照。** 当初の共通仕様1.0 mmに対し、A-2の基板厚は設計途中で**1.6 mmに変更・確定**。本READMEの部品数・製造データは初回A-2生成版の記録であり、レビュー後の回路図（別ブランチ）との同期を意味しない。

FT232Hを使ったUSB-UART基板の製造前レビュー版。UART信号はTXD/RXD/RTS#/CTS#、外形は22 × 50 mm、板厚は1.6 mm、2層で、58部品をA面に配置した。

回路図、配置・配線済みPCB、部品表、Gerber、ドリル、実装座標を作成した。最終ERC/DRCは警告・エラーとも0件、未配線0件、回路図とPCBの不一致0件。ただしUSBの90 Ω差動配線とヘッダの正式ランド寸法が未確認のため、製造へリリースできる状態ではない。

|用途|ファイル|
|---|---|
|設計結果|[結果・未検証事項](reports/result.md)|
|経緯|[作業記録](reports/work_log.md)、[判断記録](reports/decision_log.md)、[検討記録](reports/discussion_log.md)|
|図面|[回路図PDF](reports/schematic.pdf)、[PCB各層PDF](reports/pcb_layers.pdf)|
|編集用CAD|[プロジェクト](a2_usb_uart.kicad_pro)、[回路図](a2_usb_uart.kicad_sch)、[PCB](a2_usb_uart.kicad_pcb)|
|製造出力|[レビュー用製造データ](manufacturing_review/README.md)|

KiCad 10.0.8で作成。atopileは使用せず、他方式の成果物も参照していない。設計データはローカルで生成した。製造業者へのアップロードや発注はしていない。

## 再検証と出力

PowerShellから、リポジトリのルートで実行する。

```powershell
& ./01_New_Design/kicad_direct/scripts/export.ps1
& "$env:LOCALAPPDATA/Programs/KiCad/10.0/bin/python.exe" ./01_New_Design/kicad_direct/scripts/verify.py
```

`export.ps1`はERC/DRCが通った場合に出力する。編集・再出力には保存済みの回路図・PCBを使う。`generate.py --replace-generated`は回路図とPCBを作り直して配線を失わせるため、通常の再出力には使わない。`route.py`、`repair_routes.py`、`resolve_cages.py`は今回の生成・修正過程の記録であり、完成PCBに順次実行する手順ではない。人手で変更した後は、差分とバックアップを確認せずに再生成・再配線しない。
