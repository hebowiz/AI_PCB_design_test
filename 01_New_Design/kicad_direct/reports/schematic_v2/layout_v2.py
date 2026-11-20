"""V2 drawing experiment: only V0 symbols/connectivity are inputs."""
from pathlib import Path
import sys,math,uuid,json,hashlib,copy
from collections import defaultdict
import xml.etree.ElementTree as ET
H=Path(__file__).resolve().parent
R=H.parents[1]
sys.path.insert(0,str(R/'scripts'))
from sexpr import parse,dump,children,one,Q
if '--apply' not in sys.argv: raise SystemExit('Explicit --apply required. Manual changes are protected.')
target=R/'a2_usb_uart.kicad_sch'
baseline=H/'before/a2_usb_uart.kicad_sch'
allowed={hashlib.sha256(baseline.read_bytes()).hexdigest()}
if (H/'drawing.json').exists(): allowed.add(json.loads((H/'drawing.json').read_text())['sha256'])
if hashlib.sha256(target.read_bytes()).hexdigest() not in allowed: raise SystemExit('Unrecorded edits: refusing overwrite.')
s=parse(baseline.read_text(encoding='utf-8-sig')); orig=copy.deepcopy(s)
objs={one(x,'property')[2]:x for x in children(s,'symbol')}
libs={x[1]:x for x in children(one(s,'lib_symbols'),'symbol')}
nets={}
for n in ET.parse(H/'before/netlist.xml').findall('.//nets/net'):
 for x in n.findall('node'): nets[(x.attrib['ref'],x.attrib['pin'])]=n.attrib['name'].removeprefix('/')
for i,n in enumerate(['USB5V','GND','VPHY','VPLL'],1):nets[(f'#FLG0{i}','1')]=n
s[:]=[x for x in s if not isinstance(x,list) or x[0] not in ['wire','label','junction','no_connect','text','polyline','bus','bus_entry']]
pins={};used=set();segments=[];annotations=[];positions={};label_reasons=[]
def mm(v):return round(v*1.27,4)
def point(a):return [mm(x) for x in a]
def uid():return Q(str(uuid.uuid4()))
def fx(size=1.27,justify=('left','bottom')):return ['effects',['font',['size',size,size]],['justify',*justify]]
def place(ref,x,y,ang=0):
 o=objs[ref];one(o,'at')[1:]=[mm(x),mm(y),ang];positions[ref]=[x,y,ang]
 theta=math.radians(ang);pp=[]
 for u in children(libs[one(o,'lib_id')[1]],'symbol'):
  for p in children(u,'pin'):
   dx,dy,a=map(float,one(p,'at')[1:]);k=str(one(p,'number')[1])
   px=round(x+(dx*math.cos(theta)-dy*math.sin(theta))/1.27,6)
   py=round(y-(dx*math.sin(theta)+dy*math.cos(theta))/1.27,6)
   pins[(ref,k)]=(px,py,(a+ang)%360);pp.append((px,py))
 for prop in children(o,'property'):
  key=prop[1];at=one(prop,'at');e=one(prop,'effects');e[:]=fx(justify=('left',))
  at[1:]=[mm(x),mm(y),0]
  if key not in ['Reference','Value'] or ref.startswith('#'):e.append(['hide','yes']);continue
  if ref.startswith(('R','C')) and ang in (0,180):
   at[1:]=[mm(x+2),mm(y+(-1 if key=='Reference' else 1)),0]
   if ang==180:one(e,'justify')[1]='right'
  elif ref=='Q1':at[1:]=[mm(x+6),mm(y+(-1 if key=='Reference' else 1)),0]
  else:
   top=min(v[1] for v in pp)
   at[1:]=[mm(x),mm(top-(6 if key=='Reference' else 4)),90 if ang in (90,270) else 0]
   e.remove(one(e,'justify'))
