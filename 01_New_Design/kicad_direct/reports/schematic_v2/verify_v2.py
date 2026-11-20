"""Read-only design verification; reports are written only beneath this directory."""
from pathlib import Path
import sys,copy,json,hashlib,re,subprocess,math,csv
import xml.etree.ElementTree as ET
H=Path(__file__).resolve().parent;R=H.parents[1];REPO=R.parents[1]
sys.path.insert(0,str(R/'scripts'))
from sexpr import *
prov=json.loads((H/'provenance.json').read_text());BASE=prov['baseline']
sha=lambda b:hashlib.sha256(b).hexdigest()
docs={'V0':parse((H/'before/a2_usb_uart.kicad_sch').read_text(encoding='utf-8-sig')),
      'V1':parse((H/'v1_reference/a2_usb_uart.kicad_sch').read_text(encoding='utf-8-sig')),
      'V2':parse((R/'a2_usb_uart.kicad_sch').read_text(encoding='utf-8-sig'))}
def immutable(s):
 out={}
 for o in children(s,'symbol'):
  o=copy.deepcopy(o);ref=one(o,'property')[2]
  o[:]=[x for x in o if not isinstance(x,list) or x[0]!='at']
  for prop in children(o,'property'):prop[:]=[x for x in prop if not isinstance(x,list) or x[0] not in ['at','effects']]
  out[ref]=o
 return out
norm=lambda x:re.sub(rb'<date>.*?</date>',b'<date>EXPORT_TIMESTAMP_ONLY</date>',x,count=1)
raw=[(H/f'{d}/netlist.xml').read_bytes() for d in ['before','after']]
normal=[norm(x) for x in raw]
for d,b in zip(['before','after'],normal):(H/d/'netlist.normalized.xml').write_bytes(b)
xmls={v:ET.parse(H/d/'netlist.xml').getroot() for v,d in [('V0','before'),('V1','v1_reference'),('V2','after')]}
def structural(e):
 # Entire component, library and net sections retained. Only design export metadata is outside these sections.
 return {key:ET.tostring(e.find(key),encoding='unicode') for key in ['components','libparts','libraries','nets']}
erc={}
for v,d in [('V0','before'),('V1','v1_reference'),('V2','after')]:
 e=json.loads((H/d/'erc.json').read_text(encoding='utf-8-sig'))
 violations=[x for sh in e['sheets'] for x in sh['violations']]
 erc[v]={'errors':sum(x['severity']=='error' for x in violations),'warnings':sum(x['severity']=='warning' for x in violations),'total':len(violations)}
base_bytes=subprocess.check_output(['git','show',BASE+':01_New_Design/kicad_direct/a2_usb_uart.kicad_sch'],cwd=REPO)
reference=json.loads((H/'v1_reference/provenance.json').read_text())
assert all(sha((H/'v1_reference'/name).read_bytes())==item['sha256'] for name,item in reference['files'].items())
assert base_bytes==(H/'before/a2_usb_uart.kicad_sch').read_bytes()
protected=[]
entries=subprocess.check_output(['git','ls-tree','-r',BASE,'--','01_New_Design/kicad_direct'],cwd=REPO,text=True).splitlines()
for line in entries:
 info,path=line.split('\t',1);blob=info.split()[2]
 if path.endswith('/a2_usb_uart.kicad_sch'):continue
 now=subprocess.check_output(['git','hash-object','--path='+path,path],cwd=REPO,text=True).strip()
 protected.append({'path':path,'base_git_blob':blob,'current_git_blob':now,'equal':blob==now})
