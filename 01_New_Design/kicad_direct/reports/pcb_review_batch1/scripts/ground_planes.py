from local_tools import *
net=b.FindNet('GND').GetNetCode();logs=[]
# Stitch each isolated copper polygon where a compliant through via fits.
for run in range(2):
 save(True);zones=[z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname()=='GND'];poly={z.GetLayer():z.GetFilledPolysList(z.GetLayer()) for z in zones};mask,vm=masks(net)
 for z in zones:
  shape=poly[z.GetLayer()];other=poly[p.B_Cu if z.GetLayer()==p.F_Cu else p.F_Cu]
  for i in range(shape.OutlineCount()):
   contour=shape.COutline(i);bb=contour.BBox();area=abs(contour.Area())/1e12
   if area<.15:continue
   vs=[t for t in b.GetTracks() if isinstance(t,p.PCB_VIA) and t.GetNetCode()==net]
   if any(shape.Contains(t.GetPosition(),i) for t in vs):continue
   xmin,ymin=xy(bb.GetOrigin());xmax,ymax=xy(bb.GetEnd());cx,cy=(xmin+xmax)/2,(ymin+ymax)/2;candidates=[]
   for x in np.arange(max(100.65,xmin),min(121.35,xmax)+.001,.15):
    for y in np.arange(max(100.65,ymin),min(149.35,ymax)+.001,.15):
     pt=v(float(x),float(y));node=r.node(float(x)-100,float(y)-100)
     if vm[node%r.PLANE] or not shape.Contains(pt,i) or not other.Contains(pt):continue
     if any(math.dist(xy(t.GetPosition()),(x,y))<1.11 for t in vs):continue
     candidates.append((math.hypot(x-cx,y-cy),float(x),float(y)))
   if not candidates:continue
   _,x,y=min(candidates);via(x,y,'GND');logs.append({'run':run,'layer':z.GetLayerName(),'polygon':i,'area_mm2':area,'via':[x,y]});refresh();mask,vm=masks(net)
(OUT/'ground_plane_stitching.json').write_text(json.dumps(logs,indent=2));print('added',len(logs));drc('ground_planes')
