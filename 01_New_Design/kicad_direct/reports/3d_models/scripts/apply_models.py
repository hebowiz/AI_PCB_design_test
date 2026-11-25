"""Patch only model expressions; preserve all other PCB bytes."""
from pathlib import Path
import subprocess,re,json,hashlib,shutil
import pcbnew as k
root=Path('01_New_Design/kicad_direct')
report=root/'reports/3d_models'
base='22a74e75bdd508a28644a9df42fda8d10793d63e'

def spans(s,key):
    result=[]
    for m in re.finditer(r'\('+re.escape(key)+r'\s',s):
        start=m.start(); level=0; quote=False; escape=False
        for i in range(start,len(s)):
            c=s[i]
            if escape:escape=False;continue
            if quote and c=='\\':escape=True;continue
            if c=='"':quote=not quote
            if not quote:
                if c=='(':level+=1
                elif c==')':
                    level-=1
                    if level==0:result.append((start,i+1));break
    return result

mapping={
 'J1':'${KIPRJMOD}/models/vendor/Molex_480372200_aligned.step',
 'J2':'${KIPRJMOD}/models/TSM_104_01_T_SH_simplified.wrl',
 'D1':'${KIPRJMOD}/models/DPY0002A_simplified.wrl',
 'D5':'${KIPRJMOD}/models/DPY0002A_simplified.wrl',
 'R17':'${KICAD10_3DMODEL_DIR}/Resistor_SMD.3dshapes/R_0603_1608Metric.step'}
def strip_models(s):
    for a,b in reversed(spans(s,'model')):s=s[:a]+s[b:]
    return re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',s)
def modelblock(path,indent):
    return '(model "'+path+'"\n'+indent+'\t(offset (xyz 0 0 0))\n'+indent+'\t(scale (xyz 1 1 1))\n'+indent+'\t(rotate (xyz 0 0 0))\n'+indent+')'
def replace(s,path,indent):
    positions=spans(s,'model')
    if positions:
        assert len(positions)==1
        a,b=positions[0];return s[:a]+modelblock(path,indent)+s[b:]
    idx=s.rfind(')')
    return s[:idx].rstrip()+'\n'+indent+modelblock(path,indent)+'\n'+indent[:-1]+s[idx:]
pcb=root/'a2_usb_uart.kicad_pcb'
before=subprocess.check_output(['git','show',base+':'+pcb.as_posix()]).decode('utf-8')
after=before
changed=[]
for a,b in reversed(spans(before,'footprint')):
    block=before[a:b];m=re.search(r'\(property "Reference" "([^"]+)"',block)
    if m and m[1] in mapping:
        after=after[:a]+replace(block,mapping[m[1]],'\t\t')+after[b:];changed.append(m[1])
assert strip_models(before)==strip_models(after)
assert pcb.read_text(encoding='utf-8') in (before, after), 'PCB differs from this script baseline/candidate; stop'
pcb.write_bytes(after.encode('utf-8'))
library_names={'J1':'USB_A_Molex_48037-2200_Horizontal','J2':'TSM_104_SH_PROVISIONAL','R17':'R_0603_Bourns_CRPF'}
for ref,name in library_names.items():
    p=root/'libraries/A2.pretty'/(name+'.kicad_mod')
    original=subprocess.check_output(['git','show',base+':'+p.as_posix()]).decode('utf-8')
    updated=replace(original,mapping[ref],'\t');assert strip_models(original)==strip_models(updated)
    assert p.read_text(encoding='utf-8') in (original, updated), 'Library differs from baseline/candidate; stop'
    p.write_bytes(updated.encode('utf-8'))
installed=Path('C:/Users/hebow/AppData/Local/Programs/KiCad/10.0/share/kicad/3dmodels')
rows=[]
board=k.LoadBoard(str(pcb))
for f in board.GetFootprints():
    models=[]
    for m in f.Models():
        path=m.m_Filename.replace('${KIPRJMOD}',str(root)).replace('${KICAD10_3DMODEL_DIR}',str(installed))
        models.append({'path':m.m_Filename,'exists':Path(path).is_file()})
    rows.append({'ref':f.GetReference(),'dnp':f.IsDNP(),'models':models})
assert all(all(m['exists'] for m in row['models']) for row in rows)
assert {r['ref'] for r in rows if not r['models']}=={'TP1','TP2'}
proof={'base':base,'modified_references':sorted(changed),'all_non_model_PCB_content_equal':True,'footprints':len(rows),'tracks_and_vias':len(list(board.GetTracks())),'zones':len(list(board.Zones())), 'models':rows}
(report/'integrity.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps({x:y for x,y in proof.items() if x!='models'},indent=2))
