# A — 新規設計（3方式で実施）

同一の要求仕様を3種類の手段で実装し、回路・PCBの品質、工数、AIの自動化範囲、手作業の介入を比較する。

| ケース | 手段 | 保存先 |
| --- | --- | --- |
| A-1 | atopile + KiCad（配線にはFreeroutingも使用可能） | `atopile/` |
| A-2 | KiCad直接設計（回路図からPCBまで） | `kicad_direct/` |
| A-3 | EasyEDA Pro直接設計（回路図からPCBまで） | `easyeda/` |

- `specs/`: 3ケースに共通する設計要求仕様
- `reports/`: 方式横断の比較・レビュー
- 結果が異なった場合は、AIへの指示、使用機能、手直し、検証条件も記録する。

Bはこのディレクトリでは実施しない。B-2は`../02_Design_Modification/`で扱う。
