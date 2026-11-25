from common import *
from geom import poly
from shapely.geometry import box
from shapely.ops import unary_union
# Explicit local placement plan. No broad automatic regeneration.
plan={'J2':(111,143.1928,0),'J3':(111,137.9,0),'U4':(104.6,129.3,0),'C18':(101.7,129.4,270),'C19':(108.0,133.0,0),'R7':(111,132.4,180),'R8':(111,133.85,0),'R10':(113.4,133.5,0)}
oldpins={r:{p.GetNumber():xy(p.GetPosition()) for p in fps[r].Pads()} for r in plan}
oldplacements={r:{'pos':xy(fps[r].GetPosition()),'rot':fps[r].GetOrientationDegrees()} for r in plan}
for r,(x,y,a) in plan.items():
 f=fps[r];f.SetOrientationDegrees(a);f.SetPosition(v(x,y))
# J2 keeps existing footprint identifier; J3 uses a new project-local footprint.
f=fps['J2']
for p in f.Pads():p.SetSize(v(1.27,3.175))
f.SetLibDescription('Samtec TSM-104-01-T-SH: recommended footprint revision B, no LC/A options')
for m in f.Models():m.m_Offset.y=-.7172
f=fps['J3'];f.SetFPID(k.LIB_ID('A2','TSM_104_SV'))
for p in f.Pads():
 n=int(p.GetNumber());p.SetOrientationDegrees(0);p.SetSize(v(1.27,3.429));p.SetShape(k.PAD_SHAPE_RECT)
 p.SetPosition(v(111+(n-2.5)*2.54,137.9+(-1 if n%2 else 1)*1.4605))
f.SetLibDescription('Samtec TSM-104-01-T-SV: footprint D, no LC/A options; pin 1 left, tail towards board interior')
f.Models().clear()
m=k.FP_3DMODEL();m.m_Filename='${KIPRJMOD}/models/TSM_104_01_T_SV_simplified.wrl';f.Add3DModel(m);KEEP.append(m)
# New graphic outlines and physical courtyard follow body and pad envelope.
for ref in ['J2','J3']:
 f=fps[ref]
 for g in list(f.GraphicalItems()):KEEP.append(g);f.Remove(g)
 def outline(coords,layer,width):
  for a,c in zip(coords,coords[1:]+coords[:1]):
   g=k.PCB_SHAPE(f);g.SetShape(k.SHAPE_T_SEGMENT);g.SetLayer(layer);g.SetWidth(k.FromMM(width));g.SetStart(v(*a));g.SetEnd(v(*c));f.Add(g);KEEP.append(g)
 if ref=='J2':
  bd=(105.92,147.46,116.08,150.0)
  cy=box(105.67,141.3553,116.33,156.092)
 else:
  bd=(105.92,136.63,116.08,139.17)
  cy=unary_union([box(bd[0]-.25,bd[1]-.25,bd[2]+.25,bd[3]+.25)]+[poly(p).buffer(.25,join_style=2) for p in f.Pads()])
 outline([(bd[0],bd[1]),(bd[2],bd[1]),(bd[2],bd[3]),(bd[0],bd[3])],k.F_Fab,.1)
 outline(list(cy.exterior.coords)[:-1],k.F_CrtYd,.05)
 f.Reference().SetPosition(v(111,146.0 if ref=='J2' else 137.9));f.Reference().SetTextAngle(k.EDA_ANGLE(0,k.DEGREES_T));f.Reference().SetTextSize(v(.7,.7))
 f.Value().SetVisible(False)
 # Project-local source footprint is exported with same geometry.
 # Library export is performed in a separate process after PCB save.
# Preserve the electrical meaning: only J3 footprint association changes in schematic.
sch=ROOT/'a2_usb_uart.kicad_sch';s=sch.read_text()
old='A2:PinHeader_1x04_P2.54mm_Vertical_SMD_Pin1Left'
assert s.count(old)==1
(OUT/'candidate/a2_usb_uart.kicad_sch').write_text(s.replace(old,'A2:TSM_104_SV'))
# Select only copper attached to moved pads and affected routing in the local region.
# First report exact planned removals; routing is rebuilt explicitly in later scripts.
sel=[]
for t in b.GetTracks():
 a,c=xy(t.GetStart()),xy(t.GetEnd());net=t.GetNetname()
 # Only bottom connector/power region. Upstream signal routes stay fixed.
 local=min(a[1],c[1])>=132.0
 affected=net in ['GND','USB5V','VIO','VIO_OUT','/FB','/VSEL_3V3','/VSEL_2V5','/TXD','/RXD','/RTS_N','/CTS_N','USB5V_OUT','/USB5V_SW']
 if local and affected:sel.append(t)
# This intermediate candidate deliberately keeps copper until scoped removal is reviewed in code.
(OUT/'placement_plan.json').write_text(json.dumps({'before':oldplacements,'after':plan,'pad_before':oldpins,'pad_after':{r:{p.GetNumber():xy(p.GetPosition()) for p in fps[r].Pads()} for r in plan},'copper_candidates':[record(t) for t in sel]},indent=2))
save(False)
print('Prepared placement and footprint candidate; copper unchanged',len(sel))
