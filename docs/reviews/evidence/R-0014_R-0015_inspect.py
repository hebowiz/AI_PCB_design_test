"""Read current schematic only; write review evidence and crops beside this script."""
from pathlib import Path
import sys,json,hashlib,subprocess,math,xml.etree.ElementTree as ET
D=Path(sys.argv[1]);O=Path(__file__).parent;R=D/'01_New_Design/kicad_direct'
sys.path.insert(0,str(R/'scripts'));from sexpr import parse,children,one
P=R/'a2_usb_uart.kicad_sch';S=parse(P.read_text());H=R/'reports/review_drawing/after'
objs={next(str(p[2]) for p in children(o,'property') if p[1]=='Reference'):o for o in children(S,'symbol')}
libs={str(l[1]):l for l in children(one(S,'lib_symbols'),'symbol')}
g=lambda p:tuple(round(float(v)/1.27,5) for v in p)
pos=lambda o:g(one(o,'at')[1:3])
props=lambda o:{str(p[1]):str(p[2]) for p in children(o,'property')}
wires=[tuple(g(p[1:3]) for p in one(w,'pts')[1:]) for w in children(S,'wire')]
def on(p,w):
 a,b=w;return abs((p[0]-a[0])*(b[1]-a[1])-(p[1]-a[1])*(b[0]-a[0]))<1e-6 and min(a[0],b[0])<=p[0]<=max(a[0],b[0]) and min(a[1],b[1])<=p[1]<=max(a[1],b[1])
net=ET.parse(H/'netlist.xml');nets={n.get('ref')+'.'+n.get('pin'):e.get('name') for e in net.findall('.//nets/net') for n in e.findall('node')}
def pins(r):
 o=objs[r];a=one(o,'at');ang=math.radians(float(a[3]));origin=pos(o);out={}
 assert one(o,'mirror') is None
 for part in children(libs[str(one(o,'lib_id')[1])],'symbol'):
  for p in children(part,'pin'):
   x,y=g(one(p,'at')[1:3]);q=(round(origin[0]+x*math.cos(ang)-y*math.sin(ang),5),round(origin[1]-x*math.sin(ang)-y*math.cos(ang),5))
   out[str(one(p,'number')[1])]={'name':str(one(p,'name')[1]),'point_grid':q,'net':nets.get(r+'.'+str(one(p,'number')[1]))}
 return out
flags=[]
for r,o in objs.items():
 if str(one(o,'lib_id')[1])!='power:PWR_FLAG':continue
 q=pos(o);touch=[w for w in wires if on(q,w)]
 flags.append({'ref':r,'position_grid':q,'angle_degrees':float(one(o,'at')[3]),'mirror':one(o,'mirror'),'touching_wires_grid':touch,'nearby_symbols':[{'ref':k,'value':props(v)['Value'],'position_grid':pos(v)} for k,v in objs.items() if k!=r and math.dist(pos(v),q)<15]})
reset={r:{'position_grid':pos(objs[r]),'attributes':props(objs[r]),'pins':pins(r)} for r in ['R2','C22']}
u=pins('U1')['34'];reset['U1.34']=u
reset['horizontal_distance_to_U1_34_mm']={r:round(abs(pos(objs[r])[0]-u['point_grid'][0])*1.27,2) for r in ['R2','C22']}
reset['nearby_wires_grid']=[w for w in wires if any(35<=p[0]<=75 and 115<=p[1]<=145 for p in w)]
reset['nearby_labels']=[l for l in children(S,'label') if 'RESET' in str(l[1])]
result={'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=D,text=True).strip(),'design_status':subprocess.check_output(['git','status','--porcelain'],cwd=D,text=True),'source_sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'snapshot_matches':P.read_bytes()==(H/'a2_usb_uart.kicad_sch').read_bytes(),'reset':reset,'flags':flags,'units':'grid=1.27 mm, schematic geometry only; not PCB length'}
assert result['commit']=='7f0941b45309ad069e947849772c3ecf7c1d1e61' and result['design_status']=='' and result['snapshot_matches']
(O/'R-0014_R-0015.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
from PIL import Image
im=Image.open(H/'schematic.png');f=im.width/(594/1.27)
for name,box in {'reset_and_U1':(32,75,182,148),'flags':(128,178,169,253)}.items():im.crop(tuple(round(v*f) for v in box)).save(O/('R-0014_R-0015_'+name+'.png'))
print(json.dumps(result,ensure_ascii=False,indent=2))
