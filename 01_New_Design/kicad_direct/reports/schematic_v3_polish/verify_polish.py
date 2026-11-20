"""Validate polish against the exact V3-refine baseline; presentation and electrical checks are separate."""
from pathlib import Path
import sys,json,hashlib,copy,subprocess,csv,math
from collections import Counter
import xml.etree.ElementTree as ET
H=Path(__file__).resolve().parent;R=H.parents[1];REPO=R.parents[1];BASE='6654fae9168145beb779b06f72582182a3117050'
sys.path.insert(0,str(R/'scripts'));from sexpr import *
sha=lambda b:hashlib.sha256(b).hexdigest()
a=parse((H/'before/a2_usb_uart.kicad_sch').read_text(encoding='utf-8-sig'));b=parse((R/'a2_usb_uart.kicad_sch').read_text(encoding='utf-8-sig'))
objects=lambda s:{str(one(o,'property')[2]):o for o in children(s,'symbol')}
A,B=objects(a),objects(b)
def immutable(s):
 out={}
 for ref,o in objects(s).items():
  c=copy.deepcopy(o);c[:]=[x for x in c if not isinstance(x,list) or x[0]!='at']
  for pp in children(c,'property'):pp[:]=[x for x in pp if not isinstance(x,list) or x[0] not in ['at','effects']]
  out[ref]=c
 return out
ai,bi=immutable(a),immutable(b)
x={d:ET.parse(H/d/'netlist.xml').getroot() for d in ['before','after']}
def pins(e):return {(n.get('ref'),n.get('pin')):v.get('name') for v in e.findall('nets/net') for n in v.findall('node')}
def comps(e):return {v.get('ref'):ET.tostring(v,encoding='unicode') for v in e.findall('components/comp')}
pa,pb=pins(x['before']),pins(x['after']);ca,cb=comps(x['before']),comps(x['after'])
partition=lambda pp:sorted(sorted(k for k in pp if pp[k]==v) for v in set(pp.values()))
erc={}
for ver in ['before','after']:
 e=json.loads((H/ver/'erc.json').read_text(encoding='utf-8-sig'));vs=[v for sh in e['sheets'] for v in sh['violations']]
 erc[ver]={'errors':sum(v['severity']=='error' for v in vs),'warnings':sum(v['severity']=='warning' for v in vs),'ignored_checks':e['ignored_checks']}
fresh=ET.parse(H/'before/netlist_fresh.xml').getroot();fe=json.loads((H/'before/erc_fresh.json').read_text(encoding='utf-8-sig'))
allowed={'01_New_Design/kicad_direct/a2_usb_uart.kicad_sch'};prefix='01_New_Design/kicad_direct/reports/schematic_v3_polish/'
protected=[]
for line in subprocess.check_output(['git','ls-tree','-r',BASE],cwd=REPO,text=True).splitlines():
 info,path=line.split('\t',1)
 if path in allowed:continue
 blob=info.split()[2];now=subprocess.check_output(['git','hash-object','--path='+path,path],cwd=REPO,text=True).strip();protected.append({'path':path,'base_blob':blob,'current_blob':now,'equal':blob==now})
with (H/'protected_files.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(protected[0]));w.writeheader();w.writerows(protected)
changed=subprocess.check_output(['git','diff','--name-only',BASE],cwd=REPO,text=True).splitlines();untracked=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=REPO,text=True).splitlines()
basebytes=subprocess.check_output(['git','show',BASE+':01_New_Design/kicad_direct/a2_usb_uart.kicad_sch'],cwd=REPO)
P=json.loads((H/'patch_manifest.json').read_text());D=json.loads((R/'reports/schematic_v3_refine/patch_manifest.json').read_text());beforeP=D['pins'];afterP=P['pins']
coord=lambda o:tuple(round(float(v)/1.27,6) for v in one(o,'at')[1:3])
wire=lambda a1,b1:any({tuple(a1),tuple(b1)}=={tuple(u),tuple(v)} for u,v,n in P['classified_wires'])
capcheck=[]
for r in sorted(k for k in ca if k.startswith('C')):
 o=B[r];p1=afterP[r+'.1'];p2=afterP[r+'.2'];end=(p2[0],p2[1]+1)
 fields={str(q[1]):q for q in children(o,'property')};rf,vf=fields['Reference'],fields['Value'];at1=one(rf,'at');at2=one(vf,'at')
 capcheck.append({'reference':r,'angle_deg':float(one(o,'at')[3]),'vertical_top_power_bottom_GND':p1[0]==p2[0] and p1[1]<p2[1] and pb[(r,'2')]=='GND' and pb[(r,'1')]!='GND','ground_symbol_below':any(k.startswith('#PWR') and str(children(t,'property')[1][2])=='GND' and coord(t)==end for k,t in B.items()),'short_ground_wire_1_27mm':wire(p2,end),'fields_horizontal':float(at1[3])==0 and float(at2[3])==0,'reference_above_value_same_x':at1[1]==at2[1] and float(at1[2])<float(at2[2]),'field_anchor_offset_x_mm':round(abs(float(at1[1])-float(one(o,'at')[1])),3),'symbol_xy_grid':coord(o),'reference_xy_grid':coord(rf),'value_xy_grid':coord(vf)})
