"""Compare complete KiCad XML netlists and immutable schematic data."""
from pathlib import Path
import xml.etree.ElementTree as ET
import json,hashlib,subprocess,sys,csv,copy
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]; REPO=ROOT.parents[1]
BASE='6491a464c2eb8ea2d876a913f37be9590db316d8'
sys.path.insert(0,str(ROOT/'scripts'))
from sexpr import parse,children,one
def sha(b):return hashlib.sha256(b).hexdigest()
trees=[ET.parse(HERE/d/'netlist.xml') for d in ['before','after']]
normalized=[]
for d,t in zip(['before','after'],trees):
    # This is the ONLY excluded XML field. No net, component, library, UUID,
    # filename, ordering, or numeric net-code normalization is performed.
    t.find('./design/date').text='EXPORT_TIMESTAMP_ONLY'
    data=ET.tostring(t.getroot(),encoding='utf-8',xml_declaration=True)
    (HERE/d/'netlist.normalized.xml').write_bytes(data);normalized.append(data)
before=parse((HERE/'before/a2_usb_uart.kicad_sch').read_text(encoding='utf-8-sig'))
after=parse((ROOT/'a2_usb_uart.kicad_sch').read_text(encoding='utf-8-sig'))
def invariants(s):
    result={}
    for v in children(s,'symbol'):
        v=copy.deepcopy(v);ref=one(v,'property')[2]
        v[:]=[n for n in v if not isinstance(n,list) or n[0]!='at']
        for prop in children(v,'property'):
            prop[:]=[n for n in prop if not isinstance(n,list) or n[0] not in ['at','effects']]
        result[ref]=v
    return result
a,b=invariants(before),invariants(after)
changed=[ref for ref in sorted(set(a)|set(b)) if a.get(ref)!=b.get(ref)]
# Hash every pre-existing A-2 file except the one authorized schematic.
# Git's path filter accounts only for the repository's configured EOL rules.
items=subprocess.check_output(['git','ls-tree','-r',BASE,'--','01_New_Design/kicad_direct'],cwd=REPO,text=True).splitlines()
protected=[]
for item in items:
    meta,path=item.split('\t');old=meta.split()[2]
    if path=='01_New_Design/kicad_direct/a2_usb_uart.kicad_sch':continue
    current=subprocess.check_output(['git','hash-object','--path='+path,path],cwd=REPO,text=True).strip()
    protected.append({'path':path,'base_git_blob':old,'current_git_blob':current,'equal':old==current})
with (HERE/'protected_files.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=protected[0].keys());w.writeheader();w.writerows(protected)
erc={}
for d in ['before','after']:
    v=json.loads((HERE/d/'erc.json').read_text(encoding='utf-8-sig'))
    violations=[x for sh in v['sheets'] for x in sh['violations']]
    erc[d]={'errors':sum(x['severity']=='error' for x in violations),'warnings':sum(x['severity']=='warning' for x in violations),'total':len(violations)}
snapshot=(HERE/'before/a2_usb_uart.kicad_sch').read_bytes()
baseline=subprocess.check_output(['git','show',BASE+':01_New_Design/kicad_direct/a2_usb_uart.kicad_sch'],cwd=REPO)
assert snapshot==baseline, 'Before snapshot differs from main baseline'
assert sha(snapshot)==(HERE/'before/source_sha256.txt').read_text().strip()
assert sha((ROOT/'a2_usb_uart.kicad_sch').read_bytes())==(HERE/'after/source_sha256.txt').read_text().strip(), 'Saved exports do not match the current schematic revision'
result={'base_snapshot_byte_identical':snapshot==baseline,'export_input_hashes_match':True,'base_commit':BASE,'netlist_complete_xml_equal_except_export_timestamp':normalized[0]==normalized[1],
 'only_excluded_xml_field':'design/date','normalized_sha256':[sha(n) for n in normalized],
 'net_count':len(trees[0].findall('.//nets/net')),
 'terminal_count':sum(len(n.findall('node')) for n in trees[0].findall('.//nets/net')),
 'component_count':len(trees[0].findall('.//components/comp')),
 'symbol_instances':len(a),'changed_immutable_symbol_data':changed,
 'embedded_library_symbols_unchanged':one(before,'lib_symbols')==one(after,'lib_symbols'),
 'root_uuid_unchanged':one(before,'uuid')==one(after,'uuid'),
 'protected_existing_files':len(protected),'protected_file_differences':[p['path'] for p in protected if not p['equal']],
 'erc':erc}
(HERE/'comparison.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
assert normalized[0]==normalized[1], 'Complete XML differs beyond export timestamp'
assert not changed and result['embedded_library_symbols_unchanged'] and result['root_uuid_unchanged']
assert not result['protected_file_differences']
assert erc['before']['total']==erc['after']['total']==0
print(json.dumps(result,indent=2))
