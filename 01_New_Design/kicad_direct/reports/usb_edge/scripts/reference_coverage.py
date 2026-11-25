from geom import *
def ground_back(board):
 gs=[]
 for z in board.Zones():
  if z.GetIsRuleArea() or z.GetLayer()!=k.B_Cu or z.GetNetname()!='GND':continue
  s=z.GetFilledPolysList(k.B_Cu)
  def ring(r):return [xy(r.CPoint(j)) for j in range(r.PointCount())]
  for i in range(s.OutlineCount()):
   g=Polygon(ring(s.COutline(i)),[ring(s.CHole(i,j)) for j in range(s.HoleCount(i))]);gs.append(g if g.is_valid else g.buffer(0))
 for f in board.GetFootprints():
  for p in f.Pads():
   if p.GetNetname()=='GND' and p.IsOnLayer(k.B_Cu):gs.append(poly(p,k.B_Cu))
 for t in board.GetTracks():
  if t.GetNetname()!='GND':continue
  if isinstance(t,k.PCB_VIA):gs.append(Point(xy(t.GetPosition())).buffer(k.ToMM(t.GetWidth(k.B_Cu))/2))
  elif t.GetLayer()==k.B_Cu:gs.append(linegeom(t).buffer(k.ToMM(t.GetWidth())/2))
 return unary_union(gs)
old=k.LoadBoard(str(OUT/'before/a2_usb_uart.kicad_pcb'));g0=ground_back(old);g1=ground_back(b);rows=[]
for net in ['/USB_D+','/USB_D-','/XTAL_IN','/XTAL_OUT']:
 region=unary_union([linegeom(t).buffer(k.ToMM(t.GetWidth())/2) for t in b.GetTracks() if not isinstance(t,k.PCB_VIA) and t.GetLayer()==k.F_Cu and t.GetNetname()==net])
 lost=region.intersection(g0).difference(g1.buffer(.002))
 rows.append({'net':net,'front_copper_area_mm2':region.area,'before_unreferenced_area_mm2':region.difference(g0).area,'after_unreferenced_area_mm2':region.difference(g1).area,'new_loss_over_2um_tolerance_mm2':lost.area,'new_loss_bounds':lost.bounds if not lost.is_empty else []})
(OUT/'ground_reference_comparison.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2));assert all(r['new_loss_over_2um_tolerance_mm2']<.001 for r in rows)
