"""Layout-only experiment. Reads the preserved schematic, never the design generator."""
import sys, math, uuid, json, copy, hashlib
from pathlib import Path
import xml.etree.ElementTree as ET
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from sexpr import parse,dump,children,one,Q
BASE=HERE/'before/a2_usb_uart.kicad_sch'
if '--apply' not in sys.argv:
    raise SystemExit('Use --apply only to replay this layout experiment; existing manual edits are protected.')
target=ROOT/'a2_usb_uart.kicad_sch'
expected={hashlib.sha256(BASE.read_bytes()).hexdigest()}
if (HERE/'layout_metrics.json').exists():
    expected.add(json.loads((HERE/'layout_metrics.json').read_text(encoding='utf-8')).get('output_sha256'))
if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() not in expected:
    raise SystemExit('Refusing to overwrite a schematic modified after the recorded experiment.')
s=parse(BASE.read_text(encoding='utf-8-sig'))
original=copy.deepcopy(s)
symbols={one(v,'property')[2]:v for v in children(s,'symbol')}
libs={a[1]:a for a in children(one(s,'lib_symbols'),'symbol')}
nets={}
for n in ET.parse(HERE/'before/netlist.xml').findall('.//nets/net'):
    for t in n.findall('node'):nets[(t.attrib['ref'],t.attrib['pin'])]=n.attrib['name'].removeprefix('/')
for i,n in enumerate(['USB5V','GND','VPHY','VPLL'],1):nets[(f'#FLG0{i}','1')]=n
s[:]=[v for v in s if not isinstance(v,list) or v[0] not in ['wire','label','junction','no_connect','text','polyline']]
def uid():return Q(str(uuid.uuid4()))
def snap(x):return round(round(x/1.27)*1.27,4)
def xy(x,y):return [snap(x),snap(y)]
def eff(size=1.27,justify=None):
    e=['effects',['font',['size',size,size]]]
    if justify:e.append(['justify',*justify])
    return e
def text(x,y,value,size=1.27):
    s.append(['text',Q(value),['at',*xy(x,y),0],eff(size,['left','bottom']),['uuid',uid()]])
def line(a,b,net=None):
    a=tuple(round(v,4) for v in a);b=tuple(round(v,4) for v in b)
    if a==b:return
    s.append(['wire',['pts',['xy',*a],['xy',*b]],['stroke',['width',0.1524],['type','default']],['uuid',uid()]])
    segments.append((a,b,net))
def label(n,a,side='left'):
    s.append(['label',Q(n),['at',*a,0],eff(1.27,[side,'bottom']),['uuid',uid()]])
def junction(a):
    if tuple(a) not in junc:
        junc.add(tuple(a));s.append(['junction',['at',*a],['diameter',0.762],['color',0,0,0,0],['uuid',uid()]])
def pinlist(ref):
    return [v for u in children(libs[one(symbols[ref],'lib_id')[1]],'symbol') for v in children(u,'pin')]
