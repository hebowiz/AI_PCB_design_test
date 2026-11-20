# A-2 回路図視認性改善 V2 — GitHub成果物の第三者一次レビュー

レビュー日：2026-11-20（JST）  
対象：`experiment/A2-schematic-v2` / `89093caab59e9e6897808d0fd020dd2c689ba450`  
比較基準：V0（main起点`77f0fd37e0d04b10f6831f88b8f035a009238701`）、V1（`experiment/A2-schematic-v1` / `beba27eed1f1c2a94be86ccc24ce8ffe5ae3d5e6`）。  
範囲：GitHubに保存された成果物とレポート、保存済み前後PNG・拡大図の目視、Gitのリモート差分、ネットリストXMLとERC JSONの直接比較。**ローカルKiCadでの独立再出力やユーザーによる正式レビューは未実施**。

## 要約・判定

**作図方針の反映：おおむね成功。電気的同一性・既存成果物の保全：保存された証跡とリモート差分上で合格。人間向けの視認性：V1に対して一長一短。**

V2では「同一機能内の接続は実線主体」「機能ブロック間は必要に応じてネットラベル」「単一A2シートを維持」の方針が明確に採用された。V1からの改善は、局所の受動部品だけでなくIC端子まで実線化した点にある。特に水晶・リセット・REF抵抗、FT232H→レベル変換、レベル変換の電源・プルアップ、VIO帰還が読みやすくなった。

一方、USB D+/D−の大回り配線、UARTの2か所の斜め交差、ページ上段への回路集中など、実線化に伴う可読性の損失もある。**「実線追跡の増加」と「実際の人間による総合的な読みやすさ」を同義としない。**

## 比較図・拡大図（V2ブランチの固定成果物）

