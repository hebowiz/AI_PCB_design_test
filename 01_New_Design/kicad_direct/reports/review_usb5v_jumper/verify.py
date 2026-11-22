"""Validate only the approved R-0016 delta, footprint dimensions and drawing regression."""
from pathlib import Path
import sys,json,subprocess,hashlib,xml.etree.ElementTree as ET,itertools,datetime,os
H=Path(__file__).resolve().parent;R=H.parents[1];ROOT=R.parents[1]
sys.path.insert(0,str(R/'scripts'));from sexpr import *
BASE='fa741e9e1f7853efc5d27d3cb2c969a86abb31a1';REL='01_New_Design/kicad_direct/a2_usb_uart.kicad_sch'
def git(*a):return subprocess.check_output(['git',*a],cwd=ROOT)
def props(o):return {str(p[1]):str(p[2]) for p in children(o,'property')}
def ref(o):return props(o)['Reference']
def pins(v):return {n.get('ref')+'.'+n.get('pin'):net.get('name') for net in ET.parse(H/v/'netlist.xml').findall('.//nets/net') for n in net.findall('node')}
def comps(v):return {c.get('ref'):c for c in ET.parse(H/v/'netlist.xml').findall('.//components/comp')}
def segs(s):return [tuple(tuple(round(float(x),6) for x in p[1:3]) for p in one(w,'pts')[1:]) for w in children(s,'wire')]
def overlaps(s):
 out=[]
 for a,b in itertools.combinations(segs(s),2):
  for axis in [0,1]:
   other=1-axis
   if a[0][other]==a[1][other]==b[0][other]==b[1][other]:
    aa=sorted(p[axis] for p in a);bb=sorted(p[axis] for p in b)
    if min(aa[1],bb[1])-max(aa[0],bb[0])>1e-6:out.append([a,b])
 return out
sa=parse((H/'before/a2_usb_uart.kicad_sch').read_text());sb=parse((R/'a2_usb_uart.kicad_sch').read_text());oa={ref(o):o for o in children(sa,'symbol')};ob={ref(o):o for o in children(sb,'symbol')}
a,b=pins('before'),pins('after');ca,cb=comps('before'),comps('after')
expected={'SW2.2':['USB5V_OUT','/USB5V_SW'],'R17.1':[None,'/USB5V_SW'],'R17.2':[None,'USB5V_OUT'],'TP1.1':[None,'/USB5V_SW'],'TP2.1':[None,'USB5V_OUT']}
delta={k:[a.get(k),b.get(k)] for k in sorted(a.keys()|b.keys()) if a.get(k)!=b.get(k)}
liba={o[1]:o for o in children(one(sa,'lib_symbols'),'symbol')};libb={o[1]:o for o in children(one(sb,'lib_symbols'),'symbol')}
checks={
 'exactly_authorized_terminal_delta':delta==expected,
 'added_parts_only_R17_TP1_TP2':set(cb)-set(ca)=={'R17','TP1','TP2'} and set(ca)<=set(cb),
 'all_existing_part_attributes_identical':all(props(oa[r])==props(ob[r]) for r in ca),
 'existing_symbol_UUIDs_and_pin_UUIDs_preserved':all(one(oa[r],'uuid')==one(ob[r],'uuid') and children(oa[r],'pin')==children(ob[r],'pin') for r in oa),
 'existing_symbol_definitions_pin_numbers_and_types_unchanged':all(liba[k]==libb[k] for k in liba),
 'one_standard_TestPoint_definition_added':set(libb)-set(liba)=={'Connector:TestPoint'},
 'unrelated_symbols_byte_equivalent':all(oa[r]==ob[r] for r in oa if r not in {'#FLG05','#PWR0123'}),
 'existing_DNP_BOM_board_flags_identical':all(all(one(oa[r],k)==one(ob[r],k) for k in ['dnp','in_bom','on_board']) for r in oa),
 'J2_4_remains_USB5V_OUT':b['J2.4']=='USB5V_OUT',
 'all_FLAGs_up':all(float(one(o,'at')[3])==0 and one(o,'mirror') is None for r,o in ob.items() if r.startswith('#FLG')),
 'all_capacitors_vertical_and_unchanged':all(float(one(o,'at')[3])==0 and o==oa[r] for r,o in ob.items() if r.startswith('C')),
 'zero_positive_length_wire_overlaps':not overlaps(sb),
 'zero_duplicate_segments':len(segs(sb))==len(set(tuple(sorted(s)) for s in segs(sb))),
 'source_matches_export':(R/'a2_usb_uart.kicad_sch').read_bytes()==(H/'after/a2_usb_uart.kicad_sch').read_bytes(),
 'TPs_in_board_but_not_assembly_BOM':all(one(ob[r],'on_board')[1]=='yes' and one(ob[r],'in_bom')[1]=='no' for r in ['TP1','TP2'])}