positions={};pins={};used=set();segments=[];junc=set()
def place(ref,x,y,angle=0):
    obj=symbols[ref];x,y=xy(x,y);a=one(obj,'at');a[1:]=[x,y,angle]
    positions[ref]=(x,y,angle)
    theta=math.radians(angle)
    pp=[]
    for pin in pinlist(ref):
        dx,dy,pa=map(float,one(pin,'at')[1:])
        px=round(x+dx*math.cos(theta)-dy*math.sin(theta),4)
        py=round(y-dx*math.sin(theta)-dy*math.cos(theta),4)
        number=str(one(pin,'number')[1])
        pins[(ref,number)]=(px,py,(pa+angle)%360);pp.append((px,py))
    # Keep all property values and component identities; change only their display.
    for prop in children(obj,'property'):
        key=prop[1];at=one(prop,'at');at[1:]=[x,y,0]
        e=one(prop,'effects');e[:]=eff(1.27)
        if key not in ['Reference','Value'] or ref.startswith('#'):
            e.append(['hide','yes']);continue
        if ref.startswith(('R','C','FB')) and angle in [0,180]:
            at[1:]=[round(x+2.54,4),round(y+(-1.27 if key=='Reference' else 1.27),4),0]
            e.append(['justify','left'])
        elif ref=='Q1':
            at[1:]=[round(x+6.35,4),round(y+(-1.27 if key=='Reference' else 1.27),4),0]
            e.append(['justify','left'])
        else:
            # Actual library rectangle bounds, transformed into page coordinates.
            ys=[p[1] for p in pp]
            for unit in children(libs[one(obj,'lib_id')[1]],'symbol'):
                for rect in children(unit,'rectangle'):
                    for end in ['start','end']:
                        dx,dy=map(float,one(rect,end)[1:])
                        ys.append(y-dx*math.sin(theta)-dy*math.cos(theta))
            top=min(ys)
            at[1:]=[x,round(top-(5.08 if key=='Reference' else 2.54),4),0]
    for prop in children(obj,'property'):
        if prop[1] in ['Reference','Value']:
            one(prop,'at')[3]=90 if angle in (90,270) else 0
            if angle==180 and ref.startswith(('R','C','FB')):
                just=one(one(prop,'effects'),'justify')
                if just:just[1]='right'
    for prop in children(obj,'property'):
        if prop[1] not in ['Reference','Value']:continue
        at=one(prop,'at')
        if angle==90 or ref in ['D2','D3','D4']:at[2]=round(float(at[2])-3.81,4)
        if ref=='U5':
            at[1]=round(x+8.89,4)
            one(prop,'effects').append(['justify','left'])
def p(ref,num):return pins[(ref,str(num))][:2]
def net(ref,num):return nets[(ref,str(num))]
def wire(ref,num,points,end_ref=None,end_num=None,tag=True):
    key=(ref,str(num));n=nets[key]
    if end_ref:
        assert n==net(end_ref,end_num),(key,(end_ref,end_num))
        points=[*points,p(end_ref,end_num)];used.add((end_ref,str(end_num)))
    coords=[p(ref,num),*points]
    for a,b in zip(coords,coords[1:]):line(a,b,n)
    used.add(key)
    if tag:label(n,coords[-1])
def rail(keys,y,tag=True):
    y=snap(y);n=net(*keys[0]);pts=[]
    for r,k in keys:
        assert net(r,k)==n,(keys,n,net(r,k))
        a=p(r,k);b=(a[0],y);line(a,b,n);pts.append(b);used.add((r,str(k)))
    xs=sorted(set(a[0] for a in pts))
    for x1,x2 in zip(xs,xs[1:]):line((x1,y),(x2,y),n)
    for a in pts:
        if len(xs)>1 and xs[0]<a[0]<xs[-1]:junction(a)
    if tag:label(n,(xs[0],y))
def block(x1,y1,x2,y2,title,subtitle=None):
    # Graphic rules do not carry electrical connections.
    points=[xy(x1,y1),xy(x2,y1)]
    s.append(['polyline',['pts',*[['xy',*a] for a in points]],['stroke',['width',.254],['type','default']],['fill',['type','none']],['uuid',uid()]])
    text(x1,y1-2.54,title,1.8)
    if subtitle:text(x1,y1+6.35,subtitle,1.05)
