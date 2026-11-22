"""Read-only inspection of the approved A-2 schematic; writes review evidence only."""
from pathlib import Path
import sys,json,hashlib,subprocess,xml.etree.ElementTree as ET
D=Path(sys.argv[1]);O=Path(__file__).parent
sys.path.insert(0,str(D/'01_New_Design/kicad_direct/scripts'))
from sexpr import parse,children,one
R=D/'01_New_Design/kicad_direct';P=R/'a2_usb_uart.kicad_sch';S=parse(P.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
g=lambda a:tuple(round(float(v)/1.27,5) for v in a)
wires=[tuple(g(p[1:3]) for p in one(w,'pts')[1:]) for w in children(S,'wire')]
ws={frozenset(w) for w in wires}
paths={
 'USB_D+':[(42,48),(58,48),(58,29),(187,29),(187,67),(177,67)],
 'USB_D-':[(42,46),(74,46),(74,27),(189,27),(189,65),(177,65)],
 'XTAL_IN':[(102,42),(93,42),(93,32),(137,32),(137,63),(153,63)],
 'XTAL_OUT':[(108,42),(117,42),(117,34),(139,34),(139,65),(153,65)]}
for name,path in paths.items():
 for a,b in zip(path,path[1:]):assert frozenset((a,b)) in ws,(name,a,b)
def crosses(p,q):
 result=[]
 for a,b in zip(p,p[1:]):
  for c,d in zip(q,q[1:]):
   if a[0]==b[0] and c[1]==d[1]:
    x,y=a[0],c[1]
    if min(a[1],b[1])<y<max(a[1],b[1]) and min(c[0],d[0])<x<max(c[0],d[0]):result.append((x,y))
   elif a[1]==b[1] and c[0]==d[0]:
    x,y=c[0],a[1]
    if min(c[1],d[1])<y<max(c[1],d[1]) and min(a[0],b[0])<x<max(a[0],b[0]):result.append((x,y))
 return result
objs={next(str(p[2]) for p in children(o,'property') if p[1]=='Reference'):o for o in children(S,'symbol')}
junctions={g(one(j,'at')[1:3]) for j in children(S,'junction')}
points={r:g(one(objs[r],'at')[1:3]) for r in ['C1','C2','C3','C4','C23','U1','U4','SW1','SW2','SW3','#FLG07','#PWR0109','#PWR0174','#PWR0118']}
net=ET.parse(R/'reports/review_capacitors/after/netlist.xml');nets={n.get('ref')+'.'+n.get('pin'):e.get('name') for e in net.findall('.//nets/net') for n in e.findall('node')}
refpins=['C3.1','C3.2','U1.12','U1.24','C1.1','C1.2','C23.1','C23.2','U1.40','U1.39','U1.1','U1.2','U1.6','U1.7','Y1.1','Y1.3']
flag=objs['#FLG07'];lib=next(l for l in children(one(S,'lib_symbols'),'symbol') if l[1]==one(flag,'lib_id')[1])
# Find the vertical graphic stem, and its exact coincident wire segment.
assert frozenset(((141,100),(141,99))) in ws
newpaths={
 'USB_D+':[(42,48),(58,48),(58,27),(189,27),(189,67),(177,67)],
 'USB_D-':[(42,46),(74,46),(74,29),(187,29),(187,65),(177,65)],
 'XTAL_IN':[(102,42),(93,42),(93,32),(139,32),(139,63),(153,63)],
 'XTAL_OUT':[(108,42),(117,42),(117,34),(137,34),(137,65),(153,65)]}
result={'design_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=D,text=True).strip(),'source_sha256':sha(P),'snapshot_matches':P.read_bytes()==(R/'reports/review_capacitors/after/a2_usb_uart.kicad_sch').read_bytes(),'design_status':subprocess.check_output(['git','status','--porcelain'],cwd=D,text=True),'coordinate_unit':'50 mil grid = 1.27 mm; display geometry, not PCB length','positions':points,'selected_terminal_nets':{k:nets[k] for k in refpins},'existing_paths':paths,'existing_pair_crossings':{name:crosses(paths[a],paths[b]) for name,a,b in [('USB','USB_D+','USB_D-'),('XTAL','XTAL_IN','XTAL_OUT')]},'flag_graphic':lib,'flag_wire_overlap_grid':[[141,100],[141,99]],'proposal_only_paths':newpaths,'proposal_pair_crossings':{name:crosses(newpaths[a],newpaths[b]) for name,a,b in [('USB','USB_D+','USB_D-'),('XTAL','XTAL_IN','XTAL_OUT')]},'power_spacing_mm':{'USB5V_to_U4_input_rail_vertical':(231-178)*1.27,'U4_center_to_SW3_center_horizontal':(210-65)*1.27,'U4_center_to_SW2_center_vertical':(293-232)*1.27},'notes':['Proposal paths are geometric sketches only: no schematic edit, netlist export or ERC performed.','Pair crossing count is per pair, not crossings against all schematic objects.','A flag graphic stem overlapping a wire is not two duplicate wire objects.']}
result['existing_crossings_have_no_junction']=all(tuple(p) not in junctions for group in result['existing_pair_crossings'].values() for p in group)
assert result['snapshot_matches'] and result['design_status']==''
(O/'R-0009_R-0013.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
from PIL import Image
im=Image.open(R/'reports/review_capacitors/after/schematic.png');f=im.width/(594/1.27)
for name,box in {'pair_routes':(38,23,195,70),'power_spacing':(15,166,237,319)}.items():im.crop(tuple(round(v*f) for v in box)).save(O/('R-0009_R-0013_'+name+'.png'))
print(json.dumps({k:result[k] for k in ['source_sha256','snapshot_matches','existing_pair_crossings','proposal_pair_crossings','existing_crossings_have_no_junction','power_spacing_mm']},indent=2))
