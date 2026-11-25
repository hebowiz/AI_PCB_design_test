"""R-0034: exact model-offset edit; never regenerate layout."""
from pathlib import Path
import re, subprocess, json, hashlib
import pcbnew as k
root=Path(__file__).resolve().parents[3]
out=root/'reports/header_alignment_fix'
base='07cc2d9ab3d8d41842a378ee1c1a4df9c263ae0a'
name='TSM_104_01_T_SH_simplified.wrl'
files=['a2_usb_uart.kicad_pcb','libraries/A2.pretty/TSM_104_SH_PROVISIONAL.kicad_mod']
changes=[]
for rel in files:
 p=root/rel
 original=subprocess.check_output(['git','show',base+':01_New_Design/kicad_direct/'+rel])
 raw=p.read_bytes()
 # Normalize only for comparison; preserve actual local line endings in edit.
 assert raw.replace(b'\r\n',b'\n')==original.replace(b'\r\n',b'\n')
 pattern=rb'(\(model "\$\{KIPRJMOD\}/models/TSM_104_01_T_SH_simplified\.wrl"\s*\(offset\s*\(xyz )0 0 0(\))'
 fixed,n=re.subn(pattern,rb'\g<1>0 -0.7172 0\2',raw)
 assert n==1
 p.write_bytes(fixed)
 assert fixed.replace(b'0 -0.7172 0',b'0 0 0',1)==raw
 changes.append({'file':rel,'only_model_offset_changed':True,'before_sha256':hashlib.sha256(raw).hexdigest(),'after_sha256':hashlib.sha256(fixed).hexdigest()})
# Fresh parser read from disk, not the transient object edited above.
b=k.LoadBoard(str(root/'a2_usb_uart.kicad_pcb'))
f=next(x for x in b.GetFootprints() if x.GetReference()=='J2')
lib=k.FootprintLoad(str(root/'libraries/A2.pretty'),'TSM_104_SH_PROVISIONAL')
for obj in [f,lib]:
 m=list(obj.Models())[0]
 assert abs(m.m_Offset.y+.7172)<1e-9
 assert [m.m_Scale.x,m.m_Scale.y,m.m_Scale.z]==[1,1,1]
 assert [m.m_Rotation.x,m.m_Rotation.y,m.m_Rotation.z]==[0,0,0]
s=(root/'models'/name).read_text()
body=re.search(r'point \[(.*?)\]',s,re.S).group(1)
ys=[float(row.strip().split()[1])*2.54 for row in body.strip().split(',')]
fy=k.ToMM(f.GetPosition().y)
assert f.GetOrientationDegrees()==0
offset=list(f.Models())[0].m_Offset.y
bounds=[fy-max(ys)-offset,fy-min(ys)-offset]
edge=max(k.ToMM(g.GetStart().y) for g in b.GetDrawings() if g.GetLayer()==k.Edge_Cuts)
fab=[k.ToMM(p.y) for g in f.GraphicalItems() if g.GetLayer()==k.F_Fab for p in [g.GetStart(),g.GetEnd()]]
assert abs(edge-bounds[1])<1e-6
assert abs(min(fab)-bounds[0])<1e-6 and abs(max(fab)-bounds[1])<1e-6
result={'base_commit':base,'files':changes,'saved_pcb_and_library_offset_y_mm':offset,'j2_origin_y_mm':fy,'body_board_y_bounds_mm':bounds,'fab_y_bounds_mm':[min(fab),max(fab)],'board_edge_y_mm':edge,'remaining_gap_mm':edge-bounds[1],'tolerance_mm':1e-6,'layout_copper_pads_nets_fields_unchanged':True}
(out/'checks/alignment.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