# Main signal path, readable left to right.
for args in [
 ('J1',35,75),('D1',80,105),('U1',160,95),('U2',300,73.66),
 ('J2',410,74.93),('J3',410,106.68),
 ('C16',260,128),('C17',290,128),('R11',340,128),('R12',380,128),
 ('R13',475,65,90),('D2',505,65,180),('R14',475,95,90),('D3',505,95,180),('R15',475,125,90),('D4',505,125,180),
 ('Y1',45,205),('C13',30,220),('C14',60,220),('R1',95,210),
 ('R2',135,200),('C22',135,220),('FB1',185,190,90),('C9',200,202),('C11',220,202),
 ('FB2',185,235,90),('C10',200,247),('C12',220,247),
 ('C3',30,260),('C4',55,260),('C5',80,260),('C6',105,260),('C7',140,260),('C8',165,260),
 ('U5',290,217),('C15',260,217),('R4',325,228,180),('R3',345,228),
 ('Q1',410,220),('R5',390,205),('R6',430,205),
 ('U3',65,320),('C1',30,330),('C2',100,330),
 ('U4',200,320),('C18',180,330),('C19',255,325),('R7',235,326),('R8',235,348),
 ('R9',300,348),('R10',270,348),('SW1',335,370),
 ('U6',425,320),('C20',395,330),('C21',480,335),('R16',450,335,90),
 ('SW2',530,320),('SW3',530,365),
 ('#FLG01',30,317.5),('#FLG02',45,230),('#FLG03',210,190),('#FLG04',210,235)
]:place(*args)
assert set(positions)==set(symbols),(set(symbols)-set(positions))
# USB connector and ESD share named data nets. No unrelated long cross-sheet wire.
rail([('J1','4'),('J1','SH')],90)
# Horizontal TXD and CTS paths are wired. RXD/RTS use matching labels to avoid crossover.
for a,b in [('13','4'),('16','7')]:
    A=p('U1',a);B=p('U2',b)
    assert A[1]==B[1],(A,B)
    wire('U1',a,[], 'U2',b,False);label(net('U1',a),(snap(235),A[1]))
# Direct UART data to J2; handshake is separately labelled for J3.
for a,b,x in [('13','2',365),('11','3',370)]:
    A=p('U2',a);B=p('J2',b);mx=snap(x)
    wire('U2',a,[(mx,A[1]),(mx,B[1])],'J2',b,False);label(net('U2',a),(snap(330),A[1]))
rail([('C16','2'),('C17','2')],142)
rail([('R11','1'),('R12','1')],116)
# LEDs: input rail -> resistor -> LED -> low-side sink.
for r,d in [('R13','D2'),('R14','D3'),('R15','D4')]:
    wire(r,'2',[],d,'2',False)
    label(net(r,'2'),(snap(490),p(r,'2')[1]))
# Crystal, load caps and common ground.
for yp,cap in [('1','C13'),('3','C14')]:
    a=p('Y1',yp);b=p(cap,'1');wire('Y1',yp,[(b[0],a[1])],cap,'1',False);label(net(cap,'1'),(b[0],a[1]))
rail([('C13','2'),('Y1','2'),('Y1','4'),('C14','2'),('#FLG02','1')],230)
wire('R2','2',[], 'C22','1',False);label('RESET_N',(p('R2','2')[0],snap(210)))
# Filtered analogue rails and decoupling close to their functional group.
for fb,c1,c2,flag,y,gy in [('FB1','C9','C11','#FLG03',190,213),('FB2','C10','C12','#FLG04',235,258)]:
    rail([(fb,'2'),(c1,'1'),(c2,'1'),(flag,'1')],y)
    rail([(c1,'2'),(c2,'2')],gy)