def field(ref,x,y):
 for prop in children(objs[ref],'property'):
  if prop[1] in ['Reference','Value']:
   one(prop,'at')[1:]=[mm(x),mm(y+(0 if prop[1]=='Reference' else 2)),90 if positions[ref][2] in (90,270) else 0]
   one(prop,'effects')[:]=fx(justify=('left',))
def p(r,k):return pins[(r,str(k))][:2]
def n(r,k):return nets[(r,str(k))]
def seg(a,b,net):
 a=tuple(round(x,6) for x in a);b=tuple(round(x,6) for x in b)
 if a!=b:segments.append((a,b,net))
def path(net,*pts):
 for a,b in zip(pts,pts[1:]):seg(a,b,net)
def connect(a,b,*via):
 a=(a[0],str(a[1]));b=(b[0],str(b[1]))
 assert nets[a]==nets[b],(a,b,nets[a],nets[b])
 path(nets[a],p(*a),*via,p(*b));used.update([a,b])
def lead(a,*pts):
 a=(a[0],str(a[1]));path(nets[a],p(*a),*pts);used.add(a)
def lab(net,at,reason='net identifier',right=False):
 s.append(['label',Q(net),['at',*point(at),0],fx(justify=('right' if right else 'left','bottom')),['uuid',uid()]])
 label_reasons.append({'net':net,'at':at,'purpose':reason})
def rail(keys,y,tag=None):
 net=n(*keys[0]);xs=[]
 for a in keys:
  assert n(*a)==net
  q=p(*a);lead(a,(q[0],y));xs.append(q[0])
 path(net,(min(xs),y),(max(xs),y))
 if tag:lab(net,(min(xs),y),tag)
def note(x,y,value,size=1.27):
 s.append(['text',Q(value),['at',*point((x,y)),0],fx(size),['uuid',uid()]])
def heading(x,y,end,title):
 note(x,y,title,1.8)
 s.append(['polyline',['pts',['xy',*point((x,y+2))],['xy',*point((end,y+2))]],['stroke',['width',.254],['type','default']],['fill',['type','none']],['uuid',uid()]])
# V0-derived placement, coordinates in 50 mil units. No V1 geometry is loaded.
placements=[
 ('J1',30,48),('D1',66,62),('U1',165,87),
 ('Y1',112,52),('C13',100,61),('C14',124,61),('R1',118,78),
 ('R2',100,96),('C22',100,112),('C7',125,119),('C8',143,119),
 ('U2',270,70),('C16',244,52),('C17',297,52),
 ('R11',306,86,0),('R12',322,86,0),('J2',355,69),('J3',355,101),
 ('R13',404,55),('D2',404,73,90),('R14',425,55),('D3',425,73,90),('R15',446,55),('D4',446,73,90),
 ('FB1',43,169,90),('C9',63,180),('C11',83,180),('#FLG03',93,169),
 ('FB2',135,169,90),('C10',155,180),('C12',175,180),('#FLG04',185,169),
 ('C3',43,209),('C4',75,209),('C5',107,209),('C6',139,209),
 ('U5',262,184),('C15',235,184),('R3',315,182),('R4',294,195,180),
 ('U3',51,269),('C1',26,278),('C2',78,278),('#FLG01',26,262),('#FLG02',51,292),
 ('U4',155,269),('C18',130,280),('C19',231,280),
 ('R7',181,275),('R8',181,293),('R9',207,293),('R10',231,293),('SW1',211,312),
 ('Q1',281,272),('R5',264,257),('R6',300,257),
 ('U6',354,269),('C20',332,280),('C21',393,280),('R16',377,280,90),
 ('SW2',425,269),('SW3',425,296)]
for a in placements:place(*a)
assert set(positions)==set(objs)
field('U5',268,169)
field('D1',61,52)
field('J2',355,58)
field('J3',355,89)
for d,x in [('D2',411),('D3',432),('D4',453)]:
 field(d,x,72)
 for prop in children(objs[d],'property'):
  if prop[1] in ['Reference','Value']:
   e=one(prop,'effects');e.remove(one(e,'justify'))
