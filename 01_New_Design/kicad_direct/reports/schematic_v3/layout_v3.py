"""V3 presentation edit. Reads immutable V2 snapshot, never regenerates original design."""
from pathlib import Path
import sys,math,uuid,json,hashlib,copy,os
from collections import defaultdict
import xml.etree.ElementTree as ET
H=Path(__file__).resolve().parent;R=H.parents[1]
sys.path.insert(0,str(R/'scripts'));from sexpr import *
if '--apply' not in sys.argv:raise SystemExit('Use --apply')
sha=lambda b:hashlib.sha256(b).hexdigest()
target=R/'a2_usb_uart.kicad_sch';baseline=H/'before/a2_usb_uart.kicad_sch'
allowed={sha(baseline.read_bytes())}
if (H/'drawing.json').exists():allowed.add(json.loads((H/'drawing.json').read_text())['sha256'])
assert sha(target.read_bytes()) in allowed,'Unrecorded manual edits; refusing overwrite'
s=parse(baseline.read_text(encoding='utf-8-sig'));orig=copy.deepcopy(s)
objs={one(x,'property')[2]:x for x in children(s,'symbol')}
libs={x[1]:x for x in children(one(s,'lib_symbols'),'symbol')}
nets={(x.attrib['ref'],x.attrib['pin']):n.attrib['name'].removeprefix('/') for n in ET.parse(H/'before/netlist.xml').findall('.//nets/net') for x in n.findall('node')}
for i,nm in enumerate(['USB5V','GND','VPHY','VPLL'],1):nets[(f'#FLG0{i}','1')]=nm
pins={};used=set();segments=[];annotations=[];positions={};label_reasons=[]
exec(compile((H/'drawing_helpers.py').read_text(),str(H/'drawing_helpers.py'),'exec'))
for ref,o in objs.items():
 x,y,a=map(float,one(o,'at')[1:]);place(ref,x/1.27,y/1.27,a)
# Classify V2 wire segments by original pin identities / labels; non-junction X crossings stay separate.
old_edges=[tuple(tuple(round(float(z)/1.27,6) for z in q[1:]) for q in one(w,'pts')[1:]) for w in children(s,'wire')]
old_points={q for e in old_edges for q in e}|{p(*k) for k in pins}
parent={q:q for q in old_points}
def find(q):
 while parent[q]!=q:parent[q]=parent[parent[q]];q=parent[q]
 return q
for a,b in old_edges:
 dx=b[0]-a[0];dy=b[1]-a[1];ll=dx*dx+dy*dy
 for q in old_points:
  if abs((q[0]-a[0])*dy-(q[1]-a[1])*dx)<1e-5 and -1e-5<=(q[0]-a[0])*dx+(q[1]-a[1])*dy<=ll+1e-5:parent[find(q)]=find(a)
roots=defaultdict(set)
for k in pins:
 if k in nets:roots[find(p(*k))].add(nets[k])
for o in children(s,'label'):
 q=tuple(round(float(v)/1.27,6) for v in one(o,'at')[1:3])
 if q in parent:roots[find(q)].add(str(o[1]))
