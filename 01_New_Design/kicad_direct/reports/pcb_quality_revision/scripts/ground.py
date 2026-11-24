from geom import *
import networkx as nx

def ground_parts():
 geoms={0:[],2:[]}
 for z in b.Zones():
  if z.GetNetname()!='GND' or z.GetIsRuleArea():continue
  layer=z.GetLayer();s=z.GetFilledPolysList(layer)
  for i in range(s.OutlineCount()):
   def ring(r):return [xy(r.CPoint(j)) for j in range(r.PointCount())]
   shell=ring(s.COutline(i));holes=[ring(s.CHole(i,j)) for j in range(s.HoleCount(i))]
   g=Polygon(shell,holes)
   if not g.is_valid:g=g.buffer(0)
   geoms[layer].append(g)
 for f in fps.values():
  for p in f.Pads():
   if p.GetNetname()=='GND':
    for z in [0,2]:
     if p.IsOnLayer(z):geoms[z].append(poly(p,z))
 for t in b.GetTracks():
  if t.GetNetname()!='GND':continue
  if isinstance(t,k.PCB_VIA):
   g=Point(xy(t.GetPosition())).buffer(.3)
   for z in [0,2]:geoms[z].append(g)
  else:geoms[t.GetLayer()].append(linegeom(t).buffer(k.ToMM(t.GetWidth())/2))
 parts=[]
 for z,gs in geoms.items():
  u=unary_union(gs).buffer(.0005)
  for g in ([u] if u.geom_type=='Polygon' else u.geoms):parts.append({'layer':z,'geom':g})
 G=nx.Graph();G.add_nodes_from(range(len(parts)))
 for t in list(b.GetTracks())+[p for f in fps.values() for p in f.Pads() if p.GetAttribute()==k.PAD_ATTRIB_PTH]:
  if t.GetNetname()!='GND' or not isinstance(t,(k.PCB_VIA,k.PAD)):continue
  q=Point(xy(t.GetPosition()));hits=[i for i,p in enumerate(parts) if p['geom'].distance(q)<.001]
  for a in hits:
   for c in hits:G.add_edge(a,c)
 comps=list(nx.connected_components(G));comps.sort(key=lambda c:-sum(parts[i]['geom'].area for i in c))
 return parts,comps

def stitch_ground():
 log=[]
 for iteration in range(10):
  k.ZONE_FILLER(b).Fill(b.Zones());parts,comps=ground_parts()
  print('native ground connectivity',count(),flush=True)
  print('ground components',len(comps),[round(sum(parts[i]['geom'].area for i in c),3) for c in comps],flush=True)
  if len(comps)<=1:return log
  # Native connectivity and the subsequent full CLI DRC remain mandatory gates.
  # Tiny filled-polygon fragments can be separate in this auxiliary geometry model.
  if count()==0:
   print('auxiliary polygon fragments retained for final DRC/visual inspection',flush=True);return log
  root=comps[0];target=comps[1];poss=[]
  # The source has a 12.5 um GND stub covered only by the old pour.
  # Remove only this documented isolated copper artifact, never a pad/via return.
  target_geom=unary_union([parts[i]['geom'] for i in target])
  stub=next((t for t in b.GetTracks() if uid(t)=='2983ba69-3445-4380-b8b7-bcf0cde261e5'),None)
  if stub is not None and target_geom.area<.03 and target_geom.intersects(linegeom(stub)):
   assert k.ToMM(stub.GetLength())<.03 and stub.GetNetname()=='GND'
   assert not any(target_geom.intersects(poly(p)) for f in fps.values() for p in f.Pads() if p.GetNetname()=='GND')
   log.append({'removed_isolated_source_stub':record(stub)});remove(stub);continue
  for i in target:
   g=parts[i]['geom'];opp=unary_union([parts[j]['geom'] for j in root if parts[j]['layer']!=parts[i]['layer']]);common=g.intersection(opp).buffer(-.12)
   if common.is_empty:continue
   x0,y0,x1,y1=common.bounds
   for ix in range(math.ceil(x0*10),math.floor(x1*10)+1):
    for iy in range(math.ceil(y0*10),math.floor(y1*10)+1):
     q=Point(ix/10,iy/10)
     if not common.contains(q):continue
     score=g.boundary.distance(q)+opp.boundary.distance(q);poss.append((-score,(ix/10,iy/10)))
  chosen=None
  for _,q in sorted(poss):
   pt=Point(q);bad=False
   if not(100.6<q[0]<121.4 and 100.6<q[1]<149.4):continue
   for f in fps.values():
    for p in f.Pads():
     if poly(p).distance(pt)<(.515 if p.GetNetname()=='GND' else .565 if p.GetAttribute()==k.PAD_ATTRIB_NPTH else .445):bad=True;break
    if bad:break
   if bad:continue
   for t in b.GetTracks():
    if isinstance(t,k.PCB_VIA):
     if math.dist(q,xy(t.GetPosition()))<(1.12 if t.GetNetname()=='GND' else .745):bad=True;break
    elif t.GetNetname()!='GND' and linegeom(t).distance(pt)<k.ToMM(t.GetWidth())/2+.445:bad=True;break
   if not bad:chosen=q;break
  if chosen is None:
   # Add an explicit GND return between existing stitching vias when no
   # vertical overlap supports a new stitch. Existing GND copper is retained.
   from local_router import route
   vv=[t for t in b.GetTracks() if isinstance(t,k.PCB_VIA) and t.GetNetname()=='GND']
   def membership(t,c):
    return any(parts[j]['geom'].distance(Point(xy(t.GetPosition())))<.001 for j in c)
   pairs=sorted((math.dist(xy(a.GetPosition()),xy(c.GetPosition())),xy(a.GetPosition()),xy(c.GetPosition())) for a in vv if membership(a,target) for c in vv if membership(c,root))
   rr=None
   for distance,qa,qc in pairs[:8]:
    if distance>10:continue
    for layer in [1,0]:
     rr=route(qa,qc,'GND',.25,(),[qa,qc],layer,layer)
     if rr:break
    if rr:break
   if not rr:
    sourcepads=[p for f in fps.values() for p in f.Pads() if p.GetNetname()=='GND' and any(parts[j]['layer']==0 and parts[j]['geom'].intersects(poly(p)) for j in target)]
    pairs2=sorted((math.dist(xy(p.GetPosition()),xy(t.GetPosition())),p.GetParentFootprint().GetReference()+'.'+p.GetNumber(),xy(p.GetPosition()),xy(t.GetPosition())) for p in sourcepads for t in vv if membership(t,root))
    for distance,pin,qa,qc in pairs2[:8]:
     if distance>10:continue
     rr=route(qa,qc,'GND',.25,[pin],[qa,qc],0,0)
     if rr:break
   if rr:
    log.append({'added_ground_return':[record(t) for t in rr]});continue
   details=[{'layer':parts[i]['layer'],'area':parts[i]['geom'].area,'bounds':parts[i]['geom'].bounds} for i in target]
   drc('ground_diagnostic')
   raise RuntimeError('no safe stitching point for '+str(details))
  vnew=via(chosen,'GND');log.append(record(vnew));print('GND stitch',chosen,flush=True)
 raise RuntimeError('ground stitching did not converge')

if __name__=='__main__':
 parts,comps=ground_parts()
 for c in comps:print([{'layer':parts[i]['layer'],'area':round(parts[i]['geom'].area,3),'bounds':parts[i]['geom'].bounds} for i in c])