# 1. USB and protection: paired wires reach U1 around the outside of the clock.
connect(('J1','2'),('U1','6'),(77,46),(77,27),(189,27),(189,65))
connect(('J1','3'),('U1','7'),(56,48),(56,31),(185,31),(185,67))
connect(('D1','1'),('J1','3'),(56,62),(56,48))
connect(('D1','2'),('J1','2'),(77,62),(77,46))
rail([('J1','4'),('J1','SH'),('D1','3')],78,'distributed ground')
lab('USB_D-',(149,27));lab('USB_D+',(149,31))
# 2. Crystal and its load capacitors directly to the oscillator pins.
connect(('Y1','1'),('C13','1'),(100,52))
connect(('Y1','3'),('C14','1'),(124,52))
connect(('Y1','1'),('U1','1'),(100,52),(100,40),(141,40),(141,63))
connect(('Y1','3'),('U1','2'),(124,52),(124,44),(137,44),(137,65))
rail([('C13','2'),('C14','2'),('Y1','2'),('Y1','4')],70,'distributed ground')
connect(('R1','1'),('U1','5'),(118,71))
lead(('R1','2'),(118,85));lab('GND',(118,85),'distributed ground')
# Reset RC and internal 1.8 V output decoupling.
connect(('R2','2'),('C22','1'))
connect(('R2','2'),('U1','34'),(100,102),(135,102),(135,89))
connect(('U1','37'),('C7','1'),(139,95),(139,108),(125,108))
connect(('U1','38'),('C8','1'),(141,97),(141,114),(143,114))
rail([('C22','2'),('C7','2'),('C8','2')],128,'distributed ground')
lab('RESET_N',(100,102));lab('VCCA_1V8',(125,108));lab('VCORE_1V8',(141,114),right=True)
# 3. UART: four explicit lines. Existing pin order requires one unjoined X.
connect(('U1','13'),('U2','4'))
connect(('U1','14'),('U2','6'),(218,71),(220,73))
connect(('U1','15'),('U2','5'),(218,73),(220,71))
connect(('U1','16'),('U2','7'))
for k,x in [('13',196),('14',196),('15',196),('16',196)]:lab(n('U1',k),(x,p('U1',k)[1]))
# Supply decoupling connects to the actual IC pins; local direction ties are explicit.
rail([('C16','1'),('U2','1')],46,'distributed supply')
connect(('U2','2'),('U2','1'),(252,65),(252,63))
lead(('C16','2'),(244,59));lab('GND',(244,59),'distributed ground')
rail([('C17','1'),('U2','16')],42,'distributed supply')
lead(('C17','2'),(297,59));lab('GND',(297,59),'distributed ground')
connect(('U2','15'),('U2','14'),(288,65),(288,67))
lead(('U2','15'),(288,65),(303,65),(303,63));lab('PWREN_N',(303,63),'between functional blocks')
rail([('U2','8'),('U2','9')],82,'distributed ground')
# External signals and pull-ups; this pin order needs a second unjoined X.
connect(('U2','13'),('J2','2'))
connect(('U2','11'),('J2','3'),(330,73),(332,71))
connect(('U2','12'),('J3','1'),(330,71),(332,73),(340,73),(340,99))
connect(('U2','10'),('J3','2'),(290,75),(290,101))
connect(('R11','2'),('U2','11'),(302,89),(302,73))
connect(('R12','2'),('U2','10'),(322,101),(290,101),(290,75))
rail([('R11','1'),('R12','1')],79,'distributed supply')
for k,at in [('13',(308,69)),('11',(308,73)),('12',(342,99)),('10',(342,101))]:lab(n('U2',k),at)
lead(('J2','4'),(348,73),(348,80));lab('USB5V_OUT',(348,80),'between functional blocks')
# Ground and supply terminals stay explicit at the connector, with no confusing long returns.
lead(('J2','1'),(349,67),(349,61));lab('GND',(349,61),'distributed ground')
lead(('J3','3'),(349,103),(349,111));lab('GND',(349,111),'distributed ground')
# 4. Indicator branches, top supply to bottom sink.
for r,d in [('R13','D2'),('R14','D3'),('R15','D4')]:
 connect((r,'2'),(d,'2'))
 lead((d,'1'),(p(d,'1')[0],84));lab(n(d,'1'),(p(d,'1')[0],84),'sink in another block')