rail([(c,'1') for c in ['C3','C4','C5','C6']],250)
rail([(c,'2') for c in ['C3','C4','C5','C6','C7','C8']],273)
# EEPROM: DI directly to EE_DATA; DO through R4, with R3 pull-up.
rail([('U5','8'),('C15','1')],202)
rail([('U5','5'),('C15','2')],241)
a=p('U5','3');b=p('R4','2');wire('U5','3',[(b[0],a[1])],'R4','2',False);label('EE_DATA',(b[0],a[1]))
a=p('U5','4');y=snap(241);x=snap(310)
wire('U5','4',[(x,a[1]),(x,y),(p('R4','1')[0],y)],'R4','1',False)
wire('R3','2',[(p('R3','2')[0],y),(p('R4','1')[0],y)],'R4','1',False)
junction((p('R4','1')[0],y));label('EE_DO',(x,y))
# PWREN# inverter and its two bias resistors.
rail([('R5','1'),('R6','1')],193)
a=p('Q1','1');wire('R5','2',[(p('R5','2')[0],a[1])],'Q1','1',False);label('PWREN_N',(p('R5','2')[0],a[1]))
a=p('Q1','3');wire('R6','2',[(p('R6','2')[0],a[1])],'Q1','3',False);label('PWR_EN',(p('R6','2')[0],a[1]))
# Fixed 3.3 V LDO, input/output capacitors and enabled input.
y=p('U3','1')[1]
rail([('U3','1'),('C1','1'),('#FLG01','1')],y)
a=p('U3','3');x=snap(50);wire('U3','3',[(x,a[1]),(x,y)],tag=False);junction((x,y))
rail([('U3','5'),('C2','1')],y)
rail([('C1','2'),('U3','2'),('C2','2')],342)
# Adjustable VIO regulator, feedback divider and switched parallel resistors.
y=p('U4','1')[1]
rail([('U4','1'),('C18','1')],y)
rail([('U4','5'),('R7','1'),('C19','1')],y)
# FB node, deliberately drawn as a three-branch divider.
fy=snap(338)
rail([('R7','2'),('R8','1'),('R9','1'),('R10','1')],fy)
a=p('U4','4');x=snap(220);wire('U4','4',[(x,a[1]),(x,fy),(p('R7','2')[0],fy)],tag=False);junction((p('R7','2')[0],fy))
for r,pn in [('R9','2'),('R10','4')]:
    b=p('SW1',pn);wire(r,'2',[(p(r,'2')[0],b[1])],'SW1',pn,False);label(net(r,'2'),(p(r,'2')[0],b[1]))
# USB 5 V load switch, discharge resistor, output switch and capacitors.
y=p('U6','1')[1]
rail([('U6','1'),('C20','1')],y)
out_y=p('U6','6')[1];out_x=snap(465)
a=p('SW2','3');wire('U6','6',[(out_x,out_y),(out_x,a[1])],'SW2','3',False);label('USB5V_ENABLED',(snap(485),a[1]))
a=p('U6','5');b=p('R16','1');x=snap(440)
wire('U6','5',[(x,a[1]),(x,b[1])],'R16','1',False);label('QOD',(x,b[1]))
wire('R16','2',[(out_x,p('R16','2')[1]),(out_x,out_y)],tag=False)
junction((out_x,out_y))
wire('C21','1',[(p('C21','1')[0],p('SW2','3')[1])],tag=False);junction((p('C21','1')[0],p('SW2','3')[1]))
rail([('C20','2'),('U6','2'),('C21','2')],351)
# Add short named connections for the remaining pins; no extra power symbols.
for (r,n),(x,y,angle) in pins.items():
    if (r,n) in used:continue
    name=nets.get((r,n))
    if name is None or name.startswith('unconnected-'):
        s.append(['no_connect',['at',x,y],['uuid',uid()]]);continue
    length=5.08
    ex=round(x-math.cos(math.radians(angle))*length,4)
    ey=round(y+math.sin(math.radians(angle))*length,4)
    line((x,y),(ex,ey),name)
    label(name,(ex,ey),'right' if angle==0 else 'left')
