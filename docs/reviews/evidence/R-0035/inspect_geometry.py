"""Read-only R-0035 geometry study; no board save or placement mutation."""
import sys,os,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(os.environ['TEMP'])/'a2-pcb-quality-packages'))
import pcbnew as k
from shapely.geometry import LineString,box,Point
from shapely.ops import polygonize,unary_union
from shapely.affinity import translate,rotate
w=Path(r'D:/Documents/KiCad/10.0/projects/99_AI_PCB_design_test/workspaces/A-2/01_New_Design/kicad_direct')
path=w/'a2_usb_uart.kicad_pcb'
before=hashlib.sha256(path.read_bytes()).hexdigest()
b=k.LoadBoard(str(path));f=next(f for f in b.GetFootprints() if f.GetReference()=='J1')
def xy(p):return (k.ToMM(p.x),k.ToMM(p.y))
def court(f):
 gs=[g for g in f.GraphicalItems() if isinstance(g,k.PCB_SHAPE) and g.GetLayer()==k.F_CrtYd]
 lines=[LineString([xy(g.GetStart()),xy(g.GetEnd())]) for g in gs if g.GetShape()==k.SHAPE_T_SEGMENT]
 rects=[box(min(xy(g.GetStart())[0],xy(g.GetEnd())[0]),min(xy(g.GetStart())[1],xy(g.GetEnd())[1]),max(xy(g.GetStart())[0],xy(g.GetEnd())[0]),max(xy(g.GetStart())[1],xy(g.GetEnd())[1])) for g in gs if g.GetShape()==k.SHAPE_T_RECT]
 circles=[Point(xy(g.GetCenter())).buffer(k.ToMM(g.GetRadius()),resolution=64) for g in gs if g.GetShape()==k.SHAPE_T_CIRCLE]
 result=unary_union(list(polygonize(lines))+rects+circles)
 assert not gs or not result.is_empty,f.GetReference()
 return result
def padshape(p):
 x,y=xy(p.GetPosition());sx,sy=xy(p.GetSize())
 return translate(rotate(box(-sx/2,-sy/2,sx/2,sy/2),-p.GetOrientationDegrees(),origin=(0,0)),xoff=x,yoff=y)
# Rectangular envelopes deliberately conservative for rounded pads.
delta=.6
targetcourt=translate(court(f),yoff=delta)
overlap=[]
for q in b.GetFootprints():
 if q==f:continue
 c=court(q)
 area=targetcourt.intersection(c).area
 if area>1e-7:overlap.append({'ref':q.GetReference(),'overlap_area_mm2':area,'original_overlap_mm2':court(f).intersection(c).area})
pads=[]
for p in f.Pads():
 d={'number':p.GetNumber(),'position_mm':xy(p.GetPosition()),'net':p.GetNetname(),'size_mm':xy(p.GetSize()),'drill_mm':xy(p.GetDrillSize())}
 if p.GetNumber() in ['1','2','3','4']:
  new=translate(padshape(p),yoff=delta)
  nearest=[]
  for q in b.GetFootprints():
   if q==f:continue
   for qp in q.Pads():
    if qp.IsOnLayer(k.F_Cu):nearest.append((new.distance(padshape(qp)),q.GetReference(),qp.GetNumber()))
  d['nearest_other_pad_after_translation_rect_envelope']=sorted(nearest)[:3]
 pads.append(d)
guide=[xy(g.GetStart())[1] for g in f.GraphicalItems() if isinstance(g,k.PCB_SHAPE) and g.GetLayer()==k.Dwgs_User]
assert before==hashlib.sha256(path.read_bytes()).hexdigest()
data={'design_commit':'5cce544232e1f0eb137ef95f5060eeea5c9729ef','pcb_sha256':before,'j1_origin_mm':xy(f.GetPosition()),'j1_rotation_deg':f.GetOrientationDegrees(),'board_edge_y_mm':100,'footprint_pcb_edge_guide_y_mm':guide,'current_locator_to_edge_mm':2.15,'recommended_locator_to_edge_mm':2.75,'proposed_translation_mm':[0,delta],'proposed_origin_mm':[111,94.375],'pads':pads,'proposed_courtyard_overlaps':overlap,'cad_modified':False}
out=Path(__file__).resolve().parent/'geometry.json'
out.write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps({'courtyard_overlaps':overlap},indent=2))