rail([('R14','1'),('R15','1')],44,'distributed supply')
for r in ['R13','R14','R15']:lab(n(r,'2'),(p(r,'2')[0],62))
lab('XTAL_IN',(100,40));lab('XTAL_OUT',(124,44));lab('REF12K',(135,71))
# 5. U1 supply bank: fixed library interleaves supplies and grounds; label the IC side.
for fb,c1,c2,flag in [('FB1','C9','C11','#FLG03'),('FB2','C10','C12','#FLG04')]:
 rail([(fb,'2'),(c1,'1'),(c2,'1'),(flag,'1')],169,'filtered rail to U1')
 rail([(c1,'2'),(c2,'2')],189,'distributed ground')
rail([(c,'1') for c in ['C3','C4','C5','C6']],199,'distributed supply')
rail([(c,'2') for c in ['C3','C4','C5','C6']],219,'distributed ground')
# 6. EEPROM: supply, DI/DO resistor, pull-up all directly visible.
rail([('U5','8'),('C15','1'),('R3','1')],174,'distributed supply')
rail([('U5','5'),('C15','2')],208,'distributed ground')
connect(('U5','3'),('R4','2'),(294,184));lab('EE_DATA',(294,184),'to U1')
connect(('U5','4'),('R4','1'),(278,186),(278,204),(294,204))
connect(('R3','2'),('R4','1'),(315,204),(294,204))
lab('EE_DO',(278,204))
# 7. Fixed 3.3 V with local EN tied visibly.
rail([('U3','1'),('C1','1'),('#FLG01','1')],262)
lab('USB5V',(31,262),'distributed supply')
connect(('U3','3'),('U3','1'),(41,269),(41,267))
rail([('U3','5'),('C2','1')],267,'distributed supply')
rail([('C1','2'),('U3','2'),('C2','2'),('#FLG02','1')],292,'distributed ground')
# 8. Adjustable regulator, divider and selector. Entire feedback loop is wired.
rail([('U4','1'),('C18','1')],262,'distributed supply')
rail([('U4','5'),('R7','1'),('C19','1')],267,'distributed supply')
rail([('R7','2'),('R8','1'),('R9','1'),('R10','1')],284)
connect(('U4','4'),('R7','2'),(170,271),(170,284),(181,284))
lab('FB',(171,284))
connect(('R9','2'),('SW1','2'),(207,301),(193,301),(193,312))
connect(('R10','2'),('SW1','4'),(231,303),(190,303),(190,314))
lab('FB_2V5',(198,301));lab('FB_3V3',(213,303))
# Common selector ground brought down beside divider, without label-only closure.
lead(('SW1','3'),(245,312),(245,319),(181,319))
lead(('R8','2'),(181,319));lead(('U4','2'),(155,319))
lead(('C18','2'),(130,319));lead(('C19','2'),(250,283),(250,319))
path('GND',(130,319),(250,319));lab('GND',(130,319),'distributed ground')
# 9. Gate / drain bias and inverter.
rail([('R5','1'),('R6','1')],246,'distributed supply')
connect(('R5','2'),('Q1','1'),(264,272));lab('PWREN_N',(264,272),'from U1')
connect(('R6','2'),('Q1','3'),(300,268));lab('PWR_EN',(300,268),'to U4 EN / U6 ON')
lead(('Q1','2'),(283,287));lab('GND',(283,287),'distributed ground')
# 10. Load switch and QOD resistor share output, followed by physical output selector.
rail([('U6','1'),('C20','1')],262,'distributed supply')
connect(('U6','6'),('SW2','3'),(400,267),(400,270))
connect(('U6','5'),('R16','1'),(365,271),(365,280))
lead(('R16','2'),(386,280),(386,267))
lead(('C21','1'),(393,267))
rail([('C20','2'),('U6','2'),('C21','2')],292,'distributed ground')
lab('USB5V_ENABLED',(387,267));lab('QOD',(365,280))
# Connect VIO to its separate output selector by a named inter-block supply.
# Preserve all unconnected pins; label only the remaining inter-block/global nodes.
fallback=[]
for key,(x,y,a) in pins.items():
 if key in used:continue
 net=nets.get(key)
 if not net or net.startswith('unconnected-'):
  s.append(['no_connect',['at',*point((x,y))],['uuid',uid()]]);continue
 ex=round(x-4*math.cos(math.radians(a)),6);ey=round(y+4*math.sin(math.radians(a)),6)
 path(net,(x,y),(ex,ey))
 reason='distributed ground' if net=='GND' else 'distributed supply' if net in ['USB5V','+3V3','VIO'] else 'between functional blocks'
 lab(net,(ex,ey),reason,a==0);fallback.append({'ref':key[0],'pin':key[1],'net':net,'reason':reason})