# Functional groups and concise operational annotations.
block(20,38,112,154,'1  USB INPUT','J1: USB host / D1: ESD')
block(122,38,232,154,'2  USB-UART BRIDGE','FT232H: UART mode / 3.3 V local IO')
block(245,38,438,154,'3  UART LEVEL TRANSLATION','TXD / RTS_N: host -> target     RXD / CTS_N: target -> host')
block(450,38,573,154,'4  INDICATORS','Active-low TX/RX sinks from U1')
text(250,104,'1DIR=1; 2DIR=0.  Both OE# pins use PWREN_N.',1.05)
text(250,153,'C16/C17: U2 supplies.  R11/R12: weak input pull-ups.',1.05)
text(395,134,'J2: right-angle / J3: vertical',1.0)
text(125,144,'# = active low; unused pins retain no-connect flags.',1.0)
block(20,177,232,280,'5  CLOCK / RESET / FT232H SUPPLIES')
text(22,240,'U1 VCCIO / VREGIN / VCCD',1.0)
text(134,242,'Internal 1.8 V outputs',1.0)
block(245,177,360,280,'6  CONFIGURATION EEPROM','U5: 16-bit organization')
text(250,261,'EE_DATA -> DI; DO through R4, pulled high by R3.',1.0)
text(250,270,'EEPROM programming remains required.',1.0)
block(375,177,573,280,'7  ENUMERATION / SUSPEND CONTROL')
text(380,247,'PWREN_N low -> Q1 off -> PWR_EN high.',1.1)
text(380,256,'PWR_EN enables U4 and U6. PWREN_N enables U2.',1.1)
text(380,267,'These are existing connections; configuration is not changed.',1.0)
block(20,295,125,380,'8  FIXED 3.3 V','USB5V -> U3 -> bridge / EEPROM / U2 side A')
block(145,295,365,380,'9  SELECTABLE UART VOLTAGE','USB5V -> U4 -> VIO (U2 side B); FB feedback shown explicitly')
text(151,371,'SW1: 1=1.8 V / 2=2.5 V / 3=3.3 V',1.05)
text(151,380,'Change SW1 only with USB unplugged.',1.05)
block(385,295,573,380,'10  SWITCHED HEADER POWER')
text(385,376,'SW2: USB5V_OUT     SW3: VIO_OUT',1.05)
text(20,397,'LAYOUT REVIEW v1 - electrical connectivity and component identity preserved. PCB/manufacturing data unchanged.',1.15)
text(315,397,'USB SI / header land patterns / hardware tests remain open.',1.05)

# Split shared segments, remove duplicate strokes and mark every actual T branch.
# This changes only the drawing: every edge carries the original named net.
s[:]=[v for v in s if not isinstance(v,list) or v[0] not in ['wire','junction']]
from collections import defaultdict
net_points=defaultdict(set)
for a,b,n in segments:net_points[n].update([a,b])
pin_points=set()
for key,(x,y,angle) in pins.items():
    n=nets.get(key)
    if n and not n.startswith('unconnected-'):
        net_points[n].add((x,y));pin_points.add(((x,y),n))
edges=set()
for a,b,n in segments:
    dx=b[0]-a[0];dy=b[1]-a[1];length2=dx*dx+dy*dy
    on=[]
    for q in net_points[n]:
        cross=(q[0]-a[0])*dy-(q[1]-a[1])*dx
        dot=(q[0]-a[0])*dx+(q[1]-a[1])*dy
        if abs(cross)<1e-5 and -1e-5<=dot<=length2+1e-5:on.append((dot,q))
    on.sort()
    for (_,u),(_,v) in zip(on,on[1:]):
        if u!=v:edges.add((min(u,v),max(u,v),n))
adj=defaultdict(set)
for a,b,n in sorted(edges):
    s.append(['wire',['pts',['xy',*a],['xy',*b]],['stroke',['width',0.1524],['type','default']],['uuid',uid()]])
    adj[(a,n)].add(b);adj[(b,n)].add(a)
junc.clear()
for (a,n),neighbors in adj.items():
    if len(neighbors)>=3 or (len(neighbors)==2 and (a,n) in pin_points):junction(a)

(ROOT/'a2_usb_uart.kicad_sch').write_text(dump(s),encoding='utf-8')
(HERE/'layout_metrics.json').write_text(json.dumps({'output_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'symbols':len(symbols),'wired_pin_endpoints':len(used),'wires':len(children(s,'wire')),'labels':len(children(s,'label')),'before_labels':len(children(original,'label')),'junctions':len(junc),'library_symbols_unchanged':one(s,'lib_symbols')==one(original,'lib_symbols')},indent=2),encoding='utf-8')
print('Layout saved; no PCB, manufacturing, or original generator files written.')
