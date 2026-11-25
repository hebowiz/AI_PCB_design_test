from ground import *
log=[]
for iteration in range(12):
 k.ZONE_FILLER(b).Fill(b.Zones());parts,comps=ground_parts();print('GND',count(),[round(sum(parts[i]['geom'].area for i in c),2) for c in comps],flush=True)
 if count()==0:break
 poss=[]
 for ci,target in enumerate(comps):
  for i in target:
   g=parts[i]['geom'];opp=unary_union([parts[j]['geom'] for cj,c in enumerate(comps) if cj!=ci for j in c if parts[j]['layer']!=parts[i]['layer']]);common=g.buffer(.23).intersection(opp.buffer(.23))
   if common.is_empty:continue
   x0,y0,x1,y1=common.bounds
   for ix in range(math.ceil(x0*20),math.floor(x1*20)+1):
    for iy in range(math.ceil(y0*20),math.floor(y1*20)+1):
     q=(ix/20,iy/20);pt=Point(q)
     if common.contains(pt):poss.append((-min(g.boundary.distance(pt),opp.boundary.distance(pt)),q))
 chosen=None
 for _,q in sorted(poss):
  pt=Point(q)
  if not(100.6<q[0]<121.4 and 124.5<q[1]<149.4):continue
  if any(poly(p).distance(pt)<(.505 if p.GetNetname()=='GND' else .565 if p.GetAttribute()==k.PAD_ATTRIB_NPTH else .435) for f in fps.values() for p in f.Pads()):continue
  if any((math.dist(q,xy(t.GetPosition()))<(1.105 if t.GetNetname()=='GND' else .735)) if isinstance(t,k.PCB_VIA) else (t.GetNetname()!='GND' and linegeom(t).distance(pt)<k.ToMM(t.GetWidth())/2+.435) for t in b.GetTracks()):continue
  chosen=q;break
 if chosen is None:print('no stitch',len(poss));break
 log.append(record(via(chosen,'GND')));print('via',chosen,flush=True)
(OUT/'ground_stitches.json').write_text(json.dumps(log,indent=2));drc('stitches')
