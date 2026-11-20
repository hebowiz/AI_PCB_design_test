"""Mechanical electrical identity checks, restricted-change audit and drawing metrics."""
from pathlib import Path
import sys,json,hashlib,copy,subprocess,math,csv
import xml.etree.ElementTree as ET
H=Path(__file__).resolve().parent;R=H.parents[1];REPO=R.parents[1];BASE='89093caab59e9e6897808d0fd020dd2c689ba450'
sys.path.insert(0,str(R/'scripts'));from sexpr import *
sha=lambda b:hashlib.sha256(b).hexdigest()
a=parse((H/'before/a2_usb_uart.kicad_sch').read_text(encoding='utf-8-sig'));b=parse((R/'a2_usb_uart.kicad_sch').read_text(encoding='utf-8-sig'))
def imm(s):
 out={}
 for o in children(s,'symbol'):
  c=copy.deepcopy(o);ref=one(c,'property')[2];c[:]=[x for x in c if not isinstance(x,list) or x[0]!='at']
  for pp in children(c,'property'):pp[:]=[x for x in pp if not isinstance(x,list) or x[0] not in ['at','effects']]
  out[ref]=c
 return out
ai,bi=imm(a),imm(b);oldlibs={x[1]:x for x in children(one(a,'lib_symbols'),'symbol')};newlibs={x[1]:x for x in children(one(b,'lib_symbols'),'symbol')}
xml={d:ET.parse(H/d/'netlist.xml').getroot() for d in ['before','after']}
def pins(e):return {(n.attrib['ref'],n.attrib['pin']):v.attrib['name'].removeprefix('/') for v in e.findall('nets/net') for n in v.findall('node') if not n.attrib['ref'].startswith('#')}
def comps(e):return {v.attrib['ref']:ET.tostring(v,encoding='unicode') for v in e.findall('components/comp')}
pa,pb=(pins(xml[d]) for d in ['before','after']);ca,cb=(comps(xml[d]) for d in ['before','after'])
diffs=[{'ref':k[0],'pin':k[1],'before':v,'after':pb.get(k)} for k,v in pa.items() if pb.get(k)!=v]
partition=lambda pp:sorted(sorted(k for k in pp if pp[k]==v) for v in set(pp.values()))
erc={}
for d in ['before','after']:
 e=json.loads((H/d/'erc.json').read_text(encoding='utf-8-sig'));vs=[v for sh in e['sheets'] for v in sh['violations']];erc[d]={'errors':sum(v['severity']=='error' for v in vs),'warnings':sum(v['severity']=='warning' for v in vs),'ignored_checks':e['ignored_checks']}
allowed={'01_New_Design/kicad_direct/a2_usb_uart.kicad_sch','01_New_Design/kicad_direct/sym-lib-table','01_New_Design/kicad_direct/libraries/A2_PowerV3.kicad_sym'}
prefix='01_New_Design/kicad_direct/reports/schematic_v3/'
protected=[]
for line in subprocess.check_output(['git','ls-tree','-r',BASE],cwd=REPO,text=True).splitlines():
 info,path=line.split('\t',1)
 if path in allowed:continue
 blob=info.split()[2];now=subprocess.check_output(['git','hash-object','--path='+path,path],cwd=REPO,text=True).strip()
 protected.append({'path':path,'base_blob':blob,'current_blob':now,'equal':blob==now})
with (H/'protected_files.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(protected[0]));w.writeheader();w.writerows(protected)
changed=subprocess.check_output(['git','diff','--name-only',BASE],cwd=REPO,text=True).splitlines()
untracked=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=REPO,text=True).splitlines()
manifest=json.loads((H/'after/export_manifest.json').read_text())
basebytes=subprocess.check_output(['git','show',BASE+':01_New_Design/kicad_direct/a2_usb_uart.kicad_sch'],cwd=REPO)
result={'base':BASE,'baseline_byte_identical':basebytes==(H/'before/a2_usb_uart.kicad_sch').read_bytes(),
 'real_components':len(ca),'component_xml_attributes_equal':ca==cb,'terminal_count':len(pa),'all_terminal_net_names_equal':pa==pb,
 'root_scope_name_normalization':'Only leading / removed: V2 root-local labels -> V3 global power names on the same single sheet.',
 'net_count_before':len(set(pa.values())),'net_count_after':len(set(pb.values())),'net_partition_equal':partition(pa)==partition(pb),'pin_differences':diffs,
 'all_existing_symbol_attributes_uuid_pin_identifiers_preserved':all(v==bi.get(k) for k,v in ai.items()),'all_existing_library_definitions_preserved':all(v==newlibs.get(k) for k,v in oldlibs.items()),
 'root_uuid_preserved':one(a,'uuid')==one(b,'uuid'),'added_symbol_references':sorted(set(bi)-set(ai)),
 'only_power_symbols_added':all(k.startswith(('#PWR','#FLG')) for k in set(bi)-set(ai)),
 'protected_file_count':len(protected),'protected_file_differences':[x['path'] for x in protected if not x['equal']],
 'changes_outside_scope':[p for p in set(changed+untracked) if p not in allowed and not p.startswith(prefix)],
 'erc':erc,'erc_settings_equal':erc['before']['ignored_checks']==erc['after']['ignored_checks'],
 'source_sha256':sha((R/'a2_usb_uart.kicad_sch').read_bytes()),'exports_current':manifest['source_sha256']==sha((R/'a2_usb_uart.kicad_sch').read_bytes()) and all(sha((H/'after'/n).read_bytes())==v for n,v in manifest['outputs_sha256'].items()),'user_review_approved':False}
