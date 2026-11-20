"""Local, idempotent V3 presentation patch; does not run the V3 generator."""
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
d=json.loads((R/'reports/schematic_v3/drawing.json').read_text())
segments=[(tuple(a),tuple(b),n) for a,b,n in d['v3_classified_wires']]
oldpins={k:tuple(v['at']) for k,v in d['pins'].items()}
nets={k:v['net'] for k,v in d['pins'].items()}
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
def newpower(n,at):
 r0=next(r for r,o in objs.items() if r.startswith('#PWR') and str(children(o,'property')[1][2])==n)
 o=copy.deepcopy(objs[r0]);r='#PWR'+str(171+len(added)).zfill(4);added.append(r)
 one(o,'uuid')[1]=uid();one(o,'property')[2]=Q(r)
 for p in children(o,'pin'):one(p,'uuid')[1]=uid()
 for proj in children(one(o,'instances'),'project'):
  for p in children(proj,'path'):one(p,'reference')[1]=Q(r)
 objs[r]=o;s.append(o);nets[r+'.1']=n;move(r,*at)
 return r
added=[]
def ground(r,k='2',end=None,via=()):
 old=oldpins[r+'.'+k];oldend=(old[0],old[1]+2)
 remove(lambda a,b,n:n=='GND' and (a==old or b==old))
 p=pins()[r+'.'+k];end=end or (p[0],p[1]+1)
 power_at('GND',oldend,end);path('GND',p,*via,end)
def labelmove(n,old,new):
 o=next(o for o in children(s,'label') if o[1]==n and coord(o)==tuple(old));one(o,'at')[1:3]=pt(new)
# New local coil graphic: same anchor positions, numbers, names, and passive types.
coil=copy.deepcopy(libs['Device:FerriteBead']);coil[1]=Q('FB_Coil')
for o in children(coil,'symbol'):
 if str(o[1]).endswith('_0_1'):
  o[:]=['symbol',Q('FB_Coil_0_1')]
  for top in [2.54,1.27,0,-1.27]:
   o.append(['arc',['start',0,top],['mid',.6323,round(top-.635,4)],['end',0,round(top-1.27,4)],['stroke',['width',0],['type','default']],['fill',['type','none']]])
 else:
  o[1]=Q('FB_Coil_1_1')
  for p in children(o,'pin'):one(p,'length')[1]=1.27
local=['kicad_symbol_lib',['version','20241209'],['generator',Q('a2_v3_refine')],coil]
(R/'libraries/A2_Refine.kicad_sym').write_text(dump(local),encoding='utf-8')
embedded=copy.deepcopy(coil);embedded[1]=Q('A2_Refine:FB_Coil');one(s,'lib_symbols').append(embedded);libs[str(embedded[1])]=embedded
for r in ['FB1','FB2']:one(objs[r],'lib_id')[1]=Q('A2_Refine:FB_Coil')
table=parse((R/'sym-lib-table').read_text());table[:]=[o for o in table if not(isinstance(o,list) and o[0]=='lib' and one(o,'name')[1]=='A2_Refine')]
table.append(['lib',['name',Q('A2_Refine')],['type',Q('KiCad')],['uri',Q('${KIPRJMOD}/libraries/A2_Refine.kicad_sym')],['options',Q('')],['descr',Q('Ferrite bead with coil graphic; electrical identity retained')]])
(R/'sym-lib-table').write_text(dump(table),encoding='utf-8')
# D1: preserve USB overhead pair; shorten both signal branches and local return.
remove(lambda a,b,n:n in ['USB_D+','USB_D-'])
move('D1',66,54);fields('D1',80,52)
path('USB_D-',(42,46),(74,46),(74,27),(189,27),(189,65),(177,65));path('USB_D-',(74,46),(74,54))
path('USB_D+',(42,48),(58,48),(58,29),(187,29),(187,67),(177,67));path('USB_D+',(58,48),(58,54))
ground('D1','3')
# Crystal load branches and reset bypass: keep existing pair trunk.
for r,x in [('C13',93),('C14',117)]:
 old=oldpins[r+'.1'];remove(lambda a,b,n:old in (a,b));move(r,x,46);fields(r,x+2,45)
 path(nets[r+'.1'],(x,42),(x,43));ground(r)
remove(lambda a,b,n:n in ['REF12K','RESET_N','VCCA_1V8','VCORE_1V8','VPHY','VPLL'])
move('R1',105,87);fields('R1',107,86);path('REF12K',(105,84),(113,84),(113,71),(153,71));ground('R1')
move('C22',45,136);fields('C22',47,135);ground('C22')
path('RESET_N',(45,129),(45,132),(45,133));path('RESET_N',(45,132),(120,132),(120,92),(147,92),(147,89),(153,89))
# Remove old U1 +3V3 decoupler bank and the two old filter input stubs only.
remove(lambda a,b,n:n=='+3V3' and max(a[0],b[0])<180 and min(a[1],b[1])>=60 and max(a[1],b[1])<160 and not (a[0]==b[0]==45))
for r,y in [('C3',81),('C4',87),('C5',99),('C6',107)]:
 move(r,137,y,270);fields(r,143 if r=='C3' else 123,y-1)
 path('+3V3',(140,y),(141,y),(153,y))
 ground(r,end=(134,y+1))
 if r=='C3':power_at('+3V3',(83,139),(141,y))
 else:newpower('+3V3',(141,y))
