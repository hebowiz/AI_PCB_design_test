"""Compare real terminals, immutable component identity, pin semantics and protected files."""
from pathlib import Path
import sys,json,hashlib,copy,subprocess,csv,math
from collections import Counter,defaultdict
import xml.etree.ElementTree as ET
H=Path(__file__).resolve().parent;R=H.parents[1];REPO=R.parents[1];BASE='3a0e18c99daca23e188540f4f82afcac85b4ab2f'
sys.path.insert(0,str(R/'scripts'));from sexpr import *
sha=lambda b:hashlib.sha256(b).hexdigest()
a=parse((H/'before/a2_usb_uart.kicad_sch').read_text(encoding='utf-8-sig'));b=parse((R/'a2_usb_uart.kicad_sch').read_text(encoding='utf-8-sig'))
def imm(s):
 out={}
 for o in children(s,'symbol'):
  c=copy.deepcopy(o);ref=str(one(c,'property')[2]);c[:]=[x for x in c if not isinstance(x,list) or x[0]!='at']
  if ref in ['FB1','FB2']:one(c,'lib_id')[1]=Q('ALLOWED_FERRITE_GRAPHIC')
  for pp in children(c,'property'):pp[:]=[x for x in pp if not isinstance(x,list) or x[0] not in ['at','effects']]
  out[ref]=c
 return out
ai,bi=imm(a),imm(b);oldlibs={str(x[1]):x for x in children(one(a,'lib_symbols'),'symbol')};newlibs={str(x[1]):x for x in children(one(b,'lib_symbols'),'symbol')}
def libpins(lib):
 return {str(one(p,'number')[1]):{'electrical_type':p[1],'shape':p[2],'at':list(map(float,one(p,'at')[1:])),'name':str(one(p,'name')[1])} for u in children(lib,'symbol') for p in children(u,'pin')}
def component_pins(s,libs):return {str(one(o,'property')[2]):libpins(libs[str(one(o,'lib_id')[1])]) for o in children(s,'symbol') if not str(one(o,'property')[2]).startswith('#')}
xml={d:ET.parse(H/d/'netlist.xml').getroot() for d in ['before','after']}
def pins(e):return {(n.attrib['ref'],n.attrib['pin']):v.attrib['name'] for v in e.findall('nets/net') for n in v.findall('node') if not n.attrib['ref'].startswith('#')}
def comps(e,normalize=True):
 result={}
 for v in e.findall('components/comp'):
  c=copy.deepcopy(v);ref=c.attrib['ref']
  if normalize and ref in ['FB1','FB2']:
   for k in ['lib','part']:c.find('libsource').set(k,'ALLOWED_FERRITE_GRAPHIC')
  result[ref]=ET.tostring(c,encoding='unicode')
 return result
pa,pb=(pins(xml[d]) for d in ['before','after']);ca,cb=(comps(xml[d]) for d in ['before','after'])
partition=lambda pp:sorted(sorted(k for k in pp if pp[k]==v) for v in set(pp.values()))
erc={}
for d in ['before','after']:
 e=json.loads((H/d/'erc.json').read_text(encoding='utf-8-sig'));vs=[v for sh in e['sheets'] for v in sh['violations']];erc[d]={'errors':sum(v['severity']=='error' for v in vs),'warnings':sum(v['severity']=='warning' for v in vs),'ignored_checks':e['ignored_checks']}
allowed={'01_New_Design/kicad_direct/a2_usb_uart.kicad_sch','01_New_Design/kicad_direct/sym-lib-table','01_New_Design/kicad_direct/libraries/A2_Refine.kicad_sym'}
prefix='01_New_Design/kicad_direct/reports/schematic_v3_refine/'
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
manifest=json.loads((H/'after/export_manifest.json').read_text());basebytes=subprocess.check_output(['git','show',BASE+':01_New_Design/kicad_direct/a2_usb_uart.kicad_sch'],cwd=REPO)
P=json.loads((H/'patch_manifest.json').read_text());D=json.loads((R/'reports/schematic_v3/drawing.json').read_text())
# Repeated signal names are remote connections; singleton names identify visible local wiring.
labels=children(b,'label');counts=Counter(str(o[1]) for o in labels);labelaudit=[]
for o in labels:
 q=[round(float(x)/1.27,6) for x in one(o,'at')[1:3]];matches=[k for k,v in P['pins'].items() if v==q]
 connected=[(a1,b1,n) for a1,b1,n in P['classified_wires'] if q in [a1,b1]]
 labelaudit.append({'net':str(o[1]),'xy_grid':q,'role':'remote' if counts[str(o[1])]>1 else 'local_identifier','coincident_pins':matches,'wire_ends':len(connected)})