(H/'comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
with (H/'terminal_net_comparison.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.writer(f);w.writerow(['reference','pin','V2_net','V3_net','equal'])
 for k,v in sorted(pa.items()):w.writerow([*k,v,pb.get(k),v==pb.get(k)])
dr=json.loads((H/'drawing.json').read_text());stats={}
for v,s,key in [('V2',a,'v2_classified_wires'),('V3',b,'v3_classified_wires')]:
 ed=dr[key];stats[v]={k:len(children(s,k)) for k in ['symbol','label','wire','junction','bus']};gg=[math.dist(x,y)*1.27 for x,y,n in ed if n=='GND'];stats[v].update({'gnd_wire_total_mm':round(sum(gg),3),'gnd_wire_max_segment_mm':round(max(gg),3),'ground_symbol_count':sum(one(o,'lib_id')[1].endswith('GND_Triangle') for o in children(s,'symbol')),'circle_power_symbols':sum(str(one(o,'lib_id')[1]).startswith('A2_PowerV3:Rail') for o in children(s,'symbol'))})
# Drawing distance is a proxy for proximity, not a PCB placement metric.
def coords(s):return {one(o,'property')[2]:tuple(map(float,one(o,'at')[1:3])) for o in children(s,'symbol')}
xy={v:coords(s) for v,s in [('V2',a),('V3',b)]}
capmap={'C1':'U3','C2':'U3',**{f'C{i}':'U1' for i in range(3,15)},'C15':'U5','C16':'U2','C17':'U2','C18':'U4','C19':'U4','C20':'U6','C21':'U6'}
proximity=[{'capacitor':c,'IC':ic,**{v:round(math.dist(pos[c],pos[ic]),2) for v,pos in xy.items()}} for c,ic in capmap.items() if c not in ['C13','C14']]
(H/'drawing_comparison.json').write_text(json.dumps({'metrics':stats,'capacitor_to_IC_origin_distance_mm':proximity,'note':'Lengths are schematic drawing lengths, not PCB routing lengths. Segment maximum depends on subdivision.'},indent=2))
fresh=ET.parse(H/'before/netlist_fresh.xml').getroot()
fe=json.loads((H/'before/erc_fresh.json').read_text(encoding='utf-8-sig'))
result['baseline_fresh_export_terminals_match']=pins(fresh)==pa
result['baseline_fresh_export_components_match']=comps(fresh)==ca
result['baseline_fresh_erc_violations']=sum(len(sh['violations']) for sh in fe['sheets'])
result['baseline_fresh_erc_settings_match']=fe['ignored_checks']==erc['before']['ignored_checks']
assert result['baseline_fresh_export_terminals_match'] and result['baseline_fresh_export_components_match']
assert result['baseline_fresh_erc_violations']==0 and result['baseline_fresh_erc_settings_match']
(H/'comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ['added_symbol_references','erc']},ensure_ascii=False,indent=2));print(json.dumps(stats,indent=2))
for k in ['baseline_byte_identical','component_xml_attributes_equal','all_terminal_net_names_equal','net_partition_equal','all_existing_symbol_attributes_uuid_pin_identifiers_preserved','all_existing_library_definitions_preserved','root_uuid_preserved','only_power_symbols_added','erc_settings_equal','exports_current']:assert result[k],k
assert not result['protected_file_differences'] and not result['changes_outside_scope']
assert not any(erc[d][k] for d in erc for k in ['errors','warnings'])