assert all(len(v)==1 for v in roots.values()),roots
classified=[(a,b,next(iter(roots[find(a)]))) for a,b in old_edges]
powernets={'GND','USB5V','+3V3','VIO','VPHY','VPLL','VCCA_1V8','VCORE_1V8','USB5V_ENABLED','USB5V_OUT','VIO_OUT'}
redrawnets=powernets|{'USB_D+','USB_D-','XTAL_IN','XTAL_OUT','REF12K','RESET_N'}
# Retain V2 UART, EEPROM data and LED local wiring, with exact geometry.
segments=[(a,b,nm) for a,b,nm in classified if nm not in redrawnets and max(a[1],b[1])<230 and not(nm=='EE_CS' and a[1]>150)]
labels=[copy.deepcopy(o) for o in children(s,'label') if o[1] not in redrawnets and float(one(o,'at')[2])/1.27<230 and not(o[1]=='EE_CS' and float(one(o,'at')[2])/1.27>150)]
s[:]=[o for o in s if not isinstance(o,list) or o[0] not in ['wire','junction','label','text','polyline','no_connect']]
s.extend(labels)
for r,x,y,a in [
 ('D1',28,70,0),('Y1',105,42,0),('C13',93,51,0),('C14',117,51,0),('R1',140,77,0),
 ('R2',45,126,0),('C22',45,142,0),('C7',158,126,0),('C8',178,126,0),
 ('FB1',55,83,90),('C9',75,91,0),('C11',95,91,0),('#FLG03',112,83,0),
 ('FB2',55,107,90),('C10',75,115,0),('C12',95,115,0),('#FLG04',112,107,0),
 ('C3',83,149,0),('C4',101,149,0),('C5',119,149,0),('C6',137,149,0),
 ('C15',244,184,0),('C16',244,56,0),('C17',297,56,0),
 ('U3',65,187,0),('C1',45,193,0),('C2',88,193,0),('#FLG01',31,178,0),('#FLG02',34,202,0),
 ('U4',65,232,0),('C18',45,242,0),('C19',84,241,0),
 ('R7',95,239,0),('R8',95,259,0),('R9',120,259,0),('R10',145,259,0),('SW1',128,279,0),
 ('U6',65,294,0),('C20',45,301,0),('C21',95,299,0),('R16',113,311,90),('SW2',183,293,0),('SW3',210,231,0),
 ('Q1',288,270,0),('R5',271,255,0),('R6',307,255,0)]:place(r,x,y,a)
field('D1',22,59);field('J2',355,58);field('J3',355,89);field('U5',268,169)
for d,x in [('D2',411),('D3',432),('D4',453)]:
 field(d,x,72)
 for prop in children(objs[d],'property'):
  if prop[1] in ['Reference','Value']:one(prop,'effects').remove(one(one(prop,'effects'),'justify'))
# Custom global power symbols, pin name fixed per net. Existing symbol definitions untouched.
local=['kicad_symbol_lib',['version','20241209'],['generator','a2_v3_presentation']]
def make_lib(name,net,gnd=False):
 o=['symbol',Q(name),['power','global'],['pin_numbers',['hide','yes']],['pin_names',['offset',0],['hide','yes']],['in_bom','no'],['on_board','no'],
 ['property',Q('Reference'),Q('#PWR'),['at',0,0,0],['effects',['font',['size',1.27,1.27]],['hide','yes']]],
 ['property',Q('Value'),Q(net),['at',0,4.445,0],['effects',['font',['size',1.27,1.27]]]]]
 stroke=['stroke',['width',.2032],['type','default']]
 if gnd:
  shape=['symbol',Q(name+'_0_1'),['polyline',['pts',['xy',0,0],['xy',0,-.381]],copy.deepcopy(stroke),['fill',['type','none']]],['polyline',['pts',['xy',-1.016,-.381],['xy',1.016,-.381],['xy',0,-1.524],['xy',-1.016,-.381]],copy.deepcopy(stroke),['fill',['type','none']]]]
 else:
  shape=['symbol',Q(name+'_0_1'),['polyline',['pts',['xy',0,0],['xy',0,1.27]],copy.deepcopy(stroke),['fill',['type','none']]],['circle',['center',0,2.286],['radius',1.016],copy.deepcopy(stroke),['fill',['type','none']]],['polyline',['pts',['xy',-1.778,2.286],['xy',1.778,2.286]],copy.deepcopy(stroke),['fill',['type','none']]]]
 o.extend([shape,['symbol',Q(name+'_1_1'),['pin','power_in','line',['at',0,0,270 if gnd else 90],['length',0],['name',Q(net),['effects',['font',['size',1.27,1.27]]]],['number',Q('1'),['effects',['font',['size',1.27,1.27]]]]]]])
 local.append(o);embedded=copy.deepcopy(o);embedded[1]=Q('A2_PowerV3:'+name);one(s,'lib_symbols').append(embedded);libs[embedded[1]]=embedded
 return embedded[1]
