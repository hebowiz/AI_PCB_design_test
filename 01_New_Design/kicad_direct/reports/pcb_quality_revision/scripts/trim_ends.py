from geom import *
prev=sys.argv[1] if len(sys.argv)>1 else 'redundancy';r=json.loads((OUT/'checks'/('drc_'+prev+'.json')).read_text());idx={uid(t):t for t in b.GetTracks()};log=[]
for e in r['violations']:
 if e['type'] not in ['via_dangling','track_dangling']:continue
 t=idx[e['items'][0]['uuid']];net=t.GetNetname()
 if net in ['GND','/USB_D+','/USB_D-','/XTAL_IN','/XTAL_OUT']:continue
 rec=record(t)
 if isinstance(t,k.PCB_VIA):
  remove(t)
  if count()!=0:b.Add(t);count();continue
  rec['action']='remove unused via';log.append(rec);continue
 remove(t)
 if count()==0:rec['action']='remove proven redundant residual tail';log.append(rec);continue
 b.Add(t);count()
 line=linegeom(t);dist=[];z=t.GetLayer();w=k.ToMM(t.GetWidth())
 for f in fps.values():
  for p in f.Pads():
   if p.GetNetname()!=net or not p.IsOnLayer(z):continue
   g=poly(p,z)
   if g.distance(line)>w/2+.00001:continue
   dist.append(line.project(Point(xy(p.GetPosition()))))
 for u in b.GetTracks():
  if uid(u)==uid(t) or u.GetNetname()!=net:continue
  if isinstance(u,k.PCB_VIA):
   q=Point(xy(u.GetPosition()))
   if line.distance(q)<=k.ToMM(u.GetWidth(k.F_Cu))/2+w/2:dist.append(line.project(q))
  elif u.GetLayer()==z:
   g=linegeom(u);q=line.intersection(g)
   if not q.is_empty:dist.extend(line.project(Point(a)) for a in points(q))
   elif line.distance(g)<=(w+k.ToMM(u.GetWidth()))/2:dist.append(line.project(nearest_points(line,g)[0]))
 if len(dist)<2:continue
 a,c=line.interpolate(min(dist)).coords[0],line.interpolate(max(dist)).coords[0]
 if math.dist(a,c)<.001:continue
 t.SetStart(v(*a));t.SetEnd(v(*c))
 if count()!=0:t.SetStart(v(*rec['a']));t.SetEnd(v(*rec['b']));count();continue
 rec.update(action='trim excess ends to required contacts',after=record(t));log.append(rec)
(OUT/('trim_'+prev+'.json')).write_text(json.dumps(log,indent=2),encoding='utf-8');drc('trim_'+prev)
