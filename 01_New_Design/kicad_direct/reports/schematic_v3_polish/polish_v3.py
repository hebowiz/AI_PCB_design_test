"""Local polish of the fixed V3-refine snapshot; no prior generator is executed."""
from pathlib import Path
import sys,json,copy,math,uuid,hashlib
from collections import defaultdict
H=Path(__file__).resolve().parent;R=H.parents[1]
sys.path.insert(0,str(R/'scripts'));from sexpr import *
if '--apply' not in sys.argv:raise SystemExit('Use --apply')
sha=lambda b:hashlib.sha256(b).hexdigest()
target=R/'a2_usb_uart.kicad_sch';base=H/'before/a2_usb_uart.kicad_sch'
allowed={sha(base.read_bytes())}
if (H/'patch_manifest.json').exists():allowed.add(json.loads((H/'patch_manifest.json').read_text())['source_sha256'])
assert sha(target.read_bytes()) in allowed,'Unrecorded edits; refusing overwrite'
s=parse(base.read_text(encoding='utf-8-sig'));original=copy.deepcopy(s)
objs={str(one(o,'property')[2]):o for o in children(s,'symbol')}
libs={str(o[1]):o for o in children(one(s,'lib_symbols'),'symbol')}
import xml.etree.ElementTree as ET
d=json.loads((R/'reports/schematic_v3_refine/patch_manifest.json').read_text())
segments=[(tuple(a),tuple(b),n) for a,b,n in d['classified_wires']]
oldpins={k:tuple(v) for k,v in d['pins'].items()}
nets={node.get('ref')+'.'+node.get('pin'):net.get('name') for net in ET.parse(H/'before/netlist.xml').findall('.//nets/net') for node in net.findall('node')}
for r,o in objs.items():
 if r.startswith('#PWR'):nets[r+'.1']=str(children(o,'property')[1][2])
for r,n in {'#FLG01':'USB5V','#FLG02':'GND','#FLG03':'VPHY','#FLG04':'VPLL','#FLG05':'USB5V_OUT','#FLG06':'VIO_OUT'}.items():nets[r+'.1']=n
mm=lambda v:round(v*1.27,5)
pt=lambda a:[mm(x) for x in a]
uid=lambda:Q(str(uuid.uuid4()))
def coord(o):return tuple(round(float(v)/1.27,6) for v in one(o,'at')[1:3])
def pins():
 result={}
 for r,o in objs.items():
  x,y=coord(o);ang=float(one(o,'at')[3]);t=math.radians(ang)
  for u in children(libs[str(one(o,'lib_id')[1])],'symbol'):
   for p in children(u,'pin'):
    dx,dy,_=map(float,one(p,'at')[1:]);k=str(one(p,'number')[1])
    result[r+'.'+k]=(round(x+(dx*math.cos(t)-dy*math.sin(t))/1.27,6),round(y-(dx*math.sin(t)+dy*math.cos(t))/1.27,6))
 return result
moved=[]
def move(r,x,y,a=None):
 o=objs[r];ox,oy=coord(o);oa=float(one(o,'at')[3]);a=oa if a is None else a
 one(o,'at')[1:]=[*pt((x,y)),a]
 for q in children(o,'property'):
  at=one(q,'at');at[1]=round(float(at[1])+mm(x-ox),5);at[2]=round(float(at[2])+mm(y-oy),5)
 moved.append(r)
def fields(r,x,y,center=False):
 o=objs[r];a=float(one(o,'at')[3])
 for q in children(o,'property'):
  if q[1] not in ['Reference','Value']:continue
  one(q,'at')[1:]=[*pt((x,y+(2 if q[1]=='Value' else 0))),90 if a in (90,270) else 0]
  e=one(q,'effects');j=one(e,'justify')
  if j:e.remove(j)
  if not center:e.append(['justify','left'])
def path(n,*p):
 for a,b in zip(p,p[1:]):
  if a!=b:segments.append((tuple(a),tuple(b),n))
def remove(pred):
 global segments
 segments=[e for e in segments if not pred(*e)]
def power_at(n,old,new):
 r=next(r for r,o in objs.items() if r.startswith('#PWR') and one(o,'property')[2]==r and str(children(o,'property')[1][2])==n and coord(o)==tuple(old))
 move(r,*new);return r
added=[]
def ground(r,k='2',end=None,via=()):
 old=oldpins[r+'.'+k];oldend=(old[0],old[1]+1)
 remove(lambda a,b,n:n=='GND' and (a==old or b==old))
 p=pins()[r+'.'+k];end=end or (p[0],p[1]+1)
 power_at('GND',oldend,end);path('GND',p,*via,end)
def labelmove(n,old,new):
 o=next(o for o in children(s,'label') if o[1]==n and coord(o)==tuple(old));one(o,'at')[1:3]=pt(new)
# Two caps sharing a nearby supply group use one existing power annotation.
removed=[]
def delete_power(at):
 r=next(r for r,o in objs.items() if r.startswith('#PWR') and coord(o)==at)
 s.remove(objs[r]);del objs[r];nets.pop(r+'.1');removed.append(r)
def leftfields(r,x,y):
 fields(r,x,y)
 for q in children(objs[r],'property'):
  if q[1] in ['Reference','Value']:one(one(q,'effects'),'justify')[1]='right'