# Readable function headings and factual operating notes.
heading(16,19,193,'01  USB / CLOCK / FT232H')
heading(204,19,378,'02  UART TRANSLATION / EXTERNAL IO')
heading(393,19,454,'03  INDICATORS')
note(18,96,'J1 USB input / D1 ESD shunt',1.15)
note(18,101,'Data pair continues above the clock.',1.15)
note(91,135,'Clock, REF and RESET are wired to U1.',1.1)
note(91,140,'C7/C8 decouple U1 internal 1.8 V outputs.',1.1)
note(187,132,'# / _N = active low',1.1)
note(205,111,'TXD / RTS_N: host to target; RXD / CTS_N: target to host.',1.1)
note(205,116,'1DIR=3V3, 2DIR=GND. PWREN_N controls both OE# pins.',1.1)
note(205,121,'Crossed diagonals have no junction. Dots indicate joins.',1.1)
note(205,126,'J2: GND / TXD / RXD / USB5V_OUT',1.1)
note(205,131,'J3: RTS_N / CTS_N / GND / VIO_OUT',1.1)
note(396,96,'D2: USB power',1.1)
note(396,102,'D3/D4: U1 active-low sinks',1.1)
note(396,108,'EEPROM setup required',1.1)
heading(16,150,196,'04  FT232H SUPPLY FILTERS / DECOUPLING')
note(43,192,'VPHY -> U1.3',1.1);note(135,192,'VPLL -> U1.8',1.1)
note(23,224,'C3-C6: +3V3 for U1 VCCIO / VREGIN / VCCD.',1.15)
note(23,229,'U1 supply pins use labels to avoid an interleaved power/GND comb.',1.1)
heading(220,150,333,'05  EEPROM / CONFIGURATION')
note(225,216,'EE_DATA feeds DI; DO returns through R4. R3 pulls DO high.',1.1)
note(225,222,'EE_CS / EE_CLK connect to U1. UART / LED / PWREN setup pending.',1.1)
heading(349,150,454,'DRAWING CONVENTIONS')
note(350,164,'Local component relationships are drawn as wires.',1.15)
note(350,172,'Labels distribute supplies and cross block boundaries.',1.15)
note(350,180,'UART uses four discrete lines; no bus aliases are needed.',1.15)
note(350,188,'Existing symbol pin order and identities are retained.',1.15)
note(350,200,'Layout experiment V2; user review / approval pending.',1.15)
heading(16,243,93,'06  FIXED 3.3 V')
heading(112,243,252,'07  VIO REGULATOR / SELECTOR')
heading(258,237,313,'08  POWER ENABLE')
heading(325,243,454,'09  SWITCHED HEADER POWER')
note(20,305,'USB5V -> fixed 3.3 V',1.1)
note(20,311,'EN follows VIN.',1.1)
note(115,324,'SW1: open = 1.8 V / R9 = 2.5 V / R10 = 3.3 V. Switch with USB unplugged.',1.0)
note(260,299,'PWREN_N low:',1.1)
note(260,305,'Q1 off -> PWR_EN high.',1.1)
note(260,311,'Enables U4 and U6.',1.1)
note(350,212,'SW2 controls USB5V_OUT; SW3 controls VIO_OUT.',1.1)
note(350,218,'SW3 does not isolate the UART signal supply VIO.',1.1)
# Split collinear segments, then put dots only at electrically joined branches.
points=defaultdict(set)
for a,b,net in segments:points[net].update([a,b])
for key,(x,y,a) in pins.items():
 if key in nets:points[nets[key]].add((x,y))
