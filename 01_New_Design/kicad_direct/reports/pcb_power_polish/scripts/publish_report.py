from pathlib import Path
import json,datetime,hashlib
R=Path('01_New_Design/kicad_direct/reports/pcb_power_polish');a=json.loads((R/'before/analysis/summary.json').read_text());b=json.loads((R/'after/analysis/summary.json').read_text());i=json.loads((R/'integrity.json').read_text());turn=json.loads((R/'all_turns.json').read_text());now=datetime.datetime.now().astimezone();
comparison={k:{'before':a[k],'after':b[k]} for k in ['tracks','vias','total_track_mm','turn_ge90','non_GND_cycles','duplicate_overlap_pairs','near_pad_track_pairs','corridor_track_pair_hits','detour_pairs']};comparison['raw_endpoint_angle_candidates']={'before':len(json.loads((R/'before/all_turns.json').read_text())),'after':len(turn)};(R/'quality_comparison.json').write_text(json.dumps(comparison,indent=2))
report=f'''# A-2 PCB再修正 — R-0024・R-0027・R-0029

対象ブランチは`codex/a2-pcb-corners-decoupling`。基準は`87711e88e10653e79fdce9c3ade341b8f1440489`。ユーザーが残件の再調査・修正と固定Workspaceへの反映を依頼した。今回の結果は人間レビュー待ちであり、最終OK・製造承認ではない。

開始は2026-11-25 00:18 JST、設計検証完了は{now:%Y-%m-%d %H:%M} JST。Windows / PowerShell 7.6、KiCad 10.0.8のPython API・CLIを使用した。atopileや全面再生成は使用していない。

## 修正内容

R-0024・R-0029では、連続線分の角度をパッド・ビアの内側まで調べ直した。従来の配線グラフ検査はこれらをまとめていたため、見た目に残る角を見落としていた。今回、通常の二方向接続の90°・135°曲がりを45°単位へ修正し、パッド・ビア内の不要な重複線分を整理した。水晶の部品位置は維持し、残る曲がりだけを処理した。USB D+/D−はUUID・幅・座標・層を含めて変更前と一致する。

R-0027では、C1/C2/C11/C12、FB1/FB2、C3/C10を再配置した。C12をC10の近くへ移し、FB2→C12→C10→U1.8の順につないだ。C11はFB1とC9の間に配置し、C1はC23の手前、C2はVCCD出力と+3V3分配の間に置いた。C16の供給線がパスコンを迂回する分岐も修正した。C19の位置はU4出力との短い接続を維持し、電源線を0.3mmへ広げ、既存GNDビアへの明示配線を追加した。

C12の配置場所を確保するため、R1も局所移動した。移動した実部品は9個。IC・コネクタ・ヘッダ・スイッチ・水晶・テストポイントの位置は維持している。参照文字は移動箇所とその周辺だけ調整した。

C11/C12は承認済み回路図どおりDNPのまま。今回の経路は、その実装ランドを経由して小容量コンデンサへ給電する構造であり、4.7µFを実装済みとみなした評価ではない。C2/C5はVCCDの出力コンデンサなので、IC出力→C2→分配・C5という出力側の構成を維持した。コンデンサの電気的接続はすべて従来の並列接続。

## 配置・経路の比較

以下の配線長はパッド内銅箔を縮約したグラフ上の値。配線インダクタンスの実測・抽出値ではない。

| 経路 | 変更前 mm | 変更後 mm |
| --- | ---: | ---: |
| C12→C10 | 5.0080 | 1.3853 |
| C11→C9 | 14.8173 | 13.1906 |
| C1→C23 | 3.2514 | 3.4681 |
| U4出力→C19 | 1.0053 | 1.0053 |

C1→C23は0.2167mm増えた。C1を給電経路に確実に含め、GND帰路・他部品との間隔を確保した結果であり、全区間を短縮したとは扱わない。C11→C9はUSB・水晶の保護経路を避けるため、裏面を回る経路が残る。さらなる短縮には周辺配置の見直しが必要で、今回の候補の制約として残す。

GND端子中心から最寄りGNDビア中心までの距離は、C1が1.4534→1.3285mm、C2が1.5352→1.0500mm、C11が4.6090→1.6325mm、C12が3.9272→1.0500mm。C18は1.5089mm、C19は1.2121mmを維持した。これは近接距離であり、面内電流経路や実効インダクタンスを表す値ではない。C10の2方向サーマル帰路とGNDの並列接続は意図的に保持した。

## 検証結果

| 項目 | 結果 |
| --- | --- |
| ERC / DRC / 未配線 / 回路図不一致 | 各0件。除外追加なし |
| 部品・端子 | 58部品・197端子。番号・値・型番・フットプリント・DNP・ネット一致 |
| 回路図・プロジェクト・カスタムルール | 変更前とバイト一致 |
| 外形・厚さ・層数 | 22×50mm・1.6mm・2層を維持 |
| ビア・マスク・サーマル | 0.3/0.6mm、+0.05mm、サーマル接続を維持 |
| IC短辺中央引き出し | 64交差のずれ0件、側面接触0件 |
| 非45°線分 / 狭ピッチICパッド間通過 | 各0件 |
| 通常の二方向接続の90°以上の曲がり | 0件 |
| 電源供給→大容量→小容量→IC | 10経路の順序を配線グラフで確認 |
| USB・水晶の直下交差 | 許可済みUSB交差以外は0件。GND参照面の新規欠損0 |
| 信号・電源の閉ループ | 0件。GNDの意図的並列帰路2件 |

総配線長は{a['total_track_mm']:.5f}→{b['total_track_mm']:.5f}mm。配線{a['tracks']}→{b['tracks']}本、ビア{a['vias']}→{b['vias']}個。接続順とGND帰路の確保を優先しており、総延長の最小化を達成したという評価ではない。

生の端点ペアで90°以上となる候補は121→{len(turn)}組。残る組はC10のサーマル・ビア帰路、C16の端子分岐、+3V3の三方向分岐で、通常の二方向配線の曲がりとは分けた。座標・UUIDは`all_turns.json`に保存した。

同一ネットのパッド近接候補は14→23組。接続線を分割・面取りすると、接続直前・直後の線分も候補として増える。端子接続とその周辺線分を画像で確認し、狭ピッチICへの側面接触・パッド間通過は0件だった。候補23組は`after/analysis/pad_near.json`に残し、DRC合格だけで一般的な配線品質まで保証しない。

USB5Vの0.25mmネックは従来の2区間・合計1.18721mmを維持。USB5Vの他区間、USB5V_SW、USB5V_OUTは0.5mm。BOM・Gerber・ドリル・実装座標・既存生成スクリプトは変更していない。

## 試行と自己レビュー

1. 元PCBを`before/`へ保存し、修正は`candidate/`だけで実施した。PLL側、東側のバルク電源、GND、曲がり角の順に検証した。
2. 初期配置で生じた部品外形の重なり、銅箔間隔不足、USB5Vとビアの干渉を修正した。USB差動線ではなく、5V入力の局所経路を上側へ移してFB1への給電を確保した。
3. 冗長線分の除去と面取りにより、サーマルのスポーク不足が発生した。U4の既存接続アンカーを復元し、C10では十分な直線スポークを残して角を処理した。GNDの孤立面はビアで接続した。
4. 保護対象との照合で、USBビア内の短い3線分も整理対象に入っていたことを検出した。3線分を元UUIDで復元し、優先配線の完全一致を再検証した。UUIDの直接代入はAPIで拒否されたため、`SetUuid`に変更した。
5. 電源グラフ検査でC16の迂回分岐を検出し、C16ランドを経てU2へ給電する経路へ修正した。
6. 表裏全体図、FT232H、USB・電源、UART・LDOの拡大図を複数回確認した。シルク干渉とICピンへ斜めに入る面取りを修正し、最終データから画像と検証結果を再出力した。

各試行のDRCは`checks/`、銅箔の変更前後は`copper_diff.json`、部品移動は`integrity.json`、補助処理は`scripts/`に保存した。試行用スクリプトは各段階の入力を前提とするため、完成PCBへ一括再実行しない。

## 証跡と残課題

- [表面の比較](comparison_front.png)、[USB・電源の比較](comparison_usb_power.png)、[FT232Hの比較](comparison_ft232h.png)、[UART・LDOの比較](comparison_uart_ldo.png)
- [表面](after/front.png)、[裏面](after/back.png)、[最終DRC](after/drc_final.json)、[ERC](after/erc_final.json)
- [整合性](integrity.json)、[電源経路順](after/analysis/power_order.json)、[容量周辺の距離比較](capacitor_metrics.json)、[全ネットの配線長](after/analysis/net_lengths.csv)

人間によるR-0024・R-0027・R-0029の再判定は未実施。C11周辺の残る迂回、電源分岐・サーマルの見え方は今回の画像で確認してほしい。配線の寄生L、PDN、USBの全経路SI、発振余裕、ESD/EMC、実機動作・製造性は未評価。製造データは旧版のまま。
'''
(R/'README.md').write_text(report,encoding='utf-8')
# Promote only the independently verified candidate, preserving all other CAD files.
root=R.parents[1];pcb=root/'a2_usb_uart.kicad_pcb';assert hashlib.sha256(pcb.read_bytes()).hexdigest()=='3050da346a6d76e879fd3505c282a47a194f6da79f6527ffc4a8f0e8ac686526';candidate=R/'candidate/a2_usb_uart.kicad_pcb';assert hashlib.sha256(candidate.read_bytes()).hexdigest()==i['pcb_sha256'];pcb.write_bytes(candidate.read_bytes())
log=f'''\n## {now:%Y-%m-%d %H:%M} JST — PCBの残件再修正\n\n目的：R-0024・R-0027・R-0029への再指摘に対応する。実施操作：87711e8から専用ブランチを作り、候補PCBで大容量コンデンサの配置・給電順・GND帰路と配線角を修正した。KiCad 10.0.8のPython API、`sch export netlist`、`sch erc`、`pcb drc --schematic-parity`、配線グラフ・幾何検査、SVG/PNG出力を使用。\n\n変更ファイル：A-2 PCB、`reports/pcb_power_polish/`、本ログ・判断・議論記録。結果：ERC/DRC/未配線/回路図不一致0、10電源経路の順序を確認。回路図・設定・BOM・製造データ・既存生成処理は保持。候補の検証後にPCBへ反映した。\n\n検証証跡・失敗と再試行：[修正報告](../01_New_Design/kicad_direct/reports/pcb_power_polish/README.md)、同フォルダの`integrity.json`・`checks/`・`copper_diff.json`。日本語本文はyomiyasuで意味・数値を保持して校正した。未解決事項：C11の残る迂回と実機電気性能、人間による最終判定。固定Workspaceはユーザーの更新依頼に従い、版確定後に安全に反映する。\n'''
with Path('docs/work_log.md').open('a',encoding='utf-8') as f:f.write(log)
with Path('docs/decision_log.md').open('a',encoding='utf-8') as f:f.write('\n## DEC-A2-PCB-POWER-001 — 電源経路と曲がり角の再修正\n\n日付：2026-11-25。供給経路にバルクランドと小容量ランドを順に含め、GNDビアを近付ける。通常の二方向配線の曲がりと、サーマル・電源分岐を別に検査する。USB優先配線とコネクタ位置を維持するため、C11の迂回は残す。全面再配置は採用せず、人間の再レビューで必要性を判断する。詳細は`reports/pcb_power_polish/README.md`。\n')
with Path('docs/discussion_log.md').open('a',encoding='utf-8') as f:f.write('\n## 2026-11-25 — PCB再指摘とコンデンサの接続順\n\nユーザーは13項目をOKとし、R-0024・R-0029の直角とR-0027のバルク配置を再指摘した。残件の再調査・修正とWorkspace更新を承認した。Codexはパッド・ビア内を含む角度検査と電源経路グラフを追加し、局所修正した。詳細な測定・試行・制約は`reports/pcb_power_polish/README.md`に集約。最終判定・実機検証は未実施。\n')
print('promoted',i['pcb_sha256']);print(json.dumps(comparison,indent=2))
