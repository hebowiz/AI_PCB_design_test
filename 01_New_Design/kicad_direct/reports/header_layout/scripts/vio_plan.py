from geom import *
import networkx as nx
items=[t for t in b.GetTracks() if t.GetNetname()=='VIO'];G=nx.Graph();gs={uid(t):(Point(xy(t.GetPosition())).buffer(.3) if isinstance(t,k.PCB_VIA) else linegeom(t).buffer(k.ToMM(t.GetWidth())/2)) for t in items}
for i,t in enumerate(items):
 G.add_node(uid(t))
 for o in items[i+1:]:
  if not isinstance(t,k.PCB_VIA) and not isinstance(o,k.PCB_VIA) and t.GetLayer()!=o.GetLayer():continue
  if gs[uid(t)].distance(gs[uid(o)])<.0001:G.add_edge(uid(t),uid(o),weight=.01+(0 if isinstance(o,k.PCB_VIA) else k.ToMM(o.GetLength()))/2+(0 if isinstance(t,k.PCB_VIA) else k.ToMM(t.GetLength()))/2)
p=nx.shortest_path(G,'5fc1d11e-5cf7-4548-b552-1342805a7ed7','9dda71b5-9adf-4b7a-a93d-080cde373791',weight='weight');rows=[record(t) for id in p[1:-1] for t in items if uid(t)==id];(OUT/'vio_shortcut_plan.json').write_text(json.dumps(rows,indent=2));print('selected',len(rows),'length',sum(math.dist(r['a'],r['b']) for r in rows));print(rows)