with (H/'protected_files.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.DictWriter(f,fieldnames=list(protected[0]));w.writeheader();w.writerows(protected)
changed=subprocess.check_output(['git','diff','--name-only',BASE,'--'],cwd=REPO,text=True).splitlines()
outside=[x for x in changed if x!='01_New_Design/kicad_direct/a2_usb_uart.kicad_sch' and not x.startswith('01_New_Design/kicad_direct/reports/schematic_v2/')]
result={'base_commit':BASE,'v0_snapshot_byte_identical':True,'full_v0_v2_xml_equal_except_design_date':normal[0]==normal[1],
 'normalized_sha256':[sha(b) for b in normal],
 'v0_v1_v2_components_libparts_libraries_nets_equal':all(structural(xmls['V0'])==structural(x) for x in xmls.values()),
 'net_count':len(xmls['V0'].findall('nets/net')),'terminal_count':len(xmls['V0'].findall('nets/net/node')),'components':len(xmls['V0'].findall('components/comp')),
 'immutable_symbols_equal_all_versions':all(immutable(docs['V0'])==immutable(x) for x in docs.values()),
 'embedded_libraries_equal_all_versions':all(one(docs['V0'],'lib_symbols')==one(x,'lib_symbols') for x in docs.values()),
 'root_uuid_equal_all_versions':all(one(docs['V0'],'uuid')==one(x,'uuid') for x in docs.values()),
 'existing_a2_files_checked':len(protected),'protected_file_differences':[x['path'] for x in protected if not x['equal']],
 'tracked_changes_outside_authorized_paths':outside,'erc':erc,
 'erc_settings_unchanged':all(json.loads((H/d/'erc.json').read_text(encoding='utf-8-sig'))['ignored_checks']==json.loads((H/'before/erc.json').read_text(encoding='utf-8-sig'))['ignored_checks'] for d in ['after','v1_reference']),
 'v0_source_sha256':sha(base_bytes),'v2_source_sha256':sha((R/'a2_usb_uart.kicad_sch').read_bytes())}
for v,d in [('V0','before'),('V2','after')]:
 assert (H/d/'source_sha256.txt').read_text().strip()==result[v.lower()+'_source_sha256'], 'Exports are stale relative to the schematic'
# Wire-only reachability: count neither labels nor the internal electrical path through components.
def graph(s):
 libs={x[1]:x for x in children(one(s,'lib_symbols'),'symbol')};pins={}
 for o in children(s,'symbol'):
  ref=one(o,'property')[2];x,y,a=map(float,one(o,'at')[1:]);t=math.radians(a)
  for unit in children(libs[one(o,'lib_id')[1]],'symbol'):
   for pin in children(unit,'pin'):
    dx,dy,_=map(float,one(pin,'at')[1:])
    pins[ref+'.'+str(one(pin,'number')[1])]=(round(x+dx*math.cos(t)-dy*math.sin(t),4),round(y-dx*math.sin(t)-dy*math.cos(t),4))
 edges=[tuple(tuple(map(float,p[1:])) for p in one(w,'pts')[1:]) for w in children(s,'wire')]
 points=set(pins.values())|{p for e in edges for p in e}
 parent={q:q for q in points}
 def find(x):
  while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
  return x
 for a,b in edges:
  dx=b[0]-a[0];dy=b[1]-a[1];l=dx*dx+dy*dy
  on=[q for q in points if abs((q[0]-a[0])*dy-(q[1]-a[1])*dx)<1e-4 and -1e-4<=(q[0]-a[0])*dx+(q[1]-a[1])*dy<=l+1e-4]
  for q in on:parent[find(q)]=find(a)
 return lambda a,b:find(pins[a])==find(pins[b])
pairs=[
 ('USB D- connector to ESD','J1.2','D1.2'),('USB D+ connector to bridge','J1.3','U1.7'),
 ('Crystal input to bridge','Y1.1','U1.1'),('Crystal to load cap','Y1.1','C13.1'),
 ('RESET RC to bridge','R2.2','U1.34'),('REF resistor to bridge','R1.1','U1.5'),
 ('Internal 1.8 V capacitor','U1.37','C7.1'),('VPHY filter to capacitors','FB1.2','C11.1'),('VPHY to bridge','C11.1','U1.3'),
 ('3V3 bank to bridge','C3.1','U1.12'),('TXD bridge to translator','U1.13','U2.4'),
 ('RXD bridge to translator','U1.14','U2.6'),('RTS bridge to translator','U1.15','U2.5'),('CTS bridge to translator','U1.16','U2.7'),
 ('Translator VCCA capacitor','U2.1','C16.1'),('Translator VCCB capacitor','U2.16','C17.1'),
 ('Translator DIR tie','U2.1','U2.2'),('Translator OE pair','U2.14','U2.15'),
 ('RXD pull-up','R11.2','U2.11'),('CTS pull-up','R12.2','U2.10'),
 ('RTS to header','U2.12','J3.1'),('CTS to header','U2.10','J3.2'),
 ('EEPROM VCC capacitor','U5.8','C15.1'),('EEPROM pull-up VCC','R3.1','U5.8'),('EEPROM DO series resistor','U5.4','R4.1'),
 ('LED current resistor','R14.2','D3.2'),('Inverter gate bias','R5.2','Q1.1'),('Inverter drain bias','R6.2','Q1.3'),
 ('Inverter to regulator enable','Q1.3','U4.3'),('LDO feedback','U4.4','R7.2'),
 ('Selector common to divider ground','SW1.3','R8.2'),('Selector resistor','R9.2','SW1.2'),
 ('Load switch QOD','U6.5','R16.1'),('QOD resistor output','R16.2','U6.6'),
 ('Load switch to SW2','U6.6','SW2.3')]
graphs={v:graph(s) for v,s in docs.items()}
connections=[{'relationship':name,'from':a,'to':b,**{v:fn(a,b) for v,fn in graphs.items()}} for name,a,b in pairs]
(H/'wire_visibility.json').write_text(json.dumps(connections,indent=2))
stats={v:{k:len(children(s,k)) for k in ['symbol','wire','label','junction','bus','bus_entry','no_connect']} for v,s in docs.items()}
for v in stats:stats[v]['selected_wire_only_relationships']=sum(x[v] for x in connections)
(H/'drawing_comparison.json').write_text(json.dumps(stats,indent=2))
(H/'comparison.json').write_text(json.dumps(result,indent=2))
assert result['full_v0_v2_xml_equal_except_design_date']
assert result['v0_v1_v2_components_libparts_libraries_nets_equal']
assert result['immutable_symbols_equal_all_versions'] and result['embedded_libraries_equal_all_versions'] and result['root_uuid_equal_all_versions']
assert not result['protected_file_differences'] and not outside
assert all(x['total']==0 for x in erc.values()) and result['erc_settings_unchanged']
manifest=json.loads((H/'after/export_manifest.json').read_text())
assert manifest['source_sha256']==result['v2_source_sha256']
assert all(sha((H/'after'/name).read_bytes())==value for name,value in manifest['outputs_sha256'].items()), 'Export files changed after generation'
print(json.dumps(result,indent=2));print(json.dumps(stats,indent=2))