for v in ['before','after']:
 er=json.loads((H/v/'erc.json').read_text());checks[v+'_ERC_zero_errors_warnings']=not [i for sh in er['sheets'] for i in sh['violations']]
checks['ERC_exclusions_unchanged']=json.loads((H/'before/erc.json').read_text())['ignored_checks']==json.loads((H/'after/erc.json').read_text())['ignored_checks']
# Symbol table only adds Connector; all old entries preserve exact parsed definitions.
a_table=parse(git('show',BASE+':01_New_Design/kicad_direct/sym-lib-table').decode());b_table=parse((R/'sym-lib-table').read_text())
checks['existing_symbol_library_entries_unchanged']=children(b_table,'lib')[:-1]==children(a_table,'lib') and one(children(b_table,'lib')[-1],'name')[1]=='Connector'
# Board loader checks the new library files without opening or writing the protected PCB.
import pcbnew
fp=pcbnew.FootprintLoad(str(R/'libraries/A2.pretty'),'R_0603_Bourns_CRPF');tp=pcbnew.FootprintLoad(str(R/'libraries/A2.pretty'),'TestPoint_Pad_D1.5mm')
assert fp and tp
pad_data=lambda f:[{'number':p.GetNumber(),'x_mm':pcbnew.ToMM(p.GetPosition().x),'y_mm':pcbnew.ToMM(p.GetPosition().y),'width_mm':pcbnew.ToMM(p.GetSize().x),'height_mm':pcbnew.ToMM(p.GetSize().y)} for p in f.Pads()]
rpads=pad_data(fp);tpads=pad_data(tp)
checks['R17_pads_follow_manufacturer_midpoint']=sorted((p['x_mm'],p['width_mm'],p['height_mm']) for p in rpads)==[(-.725,.65,.9),(.725,.65,.9)]
checks['TP_pad_diameter_1p5mm_no_paste']=len(tpads)==1 and tpads[0]['width_mm']==tpads[0]['height_mm']==1.5 and not list(tp.Pads())[0].GetLayerSet().Contains(pcbnew.F_Paste)
# Hash every existing A2 tracked file except the two explicitly edited files.
files=git('ls-tree','-r','--name-only',BASE,'--','01_New_Design/kicad_direct').decode().splitlines();allow={REL,'01_New_Design/kicad_direct/sym-lib-table'}
protected={}
for f in files:
 if f not in allow:
  expected_sha=hashlib.sha256(git('show',BASE+':'+f)).hexdigest();actual_sha=hashlib.sha256((ROOT/f).read_bytes()).hexdigest();protected[f]={'baseline':expected_sha,'current':actual_sha}
# Git's clean filters account for the existing Windows CRLF checkout. Compare blob IDs as well as retaining raw SHA256 evidence.
base_blobs={line.split()[3]:line.split()[2] for line in git('ls-tree','-r',BASE,'--','01_New_Design/kicad_direct').decode().splitlines()}
current_blobs=subprocess.check_output(['git','hash-object','--stdin-paths'],input=('\n'.join(protected)+'\n').encode(),cwd=ROOT).decode().splitlines()
for (f,d),blob in zip(protected.items(),current_blobs):d['baseline_git_blob']=base_blobs[f];d['current_git_blob']=blob
checks['all_protected_existing_A2_files_identical']=all(d['baseline_git_blob']==d['current_git_blob'] for d in protected.values())
(H/'preservation.json').write_text(json.dumps(protected,indent=2),encoding='utf8')
report={'time':datetime.datetime.now().astimezone().isoformat(),'base':BASE,'contract':'electrical-change','skills':{'schematic-design':'0.1.0','schematic-style-standard':'0.1.0'},'checks':checks,'all_pass':all(checks.values()),'counts':{'components':[len(ca),len(cb)],'terminals':[len(a),len(b)],'nets':[len(set(a.values())),len(set(b.values()))]},'terminal_delta':delta,'wire_overlaps_before':overlaps(sa),'wire_overlaps_after':overlaps(sb),'protected_file_count':len(protected),'R17_pad_geometry':rpads,'TP_pad_geometry':tpads,'source_sha256':hashlib.sha256((R/'a2_usb_uart.kicad_sch').read_bytes()).hexdigest()}
(H/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
(H/'export_manifest.json').write_text(json.dumps({str(p.relative_to(H)):hashlib.sha256(p.read_bytes()).hexdigest() for v in ['before','after'] for p in (H/v).iterdir() if p.is_file()},indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2));assert report['all_pass']