# Rebuild only U1 supply/filter/reference/reset wiring; preserve all other blocks.
remove(lambda a,b,n:n in ['VPHY','VPLL','REF12K','RESET_N'])
remove(lambda a,b,n:n=='+3V3' and max(a[0],b[0])<180 and min(a[1],b[1])>60 and max(a[1],b[1])<115)
# Filter capacitors side by side, top to power and bottom to local ground.
for r,x,y,n,rail in [('C11',113,62,'VPHY',58),('C9',126,62,'VPHY',58),('C12',113,77,'VPLL',73),('C10',126,77,'VPLL',73)]:
 move(r,x,y,0);fields(r,x+2,y-1);ground(r);path(n,(x,rail),(x,y-3))
path('VPHY',(107,58),(113,58),(126,58),(135,58),(135,67),(153,67))
power_at('VPHY',(134,67),(130,58));fields('FB1',104,54,True)
path('VPLL',(107,73),(113,73),(126,73),(153,73))
r=power_at('VPLL',(134,73),(110,73));one(children(objs[r],'property')[1],'at')[1:]=[*pt((110,75)),0]
power_at('+3V3',(95,73),(89,73));path('+3V3',(89,73),(101,73));fields('FB2',104,76,True)
path('REF12K',(105,84),(96,84),(96,69),(145,69),(145,71),(153,71));labelmove('REF12K',(142,71),(133,69))
# Nearby shared +3V3 pin groups. The capacitor branches remain parallel to GND.
for r,x,y,rail in [('C3',122,87,83),('C4',137,87,83),('C5',124,105,101),('C6',137,105,101)]:
 move(r,x,y,0);fields(r,x+2,y-1);ground(r);path('+3V3',(x,rail),(x,y-3))
path('+3V3',(117,83),(122,83),(137,83),(147,83));path('+3V3',(147,83),(147,81),(153,81));path('+3V3',(147,83),(147,87),(153,87))
power_at('+3V3',(141,81),(117,83));delete_power((141,87))
path('+3V3',(124,99),(124,101),(137,101),(151,101),(153,101));path('+3V3',(151,101),(151,99),(153,99));path('+3V3',(143,101),(143,107),(153,107))
power_at('+3V3',(141,99),(124,99));delete_power((141,107))
path('RESET_N',(45,129),(45,132),(45,133));path('RESET_N',(45,132),(120,132),(120,93),(143,93),(143,89),(153,89))
# Existing vertical capacitors: bring left-side fields next to the body.
for r,x,y in [('C15',246,177),('C16',248,55),('C18',42,233),('C20',42,295)]:leftfields(r,x,y)
fields('D1',76,52);fields('U5',271,177);fields('R16',113,307,True)
fields('J2',357,67);fields('J3',357,99)
for r,x in [('D2',408),('D3',429),('D4',450)]:
 fields(r,x,72)
 # KiCad rotates field justification with a 90-degree symbol.
 for q in children(objs[r],'property'):
  if q[1] in ['Reference','Value']:one(one(q,'effects'),'justify')[1]='right'
for o in children(s,'text'):
 if o[1]=='V3 refinement. User approval pending.':o[1]=Q('V3 polish. Candidate for human review; not approved.')
# Preserve original wires/junction UUIDs when geometry is unchanged; rebuild edited segments only.
def edge(o):return tuple(tuple(round(float(v)/1.27,6) for v in q[1:]) for q in one(o,'pts')[1:])
oldwire={(min(*edge(o)),max(*edge(o))):o for o in children(s,'wire')}
oldj={coord(o):o for o in children(s,'junction')}
s[:]=[o for o in s if not(isinstance(o,list) and o[0] in ['wire','junction'])]
P=pins();points=defaultdict(set)
for a,b,n in segments:points[n].update((a,b))
for k,v in P.items():
 if nets.get(k):points[nets[k]].add(v)
edges=set()
for a,b,n in segments:
 dx=b[0]-a[0];dy=b[1]-a[1];ll=dx*dx+dy*dy;on=[]
 for q in points[n]:
  cross=(q[0]-a[0])*dy-(q[1]-a[1])*dx;dot=(q[0]-a[0])*dx+(q[1]-a[1])*dy
  if abs(cross)<1e-5 and -1e-5<=dot<=ll+1e-5:on.append((dot,q))
 on.sort()
 for (_,a1),(_,b1) in zip(on,on[1:]):
  if a1!=b1:edges.add((min(a1,b1),max(a1,b1),n))
adj=defaultdict(set);pinset={(p,nets.get(k)) for k,p in P.items()}
retained=0
for a,b,n in sorted(edges):
 if (a,b) in oldwire:s.append(oldwire[(a,b)]);retained+=1
 else:s.append(['wire',['pts',['xy',*pt(a)],['xy',*pt(b)]],['stroke',['width',.1524],['type','default']],['uuid',uid()]])
 adj[(a,n)].add(b);adj[(b,n)].add(a)
for (a,n),v in adj.items():
 if len(v)>=3 or(len(v)==2 and (a,n) in pinset):s.append(oldj.get(a,['junction',['at',*pt(a)],['diameter',.762],['color',0,0,0,0],['uuid',uid()]]))
target.write_text(dump(s),encoding='utf-8')
(H/'patch_manifest.json').write_text(json.dumps({'base_sha256':sha(base.read_bytes()),'source_sha256':sha(target.read_bytes()),'moved_symbols':sorted(set(moved)),'added_power_symbols':added,'removed_redundant_power_symbols':removed,'retained_wire_uuids':retained,'classified_wires':sorted(edges),'pins':P},indent=2))
print('Patched locally; real-component UUIDs preserved. Two redundant power annotations removed. Validation required.')
