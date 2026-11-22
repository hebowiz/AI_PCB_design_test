# A-2 V3-polish 回路図の一次レビュー（人間レビュー移行判定）

確認日：2026-11-22 JST  
対象ブランチ：`experiment/A2-schematic-v3-polish` / `778ab8896a4f9b71efba0c45f701cbf2fdfc2cac`  
基準：`experiment/A2-schematic-v3-refine` / `6654fae9168145beb779b06f72582182a3117050`  
レビュー範囲：GitHubの全体PNGと前後比較画像、USB/ESD・FT232H・UART・LDO/電源ツリー・EEPROM・LED・FB回路の拡大PNG、保存済み機械検証JSON、Gitコミット差分、GitHubの前後ネットリストXML・ERC JSONの照合。**ローカルKiCadでの独立検証、データシートに基づく回路正当性検査、実機・製造試験は未実施。**

## 判定

**回路図の視認性改善は一旦完了とし、人間による回路レビューに進めてよい**。V0の部品一覧に近い回路図から、機能ブロック、電源ツリー、USB/XTAL/UARTの接続関係、局所ESD/パスコン/FB部品の関係が追える図面になった。ユーザー自身の主観評価は「95点くらい」であり、客観的な品質保証スコアとは区別する。今後の追加の作図注文は一旦停止し、**V4の独立作図実験**または**回路の電気的レビュー**へ移行する方針。

## 主な画像

- [V3-refineとV3-polishの横並び比較](https://github.com/hebowiz/AI_PCB_design_test/blob/experiment/A2-schematic-v3-polish/01_New_Design/kicad_direct/reports/schematic_v3_polish/comparison_refine_polish.png)
- [V3-polish全体PNG](https://github.com/hebowiz/AI_PCB_design_test/blob/experiment/A2-schematic-v3-polish/01_New_Design/kicad_direct/reports/schematic_v3_polish/after/schematic.png)
- [FT232H電源・FB・パスコン](https://github.com/hebowiz/AI_PCB_design_test/blob/experiment/A2-schematic-v3-polish/01_New_Design/kicad_direct/reports/schematic_v3_polish/after/detail_ft232h.png)
- [LDO入力・出力](https://github.com/hebowiz/AI_PCB_design_test/blob/experiment/A2-schematic-v3-polish/01_New_Design/kicad_direct/reports/schematic_v3_polish/after/detail_ldos.png)
- [UART周辺パスコン](https://github.com/hebowiz/AI_PCB_design_test/blob/experiment/A2-schematic-v3-polish/01_New_Design/kicad_direct/reports/schematic_v3_polish/after/detail_uart_caps.png)
- [USB/ESD](https://github.com/hebowiz/AI_PCB_design_test/blob/experiment/A2-schematic-v3-polish/01_New_Design/kicad_direct/reports/schematic_v3_polish/after/detail_usb_esd.png)
- [電源ツリー](https://github.com/hebowiz/AI_PCB_design_test/blob/experiment/A2-schematic-v3-polish/01_New_Design/kicad_direct/reports/schematic_v3_polish/after/detail_power_tree.png)
- [Codex作業レポート](https://github.com/hebowiz/AI_PCB_design_test/blob/experiment/A2-schematic-v3-polish/01_New_Design/kicad_direct/reports/schematic_v3_polish/report.md)

## 視覚的な観察

- **コンデンサ**：V3-refineで横向きだった8部品（C3〜C6、C9〜C12）が縦向きに戻り、全22個でGNDを下側に表示する配置。機械検査の記録とFT232H等の拡大画像から改善が確認できる。
- **部品表示**：Referenceを上、Valueを下に置き、コンデンサ・IC・LED・FB・端子周辺の文字を近接配置。主な拡大図では対応関係が追いやすくなっている。
- **保持された良い点**：D1の短い分岐、USB/水晶信号の並走、フェライトビーズのコイル記号、電源のシリーズ/ツリー表示、GND三角記号、実線で追えるUART配線と非接続クロス。
- **判断上の例外**：コンデンサの縦向きと文字の空間を優先したため、一部の図面上のICピン距離はV3-refineより増えた。このトレードオフはユーザーの明示した優先度と整合。**紙面の距離をPCB実配線長と見なさない**。
- **残る表示上の特徴**：一枚のA2全体縮小では文字が小さいため、詳細はPDF拡大や機能別PNGを使用する。多ピンIC周辺には非接続交差が残るが、一律に禁止しないというユーザーの方針に合致する。

## 独立に照合した証拠と限界

| 項目 | 確認 |
| --- | --- |
| V3-refine→V3-polishの既存ファイル差分 | GitHub比較で既存変更は`a2_usb_uart.kicad_sch`のみ。それ以外は新規検査記録・画像 |
| XMLネットリスト | GitHubから`before/netlist.xml`と`after/netlist.xml`を取得。**`design/source`（Worktreeのパス）と`design/date`の2フィールドを除いて、XMLの文字列が完全一致** |
| 部品/端子/ネット | Codexの`comparison.json`で58部品/207端子/58ネット一致、差分0と記録 |
| ERC | GitHubの`before/erc_fresh.json`・`after/erc.json`を直接解析し、双方とも違反0件。従来の`single_global_label`、`four_way_junction`、`simulation_model_issue`、`footprint_filter`の無視設定は同一 |
| コンデンサの向き | `capacitor_orientation_check.json`がC1〜C22の22個すべて縦向き、GND下側と報告。画像でも主な部品を目視確認 |
| Reference・Value | `component_field_check.json`が58部品について表示・文字方向・上下順序を検査。レイアウトの良し悪し自体は目視評価 |
| 保全確認 | Codexが669既存ファイルをblob照合し差分なしと報告。GitHubのコミット比較でもCAD製造データの既存変更は回路図だけ |

注：ネットリストの出力元パスの違いは異なるWorktreeから出力したためであり、`design/date`の違いは出力時刻。XMLの比較結果は**回路変更が無いことの強い証拠**だが、元の回路が機能的に正しいことの証明ではない。

## 未評価の対象

- FT232Hの電源/USB/EEPROM設定、LDOのFB/EN、レベル変換の方向とIOレベル、外部端子の給電/スイッチ条件を含む回路機能の妥当性
- USB差動90Ωの実配線、GND帰路、スタックアップ、発振・ESDの実装条件
- フットプリント、3D形状、機構クリアランス、Gerber/CAM、実機6Mbps、熱・EMC

これらを回路レビュー・基板レビュー・実機評価の独立工程で検証する。**今回の「作図品質の合格」は設計・製造の承認ではない。**

## 次の進め方

- V3-polishを人間レビュー候補のスナップショットとして保存し、`main`へ回路図をマージしない。
- **V4**：独立の詳細指示による作図スタイルを別条件で評価。V3の規約との差を後から比較し、共通部分/選択式スタイル候補を抽出。
- **回路レビュー**：V3-polishの接続・定数・部品選定・電源シーケンスなどをデータシートと照合し、電気的な問題を個別に扱う。必要な修正は別ブランチで記録。
- スキルの生成・仕様リストGUI・PCB再設計は、別の指示があるまで実施しない。