libmap={nm:make_lib('GND_Triangle' if nm=='GND' else 'Rail_'+nm.replace('+','').replace('-','_'),nm,nm=='GND') for nm in sorted(powernets)}
new_symbols=[];symbol_points=set()
def power(nm,at,show=True):
 if (nm,at) in symbol_points:return
 symbol_points.add((nm,at));ref=f'#PWR{len(new_symbols)+101:04d}';id=uid();x,y=point(at)
 valy=y+(3.0 if nm=='GND' else -4.5)
 e=['effects',['font',['size',1.14,1.14]]]
 if not show or nm=='GND':e.append(['hide','yes'])
 o=['symbol',['lib_id',Q(libmap[nm])],['at',x,y,0],['unit',1],['in_bom','no'],['on_board','no'],['dnp','no'],['uuid',id],
 ['property',Q('Reference'),Q(ref),['at',x,y,0],['effects',['font',['size',1.27,1.27]],['hide','yes']]],
 ['property',Q('Value'),Q(nm),['at',x,valy,0],e],['pin',Q('1'),['uuid',uid()]],
 ['instances',['project',Q('a2_usb_uart'),['path',Q('/'+str(one(s,'uuid')[1])),['reference',Q(ref)],['unit',1]]]]]
 s.append(o);new_symbols.append({'reference':ref,'net':nm,'at':at});pins[(ref,'1')]=(*at,270 if nm=='GND' else 90);nets[(ref,'1')]=nm
 return o
def ground(r,k=2,dx=0,dy=2):
 q=p(r,k);end=(q[0]+dx,q[1]+dy)
 if dx:lead((r,k),(end[0],q[1]),end)
 else:lead((r,k),end)
 power('GND',end)
def supply_pin(r,k,dx=-4,dy=0):
 q=p(r,k);end=(q[0]+dx,q[1]+dy);lead((r,k),(end[0],q[1]),end);power(n(r,k),end)
# USB pair, 100 mil separation throughout the long overhead run.
connect(('J1','2'),('U1','6'),(60,46),(60,27),(189,27),(189,65))
connect(('J1','3'),('U1','7'),(58,48),(58,29),(187,29),(187,67))
connect(('D1','2'),('J1','2'),(60,70),(60,46))
connect(('D1','1'),('J1','3'),(16,70),(16,58),(58,58),(58,48))
lab('USB_D-',(151,27));lab('USB_D+',(151,29))
supply_pin('J1',1,8)
# Crystal pair, also 100 mil apart; distinct circuit, no implied PCB matching constraint.
connect(('Y1','1'),('C13','1'),(93,42))
connect(('Y1','3'),('C14','1'),(117,42))
connect(('Y1','1'),('U1','1'),(93,42),(93,32),(137,32),(137,63))
connect(('Y1','3'),('U1','2'),(117,42),(117,34),(139,34),(139,65))
lab('XTAL_IN',(105,32));lab('XTAL_OUT',(119,34))
connect(('R1','1'),('U1','5'),(140,71));lab('REF12K',(142,71))
connect(('R2','2'),('C22','1'))
connect(('R2','2'),('U1','34'),(45,132),(122,132),(122,89));lab('RESET_N',(48,132))
supply_pin('R2',1,0,-3)
connect(('U1','37'),('C7','1'),(139,95),(139,116),(158,116));power('VCCA_1V8',(158,116))
connect(('U1','38'),('C8','1'),(141,97),(141,120),(178,120));power('VCORE_1V8',(178,120))
# Filter branches physically next to U1, actual pins connected with wires.
for fb,c1,c2,fl,yy,pin,xx in [('FB1','C9','C11','#FLG03',83,'3',135),('FB2','C10','C12','#FLG04',107,'8',137)]:
 rail([(fb,'2'),(c1,'1'),(c2,'1'),(fl,'1')],yy)
 connect((fb,'2'),('U1',pin),(xx,yy),(xx,p('U1',pin)[1]))
 supply_pin(fb,1,-6);power(n(fb,2),(106,yy));path(n(fb,2),(106,yy),(112,yy))
