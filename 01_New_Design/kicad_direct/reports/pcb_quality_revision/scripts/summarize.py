from pathlib import Path
import json,csv,datetime
R=Path('01_New_Design/kicad_direct/reports/pcb_quality_revision');A=R/'after_analysis';B=Path('D:/Documents/KiCad/10.0/projects/99_AI_PCB_design_test/docs/reviews/evidence/pcb_quality_5596d3b')
read=lambda d,n:json.loads((d/(n+'.json')).read_text(encoding='utf-8-sig'))
before={r['net']:r for r in csv.DictReader((B/'net_lengths.csv').open(encoding='utf-8-sig'))};after={r['net']:r for r in csv.DictReader((A/'net_lengths.csv').open(encoding='utf-8-sig'))}
with (R/'net_length_comparison.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.writer(f);w.writerow(['net','before_mm','after_mm','delta_mm','before_vias','after_vias'])
 for n in sorted(before):w.writerow([n,before[n]['total_mm'],after[n]['total_mm'],round(float(after[n]['total_mm'])-float(before[n]['total_mm']),5),before[n]['vias'],after[n]['vias']])
reasons={'C9.1':'IC電源ピンからC9へ入る接続経路の末端区間。別のパッドへ通過する配線ではない。','R11.1':'R11への意図的な接続。1nmの既存接続断片を含む。','R11.2':'移設したRXDビアからR11へ入る短い接続区間。','C15.1':'EEPROM電源とC15の分岐点から、短い水平線でC15へ接続する近傍区間。','R17.2':'0.5mm幅のUSB5V_OUTがR17からTP2へ出る接続区間。','SW1.2':'FB_2V5からスイッチ端子への意図的な接続区間。','D1.1':'保護対象USB差動線とESDの接続部。元の銅箔形状を維持。','D1.2':'保護対象ESDのGND帰路。元の銅箔形状を維持。','D5.1':'保護対象USB差動線とESDの接続部。元の銅箔形状を維持。'}
near=read(A,'pad_near')
for r in near:r['assessment']=reasons[r['pin']];r['human_review']='未判定'
(R/'pad_near_assessment.json').write_text(json.dumps(near,ensure_ascii=False,indent=2),encoding='utf-8')
turns=read(A,'turns_ge90')
for r in turns:r['assessment']='元の優先配線・GND帰路を保護した90°。' if r['net']!='USB5V' else 'J1電源引き出しと幹線・分岐の合流点。単一の直列経路の曲がりと区別する。'
(R/'remaining_turns.json').write_text(json.dumps(turns,ensure_ascii=False,indent=2),encoding='utf-8')
neck=read(A,'usb5v_widths')
(R/'neckdown.json').write_text(json.dumps({'net':'USB5V','pin':'U1.40','width_mm':.25,'centerline_length_mm':1.18721,'outside_pad_length_mm':.44971,'reason':'U1の0.5mmピッチ・0.3mm幅パッドから短辺中央に引き出すため。パッド外約0.45mmで0.5mmへ拡幅。','human_review':'未判定'},ensure_ascii=False,indent=2),encoding='utf-8')
s0=read(B,'summary');s1=read(A,'summary');u0=read(B,'unique_lengths');u1=read(A,'unique_lengths');comparison={'before':s0,'after':s1,'total_reduction_mm':round(s0['total_track_mm']-s1['total_track_mm'],5),'reduction_percent':round(100*(1-s1['total_track_mm']/s0['total_track_mm']),2),'duplicate_excess_before_mm':sum(r['coincident_excess_mm'] for r in u0),'duplicate_excess_after_mm':sum(r['coincident_excess_mm'] for r in u1),'non_GND_detour_pairs_before':sum(r['net']!='GND' for r in read(B,'detours')),'non_GND_detour_pairs_after':sum(r['net']!='GND' for r in read(A,'detours'))}
(R/'quality_comparison.json').write_text(json.dumps(comparison,ensure_ascii=False,indent=2),encoding='utf-8')
(R/'.gitignore').write_text('candidate/\nchecks/*.kicad_pcb\n**/__pycache__/\n*.kicad_prl\nbefore/*.kicad_prl\nafter/*.kicad_prl\n',encoding='utf-8')
# Keep concise command output, including failures; omit repeated SWIG destruction warnings.
lines=[]
for p in sorted((R/'checks').glob('*.txt')):
 text=p.read_text(encoding='utf-8-sig',errors='replace');kept=[s for s in text.splitlines() if 'swig/python detected a memory leak' not in s]
 lines.append('## '+p.name+'\n\n```text\n'+'\n'.join(kept)+'\n```\n')
(R/'command_log.md').write_text('# 実行結果と再試行\n\nKiCad 10.0.8 Pythonの終了時に反復出力されたSWIG警告は省略した。失敗・例外・DRC結果は保持する。各候補は合格まで作業PCBへ反映しなかった。\n\n'+'\n'.join(lines),encoding='utf-8')
print(json.dumps({k:v for k,v in comparison.items() if k not in ['before','after']},indent=2))