path('+3V3',(151,99),(151,101),(153,101))
for r,x,n,yy,track in [('C7',158,'VCCA_1V8',95,147),('C8',136,'VCORE_1V8',97,145)]:
 oldpower=(158,116) if r=='C7' else (178,120)
 move(r,x,121);fields(r,x+2,120);ground(r)
 path(n,(153,yy),(track,yy),(track,116),(x,116),(x,118));pr=power_at(n,oldpower,(x,116))
 if r=='C8':one(children(objs[pr],'property')[1],'at')[1:]=[*pt((136,112)),0]
for fb,ca,cb,fl,net,fy,cy1,cy2,up in [('FB1','C11','C9','#FLG03','VPHY',58,61,67,67),('FB2','C12','C10','#FLG04','VPLL',73,77,83,73)]:
 oldfy=83 if fb=='FB1' else 107
 move(fb,104,fy);fields(fb,104,fy-6,True)
 power_at('+3V3',(46,oldfy),(95,fy));path('+3V3',(95,fy),(101,fy))
 move(fl,115,fy);path(net,(107,fy),(130,fy),(130,max(up,cy2)))
 path(net,(130,up),(153,up))
 power_at(net,(106,oldfy),(134,up))
 for r,cy in [(ca,cy1),(cb,cy2)]:
  move(r,125,cy,270);fields(r,115,cy-1);path(net,(128,cy),(130,cy))
  ground(r,end=(122,cy+1))
# U2 supply tap -> capacitor -> nearby VCCA/VCCB. Preserve DIR tie and UART crossings.
remove(lambda a,b,n:n=='+3V3' and 230<=min(a[0],b[0]) and max(a[0],b[0])<=258 and max(a[1],b[1])<=65)
remove(lambda a,b,n:n=='VIO' and 282<=min(a[0],b[0]) and max(a[0],b[0])<=303 and max(a[1],b[1])<=63)
move('C16',250,56);fields('C16',241,55);ground('C16')
path('+3V3',(244,52),(250,52),(254,52),(254,63),(258,63));path('+3V3',(250,52),(250,53));path('+3V3',(258,65),(254,65),(254,63))
power_at('+3V3',(238,49),(244,52))
move('C17',290,56);fields('C17',292,55);ground('C17')
path('VIO',(298,52),(290,52),(286,52),(286,63),(282,63));path('VIO',(290,52),(290,53));power_at('VIO',(303,49),(298,52))
# EEPROM cap: shorten its branch while preserving EE_CS and explicit data wiring.
old=oldpins['C15.1'];remove(lambda a,b,n:old in (a,b));move('C15',248,178);fields('C15',239,177);ground('C15');path('+3V3',(248,174),(248,175))
remove(lambda a,b,n:n=='EE_CS' and min(a[1],b[1])>170)
path('EE_CS',(254,182),(252,182),(252,179));labelmove('EE_CS',(252,177),(252,179))
lo=next(o for o in children(s,'label') if o[1]=='EE_CS' and coord(o)==(252,179));one(one(lo,'effects'),'justify')[1]='left'
# LDO/load switch bypass caps, short ground returns and preserved power tree.
for r,x,y,rail in [('C1',52,190,185),('C2',79,190,185),('C18',44,234,230),('C19',82,234,230),('C20',44,296,292),('C21',84,296,292)]:
 old=oldpins[r+'.1'];remove(lambda a,b,n:old in (a,b));move(r,x,y);fields(r,x+2,y-1)
 path(nets[r+'.1'],(x,rail),(x,y-3));ground(r)
# Two control stubs and QOD route are moved to keep capacitor text/branches clear.
remove(lambda a,b,n:n=='PWR_EN' and max(a[0],b[0])<70)
path('PWR_EN',(59,232),(54,232));fields('C18',36,233)
path('PWR_EN',(57,296),(52,296));fields('C20',36,295)
remove(lambda a,b,n:n=='QOD');path('QOD',(73,296),(77,296),(77,311),(110,311))
# Remote labels on local wired nodes get their own short end stubs.
path('EE_DATA',(294,184),(294,181));labelmove('EE_DATA',(294,184),(294,181))
path('PWREN_N',(271,270),(267,270));labelmove('PWREN_N',(271,270),(267,270))
lo=next(o for o in children(s,'label') if o[1]=='PWREN_N' and coord(o)==(267,270));one(one(lo,'effects'),'justify')[1]='right'
path('PWR_EN',(307,266),(312,266));labelmove('PWR_EN',(307,266),(312,266))
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
# Identify current experiment without changing the V3 explanatory content.
for o in children(s,'text'):
 if o[1]=='V3 presentation experiment. User approval pending.':o[1]=Q('V3 refinement. User approval pending.')
target.write_text(dump(s),encoding='utf-8')
(H/'patch_manifest.json').write_text(json.dumps({'base_sha256':sha(base.read_bytes()),'source_sha256':sha(target.read_bytes()),'moved_symbols':sorted(set(moved)),'added_power_symbols':added,'retained_wire_uuids':retained,'classified_wires':sorted(edges),'pins':P},indent=2))
print('Patched locally; existing symbol UUIDs preserved. Validation required.')