# All +3V3 pins collected locally; capacitors sit on its visibly connected branch.
for k in ['12','24','39','40','46']:lead(('U1',k),(143,p('U1',k)[1]))
path('+3V3',(143,81),(143,139),(83,139));power('+3V3',(83,139))
for r in ['C3','C4','C5','C6']:lead((r,'1'),(p(r,'1')[0],139))
# U2 caps: source, capacitor tap, then IC pin. Keep DIR and UART routing from V2.
path('+3V3',(238,49),(244,49),(252,49),(252,63),p('U2','1'))
lead(('C16','1'),(244,49));power('+3V3',(238,49))
connect(('U2','2'),('U2','1'),(252,65),(252,63))
path('VIO',(303,49),(297,49),(288,49),(288,63),p('U2','16'))
lead(('C17','1'),(297,49));power('VIO',(303,49))
rail([('R11','1'),('R12','1')],79);power('VIO',(314,79))
lead(('J2','4'),(348,73),(348,84),(354,84));power('USB5V_OUT',(354,84))
lead(('J3','4'),(342,105),(342,119),(350,119));power('VIO_OUT',(350,119))
# Indicator supplies and EEPROM supply-to-capacitor-to-pin route.
supply_pin('R13','1',0,-5);rail([('R14','1'),('R15','1')],44);power('+3V3',(425,44))
rail([('C15','1'),('U5','8'),('R3','1')],174);power('+3V3',(238,174));path('+3V3',(238,174),(244,174))
lead(('U5','1'),(252,182),(252,177));lab('EE_CS',(252,177),right=True)
# Actual power tree: three PARALLEL branches from USB5V, not a cascade of regulators.
path('USB5V',(24,178),(24,292));path('USB5V',(24,178),(31,178));power('USB5V',(24,178))
for ic,cap,yy in [('U3','C1',185),('U4','C18',230),('U6','C20',292)]:
 path('USB5V',(24,yy),(45,yy),p(ic,'1'));lead((cap,'1'),(45,yy))
connect(('U3','3'),('U3','1'),(54,187),(54,185))
connect(('U3','5'),('C2','1'),(88,185));path('+3V3',p('U3','5'),(106,185));power('+3V3',(106,185))
connect(('U4','5'),('R7','1'),(95,230));path('VIO',p('U4','5'),(174,230),(190,230),(190,232),p('SW3','3'))
lead(('C19','1'),(84,230));power('VIO',(174,230))
rail([('R7','2'),('R8','1'),('R9','1'),('R10','1')],249)
connect(('U4','4'),('R7','2'),(80,234),(80,249),(95,249));lab('FB',(82,249))
connect(('R9','2'),('SW1','2'),(120,269),(110,269),(110,279))
connect(('R10','2'),('SW1','4'),(145,272),(106,272),(106,281))
lab('FB_2V5',(112,269));lab('FB_3V3',(133,272))
lead(('U4','3'),(54,232));lab('PWR_EN',(54,232),right=True)
supply_pin('SW3','2',10)
connect(('U6','6'),('SW2','3'),(160,292),(160,294))
lead(('C21','1'),(95,292));connect(('U6','5'),('R16','1'),(85,296),(85,311))
lead(('R16','2'),(125,311),(125,292));lab('QOD',(86,311));power('USB5V_ENABLED',(138,292))
supply_pin('SW2','2',14)
lead(('U6','3'),(52,296));lab('PWR_EN',(52,296),right=True)
# Q1 unchanged inverter, repositioned outside the actual power tree.
rail([('R5','1'),('R6','1')],244);power('+3V3',(271,244))
connect(('R5','2'),('Q1','1'),(271,270));lab('PWREN_N',(271,270))
connect(('R6','2'),('Q1','3'),(307,266));lab('PWR_EN',(307,266))
# Explicit ERC drive declarations after passive mechanical selectors, separate from rail graphics.
for ref,xx,yy,nm in [('#FLG05',201,293,'USB5V_OUT'),('#FLG06',228,231,'VIO_OUT')]:
 o=copy.deepcopy(objs['#FLG01']);one(o,'uuid')[1]=uid();one(o,'property')[2]=Q(ref)
 for pin in children(o,'pin'):one(pin,'uuid')[1]=uid()
 for project in children(one(o,'instances'),'project'):
  for pa in children(project,'path'):one(pa,'reference')[1]=Q(ref)
 objs[ref]=o;s.append(o);nets[(ref,'1')]=nm;place(ref,xx,yy,180)