(H/'capacitor_orientation_check.json').write_text(json.dumps(capcheck,indent=2))
with (H/'capacitor_orientation_check.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(capcheck[0]));w.writeheader();w.writerows(capcheck)
fieldcheck=[]
for r in sorted(ca):
 o=B[r];q={str(t[1]):t for t in children(o,'property')};rf,vf=q['Reference'],q['Value'];at=one(o,'at');ra,va=one(rf,'at'),one(vf,'at')
 fieldcheck.append({'reference':r,'value':str(vf[2]),'reference_xy_mm':list(map(float,ra[1:3])),'value_xy_mm':list(map(float,va[1:3])),'same_x_reference_above_value':ra[1]==va[1] and float(ra[2])<float(va[2]),'horizontal_render_orientation':all((float(one(z,'at')[3])-float(at[3]))%180==0 for z in [rf,vf]),'both_fields_visible':all(one(one(z,'effects'),'hide') is None for z in [rf,vf]),'distance_from_symbol_origin_mm':{'Reference':round(math.dist(list(map(float,at[1:3])),list(map(float,ra[1:3]))),3),'Value':round(math.dist(list(map(float,at[1:3])),list(map(float,va[1:3]))),3)},'assessment':'Coordinate audit only; visual association and overlap assessed separately in visual_review.json.'})
(H/'component_field_check.json').write_text(json.dumps(fieldcheck,ensure_ascii=False,indent=2),encoding='utf-8')
labels=children(b,'label');counts=Counter(str(o[1]) for o in labels);labelaudit=[]
for o in labels:
 q=coord(o);ends=sum(q in [tuple(u),tuple(v)] for u,v,n in P['classified_wires']);labelaudit.append({'net':str(o[1]),'xy_grid':q,'remote':counts[str(o[1])]>1,'coincident_pin':any(tuple(v)==q for v in afterP.values()),'wire_ends':ends})
(H/'label_audit.json').write_text(json.dumps(labelaudit,indent=2))
keepnets={'USB_D+','USB_D-','XTAL_IN','XTAL_OUT','FT_TXD','FT_RXD','FT_RTS_N','FT_CTS_N','TXD','RXD','RTS_N','CTS_N'}
edges=lambda data:sorted((u,v,n) for u,v,n in data if n in keepnets)
manifest=json.loads((H/'after/export_manifest.json').read_text());bm=json.loads((H/'before/export_manifest.json').read_text())
checks={'baseline_byte_identical':basebytes==(H/'before/a2_usb_uart.kicad_sch').read_bytes(),'component_XML_attributes_exactly_equal':ca==cb,'all_real_terminal_net_names_equal':pa==pb,'net_partitions_equal':partition(pa)==partition(pb),'all_real_component_attributes_and_UUIDs_preserved':{k:v for k,v in ai.items() if not k.startswith('#')}=={k:v for k,v in bi.items() if not k.startswith('#')},'remaining_symbol_attributes_and_UUIDs_preserved':all(v==ai.get(k) for k,v in bi.items()),'only_two_redundant_power_symbols_removed':set(ai)-set(bi)=={'#PWR0171','#PWR0173'} and not(set(bi)-set(ai)),'all_embedded_symbol_definitions_and_pin_semantics_exactly_equal':one(a,'lib_symbols')==one(b,'lib_symbols'),'no_connect_markers_unchanged':children(a,'no_connect')==children(b,'no_connect'),'root_UUID_preserved':one(a,'uuid')==one(b,'uuid'),'all_non_capacitor_real_component_positions_unchanged':all(one(A[r],'at')==one(B[r],'at') for r in ca if not r.startswith('C')),'USB_XTAL_UART_wire_geometry_preserved':edges(D['classified_wires'])==edges(P['classified_wires']),'D1_ground_lead_preserved':beforeP['D1.3']==afterP['D1.3'] and wire(afterP['D1.3'],[afterP['D1.3'][0],afterP['D1.3'][1]+1]),'all_capacitors_vertical':all(float(v['angle_deg'])==0 and v['vertical_top_power_bottom_GND'] for v in capcheck),'all_capacitor_GND_below_with_short_lead':all(v['ground_symbol_below'] and v['short_ground_wire_1_27mm'] for v in capcheck),'all_capacitor_fields_horizontal_and_nearby':all(v['fields_horizontal'] and v['reference_above_value_same_x'] and v['field_anchor_offset_x_mm']==2.54 for v in capcheck),'all_real_component_fields_visible_horizontal_ref_above_value':all(v['same_x_reference_above_value'] and v['horizontal_render_orientation'] and v['both_fields_visible'] for v in fieldcheck),'remote_labels_at_free_wire_end':all(not v['coincident_pin'] and v['wire_ends']==1 for v in labelaudit if v['remote']),'all_labels_off_pins':all(not v['coincident_pin'] for v in labelaudit),'ERC_no_errors_or_warnings':not any(erc[d][k] for d in erc for k in ['errors','warnings']),'ERC_settings_unchanged':erc['before']['ignored_checks']==erc['after']['ignored_checks'],'baseline_fresh_XML_equal':pins(fresh)==pa and comps(fresh)==ca,'baseline_fresh_ERC_zero_and_settings_equal':not any(sh['violations'] for sh in fe['sheets']) and fe['ignored_checks']==erc['before']['ignored_checks'],'protected_files_unchanged':all(x['equal'] for x in protected),'changes_within_scope':all(p in allowed or p.startswith(prefix) for p in set(changed+untracked)),'baseline_exports_match_manifest':bm['source_sha256']==sha(basebytes) and all(sha((H/'before'/n).read_bytes())==v for n,v in bm['outputs_sha256'].items()),'final_exports_match_manifest':manifest['source_sha256']==sha((R/'a2_usb_uart.kicad_sch').read_bytes()) and all(sha((H/'after'/n).read_bytes())==v for n,v in manifest['outputs_sha256'].items())}
result={'base':BASE,'checks':checks,'real_components':len(ca),'terminals':len(pa),'nets_before':len(set(pa.values())),'nets_after':len(set(pb.values())),'capacitors':len(capcheck),'horizontal_capacitors_before':sum(float(one(A[r],'at')[3])%180!=0 for r in ca if r.startswith('C')),'horizontal_capacitors_after':sum(float(one(B[r],'at')[3])%180!=0 for r in ca if r.startswith('C')),'protected_file_count':len(protected),'protected_file_differences':[x['path'] for x in protected if not x['equal']],'pin_differences':[{'reference':k[0],'pin':k[1],'before':v,'after':pb.get(k)} for k,v in pa.items() if pb.get(k)!=v],'ERC':erc,'source_sha256':manifest['source_sha256'],'removed_display_symbols':P['removed_redundant_power_symbols'],'user_review_approved':False,'manufacturing_approved':False}
(H/'comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
with (H/'terminal_net_comparison.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.writer(f);w.writerow(['reference','pin','refine_net','polish_net','equal'])
 for k,v in sorted(pa.items()):w.writerow([*k,v,pb.get(k),v==pb.get(k)])
with (H/'component_attribute_comparison.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.writer(f);w.writerow(['reference','value','footprint','MPN','all_fixed_instance_attributes_equal','complete_XML_equal'])
 for r in sorted(ca):
  props={str(p[1]):str(p[2]) for p in children(B[r],'property')};w.writerow([r,props.get('Value'),props.get('Footprint'),props.get('MPN'),ai[r]==bi[r],ca[r]==cb[r]])
# All dimensions below are on the schematic paper; they are not PCB routing lengths.
capmap={'C1':'U3.1','C2':'U3.5','C3':'U1.12','C4':'U1.24','C5':'U1.39','C6':'U1.46','C7':'U1.37','C8':'U1.38','C9':'U1.3','C10':'U1.8','C11':'U1.3','C12':'U1.8','C15':'U5.8','C16':'U2.1','C17':'U2.16','C18':'U4.1','C19':'U4.5','C20':'U6.1','C21':'U6.6'}
metrics={'unit':'mm on schematic paper; not PCB','pin_to_pin_straight_line_distance':[{'capacitor':c,'IC_pin':k,'refine':round(math.dist(beforeP[c+'.1'],beforeP[k])*1.27,2),'polish':round(math.dist(afterP[c+'.1'],afterP[k])*1.27,2)} for c,k in capmap.items()],'drawing_objects':{v:{k:len(children(s,k)) for k in ['symbol','label','wire','junction','bus']} for v,s in [('refine',a),('polish',b)]},'retained_wire_UUIDs':P['retained_wire_uuids']}
(H/'drawing_metrics.json').write_text(json.dumps(metrics,indent=2))
print(json.dumps(result,ensure_ascii=False,indent=2));assert all(checks.values()),[k for k,v in checks.items() if not v]
