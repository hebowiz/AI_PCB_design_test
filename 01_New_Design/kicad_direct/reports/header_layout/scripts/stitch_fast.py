from ground import *
log=[]
for it in range(8):
 k.ZONE_FILLER(b).Fill(b.Zones());parts,comps=ground_parts();print('GND',count(),[round(sum(parts[i]['geom'].area for i in c),2) for c in comps],flush=True)
 if count()==0:break
 obstacles=[poly(p).buffer(.505 if p.GetNetname()=='GND' else .565 if p.GetAttribute()==k.PAD_ATTRIB_NPTH else .435) for f in fps.values() for p in f.Pads()]
 for t in b.GetTracks():
  if isinstance(t,k.PCB_VIA):obstacles.append(Point(xy(t.GetPosition())).buffer(1.105 if t.GetNetname()=='GND' else .735))
  elif t.GetNetname()!='GND':obstacles.append(linegeom(t).buffer(k.ToMM(t.GetWidth())/2+.435))
 block=unary_union(obstacles);poss=[]
 from shapely.geometry import box
 for ci,target in enumerate(comps):
  for i in target:
   g=parts[i]['geom'];opp=unary_union([parts[j]['geom'] for cj,c in enumerate(comps) if cj!=ci for j in c if parts[j]['layer']!=parts[i]['layer']]);common=g.buffer(.23).intersection(opp.buffer(.23)).intersection(box(100.6,124.5,121.4,149.4)).difference(block)
   if common.is_empty:continue
   x0,y0,x1,y1=common.bounds
   for ix in range(math.ceil(x0*20),math.floor(x1*20)+1):
    for iy in range(math.ceil(y0*20),math.floor(y1*20)+1):
     q=(ix/20,iy/20);pt=Point(q)
     if common.contains(pt):poss.append((g.distance(pt)+opp.distance(pt),q))
 if not poss:print('no stitch');break
 q=min(poss)[1];log.append(record(via(q,'GND')));print('via',q,flush=True)
(OUT/'ground_stitches_final.json').write_text(json.dumps(log,indent=2));drc('stitch_fast')