# Move the 1.8V annotation out of the U1 body, keeping its power symbol on the net.
for o in children(s,'symbol'):
 if one(o,'lib_id')[1]==libmap['VCCA_1V8']:
  one(children(o,'property')[1],'at')[1:]=[*point((166,117)),0]
# Short local GNDs. Consecutive U1 ground pins share only a nearby stub.
grounded=set()
for ks in [['4'],['9','10','11'],['22','23'],['35','36'],['41','42'],['47','48']]:
 yy=[p('U1',k)[1] for k in ks]
 for k in ks:lead(('U1',k),(150,p('U1',k)[1]));grounded.add(('U1',k))
 path('GND',(150,min(yy)),(150,max(yy)));power('GND',(150,max(yy)))
connect(('J1','4'),('J1','SH'),(45,50),(45,52));lead(('J1','SH'),(45,52),(45,54));power('GND',(45,54));grounded.update([('J1','4'),('J1','SH')])
# The GND flag is an existing drive declaration, not a replacement for the ground graphic.
power('GND',p('#FLG02','1'));grounded.add(('#FLG02','1'))
for key in list(pins):
 if key in grounded or key[0].startswith('#PWR') or nets.get(key)!='GND':continue
 r,k=key
 if r=='Y1' and k=='4':continue
 if r=='U2' and k=='3':ground(r,k,-3,0)
 elif r=='J2':
  lead((r,k),(349,67),(349,65),(347,65));power('GND',(347,65))
 elif r=='J3':ground(r,k,-3,7)
 elif r=='SW1':ground(r,k,4,3)
 elif r=='U2':ground(r,k,(-3 if k=='8' else 3),3)
 else:ground(r,k,0,2)
# Recreate only the original no-connects at their moved pin locations.
for k in list(pins):
 if nets.get(k,'').startswith('unconnected-'):s.append(['no_connect',['at',*point(p(*k))],['uuid',uid()]])
# Functional headings and a concise, electrically faithful explanation of the tree.
heading(16,19,193,'01  USB / CLOCK / FT232H')
heading(204,19,378,'02  UART TRANSLATION / EXTERNAL IO')
heading(393,19,454,'03  INDICATORS')
note(18,156,'C9/C11 -> VPHY; C10/C12 -> VPLL. C3-C6 -> U1 3V3 pins.',1.05)
note(18,161,'C7/C8 -> internal 1.8 V outputs. Place decouplers at their IC pins on PCB.',1.05)
note(205,114,'TXD / RTS_N: host to target; RXD / CTS_N: target to host.',1.1)
note(205,120,'Crossed diagonals have no junction. Dots indicate joins.',1.1)
note(205,126,'1DIR=3V3; 2DIR=GND; PWREN_N drives both OE# pins.',1.1)
note(396,96,'D2: USB power',1.1);note(396,102,'D3/D4: U1 active-low sinks',1.1)
heading(16,168,227,'04  POWER TREE: THREE BRANCHES FROM USB5V')
note(111,191,'U3: fixed +3V3 -> U1 / U2 VCCA / EEPROM / control',1.05)
note(111,197,'EN tied to input. VPHY / VPLL are filtered +3V3 branches.',1.05)
note(166,253,'U4: variable VIO -> U2 VCCB',1.1)
note(166,259,'SW3 switches the header supply only.',1.1)
note(166,265,'UART VIO remains connected.',1.1)
note(78,286,'SW1: open=1.8V / R9=2.5V / R10=3.3V',1.05)
note(48,316,'U6: USB 5V load switch. R16 discharges OUT via QOD; SW2 controls the header.',1.05)
heading(220,150,333,'05  EEPROM / CONFIGURATION')
note(225,211,'EE_DATA -> DI; DO returns through R4. R3 pulls DO high.',1.1)
note(225,218,'EEPROM UART / LED / PWREN setup remains pending.',1.1)
heading(254,232,333,'06  POWER ENABLE')
note(260,289,'PWREN_N low -> Q1 off -> PWR_EN high.',1.1)
note(260,295,'PWR_EN enables U4 and U6 in parallel.',1.1)
heading(349,150,454,'POWER / DRAWING NOTES')
note(350,166,'Circle with bar = named global power net.',1.1)
note(350,174,'Downward triangle = GND (same net everywhere).',1.1)
note(350,186,'USB and crystal pairs are drawn together for clarity.',1.1)
note(350,194,'This does not impose equal PCB routing constraints.',1.1)
note(350,206,'USB5V -> U3 -> +3V3 -> FB1 / FB2 -> VPHY / VPLL',1.05)
note(350,214,'USB5V -> U4 -> VIO -> SW3 -> VIO_OUT',1.05)
note(350,222,'USB5V -> U6 -> USB5V_ENABLED -> SW2 -> USB5V_OUT',1.05)
note(350,238,'Local GNDs shorten return wiring on this drawing.',1.1)
note(350,246,'Existing part / pin identities and circuit are retained.',1.1)
note(350,254,'Flags after SW2/SW3 declare drive with the switch ON.',1.05)
note(350,262,'ERC does not verify switch state or actual power delivery.',1.05)
note(350,274,'V3 presentation experiment. User approval pending.',1.1)
# Split only within each known net. Mechanical verification detects any unintended contacts.
points=defaultdict(set)
for a,b,nm in segments:points[nm].update([a,b])
for k in pins:
 if k in nets:points[nets[k]].add(p(*k))