- [V0/V1/V2 三列比較](https://github.com/hebowiz/AI_PCB_design_test/blob/experiment/A2-schematic-v2/01_New_Design/kicad_direct/reports/schematic_v2/comparison_v0_v1_v2.png)
- [V2回路図 全体](https://github.com/hebowiz/AI_PCB_design_test/blob/experiment/A2-schematic-v2/01_New_Design/kicad_direct/reports/schematic_v2/after/schematic.png)
- [USB・水晶・リセット](https://github.com/hebowiz/AI_PCB_design_test/blob/experiment/A2-schematic-v2/01_New_Design/kicad_direct/reports/schematic_v2/after/detail_usb_clock_reset.png)
- [UART・レベル変換・外部端子](https://github.com/hebowiz/AI_PCB_design_test/blob/experiment/A2-schematic-v2/01_New_Design/kicad_direct/reports/schematic_v2/after/detail_uart_io.png)
- [VIO FB・スイッチ](https://github.com/hebowiz/AI_PCB_design_test/blob/experiment/A2-schematic-v2/01_New_Design/kicad_direct/reports/schematic_v2/after/detail_vio_feedback.png)
- [V2実装・測定レポート](https://github.com/hebowiz/AI_PCB_design_test/blob/experiment/A2-schematic-v2/01_New_Design/kicad_direct/reports/schematic_v2/README.md)

## 方式の比較

| 項目 | V0 | V1 | V2 | 解釈 |
|---|---:|---:|---:|---|
| 機能区分 | 部品分類が主 | 10ブロック | 9ブロック | V2では水晶・リセットをFT232Hと組み合わせた |
| ネットラベル | 193 | 130 | 103 | V2はV1比で27減、V0比で90減 |
| wireセグメント | 193 | 222 | 278 | 配線分割を含むため、本数だけで可読性評価不可 |
| junction | 0 | 22 | 34 | 実線結合の増加を反映 |
| バス | 0 | 0 | 0 | UART4信号は個別実線を選択。必ずしも問題ではない |
| 選定35組の実線追跡 | 0 | 14 | 32 | あらかじめ選んだ35組であり全回路網羅率ではない |
| ERC | 0 | 0 | 0 | 検査条件内の結果。4項目の無視設定を維持 |

数値の出典：V2ブランチ内`drawing_comparison.json`、`wire_visibility.json`、`comparison.json`。V1のERCは今回の作業で再実行せず保存済み結果を引用。

## 良くなった点（画像目視）

1. **USB・発振・リセット**：USBコネクタからESDを経由する経路、Y1/C13/C14からFT232HのOSCI/OSCOへの接続、REF/RESET回路が実線で追える。V1では水晶の負荷容量が視覚的にまとまった一方、IC端子とはラベルによる間接接続だった。
2. **UART**：FT232HからU2を経てJ2/J3までの4信号を実線として表示。U2の電源・方向設定・両OE端子・R11/R12プルアップも追える。
3. **VIO帰還**：R7/R8とR9/R10、SW1、LDOのFBのつながりとGND帰路が読める。V1でも良好だった部分をさらに明示。
4. **局所回路の機能整理**：EEPROM、LED、固定3.3V、出力スイッチの各回路がブロックにまとめられ、ネット名を探し回る頻度が減った。

## 残る問題（目視評価）

1. **USB配線の大きな迂回**：J1/D1からU1のD+/D−までを実線化した結果、上辺の長い線を経由する。USBの回路上の短い機能的接続を視覚的に強調するには配置の再検討が必要。**回路図上の線長はPCB配線長を意味しない**。
2. **UART信号の2か所の斜め交差**：接続点なしでネットは独立しているが、見間違いの余地がある。ピン順序が固定されるなら配線形状の再設計、もしくは局所的なラベルを併用する案もある。
3. **全体俯瞰の密度の偏り**：A2上部のUSB/FT232H/UARTに要素と長い線が集中。下段は個別ブロックが独立するため、縮小表示時の細かい文字と合わせて全体の可読性には限界がある。
4. **電源ピンの可視化は未達箇所あり**：U1のVPHY/VPLLフィルタ、3.3Vデカップリングなどはラベル接続を残した。元の一体型多ピンシンボルのピン配置が主な制約。選定35組で直接追えない3組が残ったことと整合する。
5. **実線とラベルを併用する局所回路**：同一ネットの名前を保つための識別ラベルも残しており、単純なラベル減少がすべて「接続省略の解消」とは限らない。これは正当な理由があるため欠点と断定しない。

## 電気的同一性と変更範囲の検証

- GitHubのコミット比較：基準`77f0fd3`からV2`89093ca`まで、変更された既存ファイルは`01_New_Design/kicad_direct/a2_usb_uart.kicad_sch`のみ。その他の差分67ファイルは新規の記録・検証素材である。
- GitHubから`before/netlist.normalized.xml`と`after/netlist.normalized.xml`を取り出し、文字列を直接照合して**完全一致**を確認した。正規化はCodexが実施済みで`design/date`以外は除外しなかったとの記録。ネット58・端子207・部品58は成果物レポートの集計値。
- GitHub保存済みの前後ERC JSONを直接パースし、両方とも`violations`が0件と確認。無視チェックは双方とも`single_global_label`、`four_way_junction`、`simulation_model_issue`、`footprint_filter`の4種類で不変。
- Codexの`comparison.json`はV0/V1/V2の部品属性、シンボル定義、UUID、107既存ファイルの保全を報告。ただし独立したKiCad実行、実機・製造検証は実施していない。
- V2はV1成果物を参照資料として複製したが、編集用の入力はV0だったと報告。分岐元はV1を含まないmainで、Git履歴も一致。
- V2ブランチはmainに未マージ。原設計データ、PCB/BOM/Gerberへの変更は検出されなかった。

## 時間・次の実験への示唆

- V2：着手19:24:02 JST→成果物完成19:41:16 JST＝**17分14秒**（push込みの証跡確定まで約19分57秒）。V1は成果物完成まで約15分、push確認まで約23分の概算。異なる条件の計時であり、数分差を速度の優劣と断定しない。
- V2から得た知見は、作図ポリシーの明示で「実線接続を優先する」という指示を図面へ反映させられること。ただし**実線化を最大化するだけでは人間向け図面の品質は最適化されない**。
- 次回はV2への追補ではなく別ブランチで、**実線接続を原則にしながら、大迂回と交差を禁止する例外基準**、ページ全体と拡大時の2段階での可読性評価、必要なら機能別シンボル分割や階層シートを別変数として検討するのがよい。
- 最終判断はご主人様の設計者レビューによる。現時点ではV2をmainへマージしない。

