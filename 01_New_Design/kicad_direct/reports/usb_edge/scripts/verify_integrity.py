from common import *
from collections import defaultdict
old=k.LoadBoard(str(OUT/'before/a2_usb_uart.kicad_pcb'));of={f.GetReference():f for f in old.GetFootprints()}
assert set(of)==set(fps)
def models(f):return [(m.m_Filename,tuple(getattr(m,v).__getattribute__(x) for v in ['m_Offset','m_Rotation','m_Scale'] for x in ['x','y','z'])) for m in f.Models()]
def attrs(f):return [f.GetValue(),(f.GetFPID().GetLibNickname(),f.GetFPID().GetLibItemName()),f.GetAttributes(),sorted((x.GetName(),x.GetText()) for x in f.GetFields()),models(f)]
def pads(f):return sorted((p.GetNumber(),p.GetNetname(),xy(p.GetSize()),xy(p.GetDrillSize()),p.GetShape(),p.GetAttribute(),p.GetLayerSet().FmtHex()) for p in f.Pads())
assert all(attrs(of[r])==attrs(f) and pads(of[r])==pads(f) for r,f in fps.items())
placements=[{'ref':r,'before_mm':xy(of[r].GetPosition()),'after_mm':xy(f.GetPosition()),'angle_before':of[r].GetOrientationDegrees(),'angle_after':f.GetOrientationDegrees()} for r,f in fps.items() if xy(of[r].GetPosition())!=xy(f.GetPosition()) or of[r].GetOrientationDegrees()!=f.GetOrientationDegrees()]
before={uid(t):record(t) for t in old.GetTracks()};after={uid(t):record(t) for t in b.GetTracks()}
removed=[before[i] for i in before.keys()-after.keys()];added=[after[i] for i in after.keys()-before.keys()];edited=[{'before':before[i],'after':after[i]} for i in before.keys()&after.keys() if before[i]!=after[i]]
assert all(i in after and r==after[i] for i,r in before.items() if min(r['a'][1],r['b'][1])>=113)
def totals(board):
 d=defaultdict(float)
 for t in board.GetTracks():
  if not isinstance(t,k.PCB_VIA):d[t.GetNetname()]+=k.ToMM(t.GetLength())
 return dict(d)
bl,al=totals(old),totals(b);lengths=[{'net':n,'before_mm':round(bl.get(n,0),4),'after_mm':round(al.get(n,0),4),'delta_mm':round(al.get(n,0)-bl.get(n,0),4)} for n in sorted(set(bl)|set(al))]
(OUT/'copper_diff.json').write_text(json.dumps({'removed':removed,'added':added,'edited':edited},indent=2));(OUT/'net_lengths.json').write_text(json.dumps(lengths,indent=2))
for s in ['kicad_sch','kicad_pro','kicad_dru']:assert (ROOT/('a2_usb_uart.'+s)).read_bytes()==(OUT/'before'/('a2_usb_uart.'+s)).read_bytes()
f=fps['J1'];guide=[xy(g.GetStart())[1] for g in f.GraphicalItems() if isinstance(g,k.PCB_SHAPE) and g.GetLayer()==k.Dwgs_User];assert guide==[100.0]
# Same model offset and orientation: its measured local rear datum maps to board Y=99.8.
edge=100;model_rear=-5.425;rear=xy(f.GetPosition())[1]-model_rear
outline=lambda board:sorted((uid(g),g.GetLayer(),xy(g.GetStart()),xy(g.GetEnd())) for g in board.GetDrawings() if g.GetLayer()==k.Edge_Cuts)
assert outline(old)==outline(b)
zone=lambda board:sorted((uid(z),z.GetNetname(),z.GetLayerSet().FmtHex(),z.GetNumCorners(),tuple(xy(z.GetCornerPosition(i)) for i in range(z.GetNumCorners()))) for z in board.Zones())
assert zone(old)==zone(b)
usb=[r for r in lengths if r['net'] in ['/USB_D+','/USB_D-']]
result={'base_commit':'5cce544232e1f0eb137ef95f5060eeea5c9729ef','real_components':len(fps),'all_attributes_pads_nets_models_equal':True,'schematic_project_rules_byte_identical':True,'placements':placements,'all_original_copper_at_y_ge_113_unchanged':True,'edge_cuts_unchanged':True,'zones_outlines_nets_layers_unchanged':True,'zones_count':len(list(b.Zones())),'thickness_mm':k.ToMM(b.GetDesignSettings().GetBoardThickness()),'copper_layers':b.GetCopperLayerCount(),'copper_diff_counts':{'removed':len(removed),'added':len(added),'edited':len(edited)},'total_length_mm':[sum(bl.values()),sum(al.values())],'j1':{'origin_mm':xy(f.GetPosition()),'pcb_edge_guide_y_mm':guide,'locator_hole_row_y_mm':102.75,'locator_edge_distance_mm':2.75,'nominal_model_rear_y_mm':rear,'nominal_model_board_gap_mm':edge-rear,'model_not_altered':True},'usb_track_length_comparison':usb,'all_changed_usb5v_tracks_width_0_5mm':all(r['width']==.5 for r in added+[r['after'] for r in edited] if not r['via'] and r['net']=='USB5V')}
(OUT/'integrity.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))