edges=set()
for a,b,nm in segments:
 dx=b[0]-a[0];dy=b[1]-a[1];ll=dx*dx+dy*dy;on=[]
 for q in points[nm]:
  cross=(q[0]-a[0])*dy-(q[1]-a[1])*dx;dot=(q[0]-a[0])*dx+(q[1]-a[1])*dy
  if abs(cross)<1e-5 and -1e-5<=dot<=ll+1e-5:on.append((dot,q))
 on.sort()
 for (_,u),(_,v) in zip(on,on[1:]):
  if u!=v:edges.add((min(u,v),max(u,v),nm))
adj=defaultdict(set);pinset={(p(*k),nm) for k,nm in nets.items() if k in pins}
for a,b,nm in sorted(edges):
 s.append(['wire',['pts',['xy',*point(a)],['xy',*point(b)]],['stroke',['width',.1524],['type','default']],['uuid',uid()]])
 adj[(a,nm)].add(b);adj[(b,nm)].add(a)
for (a,nm),v in adj.items():
 if len(v)>=3 or (len(v)==2 and (a,nm) in pinset):s.append(['junction',['at',*point(a)],['diameter',.762],['color',0,0,0,0],['uuid',uid()]])
(R/'libraries/A2_PowerV3.kicad_sym').write_text(dump(local),encoding='utf-8')
table=parse((R/'sym-lib-table').read_text());table[:]=[o for o in table if not(isinstance(o,list) and o[0]=='lib' and one(o,'name')[1]=='A2_PowerV3')]
table.append(['lib',['name',Q('A2_PowerV3')],['type',Q('KiCad')],['uri',Q('${KIPRJMOD}/libraries/A2_PowerV3.kicad_sym')],['options',Q('')],['descr',Q('V3 global power graphics; no functional parts')]])
(R/'sym-lib-table').write_text(dump(table),encoding='utf-8')
target.write_text(dump(s),encoding='utf-8')
(H/'drawing.json').write_text(json.dumps({'sha256':sha(target.read_bytes()),'power_symbols':new_symbols,'positions':positions,'v2_classified_wires':classified,'v3_classified_wires':sorted(edges),'pins':{r+'.'+k: {'at':p(r,k),'net':nets.get((r,k))} for r,k in pins}},indent=2))
print('V3 drawn. Validation required.')
