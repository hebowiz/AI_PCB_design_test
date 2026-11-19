# A-3：EasyEDA Proによる新規基板設計

結果と未検証事項は[設計結果](reports/result.md)を参照してください。板厚は1.6 mm、外部UART信号はTXD/RXD/RTS/CTSです。

EasyEDA Proで`projects/A3-USB-UART/A3-USB-UART.eprj3`を開くと、回路図とPCBを編集できます。フォルダ全体を保持してください。`exports/`には製造用形式の出力、`reports/`には検証結果と作業記録があります。

`scripts/`は今回の実験で使用・検討した操作の記録です。一括再実行用のビルド手順ではありません。途中状態の図形IDを指定する修正スクリプトも含むため、完成工程や人間が編集した工程へ順番に再実行しないでください。未実行の`complete-3v3.js`は、局所経路計算に置き換えた初期案です。

公式CLIを呼ぶ`invoke.ps1`はスクリプトと証跡の保存先をA-3領域内に制限します。`--code-file`を使い、Windowsのコマンド長制限を避けています。ネットリスト照合は`verify-netlist.py`、製造出力の検査は`verify-exports.py`、保存前後の比較は`compare-reload.py`で再確認できます。
