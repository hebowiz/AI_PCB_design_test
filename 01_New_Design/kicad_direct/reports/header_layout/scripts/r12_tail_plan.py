from geom import *
import networkx as nx
G=nx.Graph(); key=lambda q,z:(round(q[0],4),round(q[1],4),z)
for t in b.GetTracks():
 if t.GetNetname() not in ['VIO','/CTS_N']:continue
 if isinstance(t,k.PCB_VIA):a=key(xy(t.GetPosition()),0);c=key(xy(t.GetPosition()),2)
 else:a=key(xy(t.GetStart()),t.GetLayer());c=key(xy(t.GetEnd()),t.GetLayer())
 G.add_edge((t.GetNetname(),a),(t.GetNetname(),c),obj=t)
ids=[]
for n,end,z in [('1',(115.5,132.01),0),('2',(114.25,131.95),2)]:
 p=pad('R12',n);path=nx.shortest_path(G,(p.GetNetname(),key(xy(p.GetPosition()),0)),(p.GetNetname(),key(end,z)))
 rows=[record(G[a][c]['obj']) for a,c in zip(path,path[1:])];ids+=rows;print(n,len(rows))
(OUT/'r12_tail_replacement.json').write_text(json.dumps(ids,indent=2))
print([r['uuid'] for r in ids])
