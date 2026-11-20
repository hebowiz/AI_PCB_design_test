# A-2 回路図視認性改善 V1：第三者一次レビュー

作成日：2026-11-20 JST  
レビュー対象：`experiment/A2-schematic-v1`（`beba27eed1f1c2a94be86ccc24ce8ffe5ae3d5e6`）。元の`main`コミット：`6491a464c2eb8ea2d876a913f37be9590db316d8`。  
状態：**ちゃぴによるリモートの図面・ログ一次レビュー。ユーザーによる正式レビューは未実施。**

## 結論

抽象的な「人間が読める回路図へ」という指示に対し、Codexは機能を理解してブロック単位で配置・局所接続へ変更できた。**定性的な視認性は初回より大きく改善**したと評価する。一方、A2横1枚の全体縮小では端子名が細かく、FT232Hの一体型シンボルや長い配線とネットラベルは引き続き読解を妨げる。これは正式な人間レビュー結果ではない。

## 図面へのリンク

| | 修正前 | 修正後 |
| --- | --- | --- |
| PNG | [before](../01_New_Design/kicad_direct/reports/schematic_v1/before/schematic.png)（V1ブランチ上のファイル） | [after](../01_New_Design/kicad_direct/reports/schematic_v1/after/schematic.png)（V1ブランチ上のファイル） |
| PDF | [before](../01_New_Design/kicad_direct/reports/schematic_v1/before/schematic.pdf) | [after](../01_New_Design/kicad_direct/reports/schematic_v1/after/schematic.pdf) |

上記相対リンクはV1ブランチ上での閲覧を想定。mainへの未マージ状態では次の固定URLから閲覧する。

- [修正前PNG](https://github.com/hebowiz/AI_PCB_design_test/blob/experiment/A2-schematic-v1/01_New_Design/kicad_direct/reports/schematic_v1/before/schematic.png)
- [修正後PNG](https://github.com/hebowiz/AI_PCB_design_test/blob/experiment/A2-schematic-v1/01_New_Design/kicad_direct/reports/schematic_v1/after/schematic.png)
- [Codex V1詳細報告](https://github.com/hebowiz/AI_PCB_design_test/blob/experiment/A2-schematic-v1/01_New_Design/kicad_direct/reports/schematic_v1/README.md)

## 観察した改善

- 10機能ブロックへ分離し、USB入力→FT232H→UARTレベル変換→外部端子、発振・EEPROM・電源関連を整理した。
- LDO FB分圧・切替、EEPROMのDI/DO、LED直列抵抗、電源開閉などは部品と配線の関係が以前より視覚的に追いやすい。
- ラベルは193→130（63個、約32.6%減）。局所接続を実線で表示する意図が確認できる。ただしラベル数そのものは読解品質の保証指標ではない。
- 接続変更禁止という条件を破っていないことを、保存されたXMLネットリスト比較とERCによって確認している。

## 記録上の客観的なチェック

| 確認項目 | 結果 |
| --- | --- |
| 正規化後KiCad XMLネットリスト | `design/date`のみ除外して完全一致 |
| ネット / 端子 / 部品 | 58 / 207 / 58、すべて維持 |
| 部品属性・ピン・埋込ライブラリ | 不変と記録 |
| KiCad ERC | 修正前後エラー0、警告0 |
| PCB、製造出力、元の生成スクリプト | 107ファイルをGit blobで照合し差分0 |
| 変更ブランチ | `experiment/A2-schematic-v1`。mainへ未マージ |
| ログ基準の経過 | 2026-11-20 17:41着手、18:04 push確認、約23分（概算） |

出典：V1ブランチの`reports/schematic_v1/README.md`、`comparison.json`、`layout_metrics.json`、`work_log.md`、および修正前後のPNG。**このレビューではローカルKiCadを起動した独立ERC/ネットリスト再生成は行っていない。**

## 引き続き改善したい点（V2候補）

1. **A2横1枚の縮小表示**：全体構成は分かるが、実際に部品とピン名を読むには拡大が必要。目的に応じて複数ページや階層シートを検討する。
2. **FT232Hの巨大な一体型シンボル**：ピン配置は元定義を保持。電源、USB、UART、制御が1つに詰まっている。機能分割シンボルは読みやすさ改善の候補だが、ライブラリ構造の変更が必要でありV1の「定義を変えない」条件の対象外。別検証とすべき。
3. **図面全体の余白・回路間の距離**：ブロック区分は成功。ただし長い線と離れた要素があるため、局所の理解と全体俯瞰を両立するための適切なページ設計が必要。
4. **機能的な配線・ラベルの使い分け**：FB回路や発振回路は局所配線が有効。長距離のUART接続と電源配布は、配線を伸ばすかラベルを使うかを設計レビューしながら最適化する。
5. **自動評価の限界**：ERC0とネットリスト一致は「電気的な同一性」の検証であり、読みやすさは設計者の主観評価と読解時間を別途収集する。

## 今後の判断

V1は変更を元のmainに混ぜず、独立した成果として保存する。ユーザーの正式レビュー後、必要ならV2では機能別階層シート、適切なページサイズ、局所回路の可読性ルールを明示し、**V1の変更を引き継がず元のV0から試す**。指示の効果を比較するため、初回設計とV1、V2の全体図と部分図、ネットリスト・ERC、作業時間を残す。