edges=set()
for a,b,net in segments:
 dx=b[0]-a[0];dy=b[1]-a[1];length=dx*dx+dy*dy
 on=[]
 for q in points[net]:
  cross=(q[0]-a[0])*dy-(q[1]-a[1])*dx;dot=(q[0]-a[0])*dx+(q[1]-a[1])*dy
  if abs(cross)<1e-6 and -1e-6<=dot<=length+1e-6:on.append((dot,q))
 on.sort()
 for (_,u),(_,v) in zip(on,on[1:]):
  if u!=v:edges.add((min(u,v),max(u,v),net))
adj=defaultdict(set)
pinset={(p(*k),net) for k,net in nets.items() if k in pins}
for a,b,net in sorted(edges):
 s.append(['wire',['pts',['xy',*point(a)],['xy',*point(b)]],['stroke',['width',.1524],['type','default']],['uuid',uid()]])
 adj[(a,net)].add(b);adj[(b,net)].add(a)
for (a,net),v in adj.items():
 if len(v)>=3 or (len(v)==2 and (a,net) in pinset):
  s.append(['junction',['at',*point(a)],['diameter',.762],['color',0,0,0,0],['uuid',uid()]])
# Lift the power row within the printable area, preserving all endpoint coincidences.
for obj in s:
 if not isinstance(obj,list) or obj[0] not in ['symbol','wire','label','junction','no_connect','text','polyline']:continue
 at=one(obj,'at')
 if at and float(at[2])>=mm(237):
  at[2]=round(float(at[2])-mm(8),4)
  if obj[0]=='symbol':
   for prop in children(obj,'property'):
    pa=one(prop,'at');pa[2]=round(float(pa[2])-mm(8),4)
 pts=one(obj,'pts')
 if pts and all(float(q[2])>=mm(237) for q in pts[1:]):
  for q in pts[1:]:q[2]=round(float(q[2])-mm(8),4)

# Metadata uses final page coordinates, after the power-row shift.
positions={r:[round(float(one(o,'at')[1])/1.27,6),round(float(one(o,'at')[2])/1.27,6),float(one(o,'at')[3])] for r,o in objs.items()}
for record in label_reasons:
 if record['at'][1]>=237:record['at']=[record['at'][0],record['at'][1]-8]

assert one(s,'lib_symbols')==one(orig,'lib_symbols')
target.write_text(dump(s),encoding='utf-8')
(H/'drawing.json').write_text(json.dumps({'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'labels':len(children(s,'label')),'wires':len(edges),'buses':len(children(s,'bus')),'junctions':len(children(s,'junction')),'directly_routed_pin_endpoints':len(used),'remaining_label_pin_connections':fallback,'label_purposes':label_reasons,'positions_grid_1_27mm':positions},indent=2),encoding='utf-8')
print('V2 written from V0; validate netlist and render before accepting.')