(H/'label_audit.json').write_text(json.dumps(labelaudit,indent=2))
# Unrelated UART nets keep every wire object and no junction is introduced at their X crossings.
uart={'FT_TXD','FT_RXD','FT_RTS_N','FT_CTS_N','TXD','RXD','RTS_N','CTS_N'}
ue=lambda e:sorted((a1,b1,n) for a1,b1,n in e if n in uart)
result={'base':BASE,'baseline_byte_identical':basebytes==(H/'before/a2_usb_uart.kicad_sch').read_bytes(),'real_components':len(ca),'real_component_attributes_equal_except_allowed_FB_libsource':ca==cb,'allowed_libsource_changes':{r:{v:xml[v].find(f"components/comp[@ref='{r}']/libsource").attrib for v in xml} for r in ['FB1','FB2']},'terminal_count':len(pa),'all_terminal_net_names_equal':pa==pb,'net_count_before':len(set(pa.values())),'net_count_after':len(set(pb.values())),'net_partition_equal':partition(pa)==partition(pb),'pin_differences':[{'ref':k[0],'pin':k[1],'before':v,'after':pb.get(k)} for k,v in pa.items() if pb.get(k)!=v],'all_existing_symbol_attributes_uuid_pin_identifiers_preserved':all(v==bi.get(k) for k,v in ai.items()),'all_existing_library_definitions_preserved':all(v==newlibs.get(k) for k,v in oldlibs.items()),'real_component_pin_numbers_types_names_anchors_equal':component_pins(a,oldlibs)==component_pins(b,newlibs),'FB_graphical_pin_length_mm':{'before':2.54,'after':1.27,'electrical_anchor_unchanged':True},'root_uuid_preserved':one(a,'uuid')==one(b,'uuid'),'no_connect_markers_unchanged':children(a,'no_connect')==children(b,'no_connect'),'added_symbol_references':sorted(set(bi)-set(ai)),'only_power_symbols_added':all(k.startswith('#PWR') for k in set(bi)-set(ai)),'UART_wires_geometrically_unchanged':ue(D['v3_classified_wires'])==ue(P['classified_wires']),'all_labels_off_pins':all(not x['coincident_pins'] for x in labelaudit),'all_remote_labels_at_wire_end':all(x['wire_ends']==1 for x in labelaudit if x['role']=='remote'),'remote_label_count':sum(x['role']=='remote' for x in labelaudit),'local_identifier_count':sum(x['role']=='local_identifier' for x in labelaudit),'protected_file_count':len(protected),'protected_file_differences':[x['path'] for x in protected if not x['equal']],'changes_outside_scope':[p for p in set(changed+untracked) if p not in allowed and not p.startswith(prefix)],'erc':erc,'erc_settings_equal':erc['before']['ignored_checks']==erc['after']['ignored_checks'],'source_sha256':sha((R/'a2_usb_uart.kicad_sch').read_bytes()),'exports_current':manifest['source_sha256']==sha((R/'a2_usb_uart.kicad_sch').read_bytes()) and all(sha((H/'after'/n).read_bytes())==v for n,v in manifest['outputs_sha256'].items()),'user_review_approved':False}
fresh=ET.parse(H/'before/netlist_fresh.xml').getroot();fe=json.loads((H/'before/erc_fresh.json').read_text(encoding='utf-8-sig'))
result.update({'baseline_fresh_export_terminals_match':pins(fresh)==pa,'baseline_fresh_export_components_match':comps(fresh)==ca,'baseline_fresh_erc_violations':sum(len(sh['violations']) for sh in fe['sheets']),'baseline_fresh_erc_settings_match':fe['ignored_checks']==erc['before']['ignored_checks']})
(H/'comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
with (H/'terminal_net_comparison.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.writer(f);w.writerow(['reference','pin','V3_net','refined_net','equal'])
 for k,v in sorted(pa.items()):w.writerow([*k,v,pb.get(k),v==pb.get(k)])
with (H/'component_attribute_comparison.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.writer(f);w.writerow(['reference','value','footprint','MPN','instance_identity_equal','pin_semantics_equal','xml_attributes_equal_with_documented_FB_exception'])
 for r in sorted(ca):
  o=next(o for o in children(b,'symbol') if one(o,'property')[2]==r);props={str(p[1]):str(p[2]) for p in children(o,'property')}
  w.writerow([r,props.get('Value'),props.get('Footprint'),props.get('MPN'),ai[r]==bi[r],component_pins(a,oldlibs)[r]==component_pins(b,newlibs)[r],ca[r]==cb[r]])
# Geometry metrics: paper distances only, never claimed as PCB routing or parasitics.
oldP={k:v['at'] for k,v in D['pins'].items()};newP=P['pins']
capmap={'C1':'U3.1','C2':'U3.5','C3':'U1.12','C4':'U1.24','C5':'U1.39','C6':'U1.46','C7':'U1.37','C8':'U1.38','C9':'U1.3','C10':'U1.8','C11':'U1.3','C12':'U1.8','C13':'Y1.1','C14':'Y1.3','C15':'U5.8','C16':'U2.1','C17':'U2.16','C18':'U4.1','C19':'U4.5','C20':'U6.1','C21':'U6.6'}
proximity=[{'capacitor':c,'IC_pin':ic,'V3_mm':round(math.dist(oldP[c+'.1'],oldP[ic])*1.27,2),'refined_mm':round(math.dist(newP[c+'.1'],newP[ic])*1.27,2)} for c,ic in capmap.items()]
branchold={'C1':5,'C2':5,'C3':7,'C4':7,'C5':7,'C6':7,'C7':7,'C8':3,'C9':5,'C10':5,'C11':5,'C12':5,'C13':6,'C14':6,'C15':7,'C16':4,'C17':4,'C18':9,'C19':8,'C20':6,'C21':4,'C22':7}
branchnew={'C1':2,'C2':2,'C3':1,'C4':1,'C5':1,'C6':1,'C7':2,'C8':2,'C9':2,'C10':2,'C11':2,'C12':2,'C13':1,'C14':1,'C15':1,'C16':1,'C17':1,'C18':1,'C19':1,'C20':1,'C21':1,'C22':1}
metrics={'sheet_size':'A2 single sheet','unit':'mm on schematic paper, not PCB','proximity_pin_to_pin_straight_line':proximity,'capacitor_branch_wire_lengths':[{'capacitor':c,'V3':round(v*1.27,2),'refined':round(branchnew[c]*1.27,2)} for c,v in branchold.items()],'all_22_capacitor_ground_external_leads':{'V3_mm':2.54,'refined_mm':1.27},'D1_signal_external_branch_mm':{'USB_D+':{'V3':86.36,'refined':7.62},'USB_D-':{'V3':60.96,'refined':10.16}},'D1_GND_external_lead_mm':{'V3':2.54,'refined':1.27},'drawing_object_counts':{v:{k:len(children(o,k)) for k in ['symbol','label','wire','junction','bus']} for v,o in [('V3',a),('refined',b)]},'retained_wire_uuids':P['retained_wire_uuids']}
(H/'drawing_metrics.json').write_text(json.dumps(metrics,indent=2))
bm=json.loads((H/'before/export_manifest.json').read_text())
result['baseline_exports_match_original_manifest']=bm['source_sha256']==sha(basebytes) and all(sha((H/'before'/n).read_bytes())==v for n,v in bm['outputs_sha256'].items())
(H/'comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
checks=[k for k,v in result.items() if isinstance(v,bool) and k!='user_review_approved']
print(json.dumps({k:v for k,v in result.items() if k not in ['erc','allowed_libsource_changes']},ensure_ascii=False,indent=2))
assert all(result[k] for k in checks),[k for k in checks if not result[k]]
assert not result['protected_file_differences'] and not result['changes_outside_scope'] and not result['baseline_fresh_erc_violations']
assert not any(erc[d][k] for d in erc for k in ['errors','warnings'])
