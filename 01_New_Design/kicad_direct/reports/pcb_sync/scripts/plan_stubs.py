"""Read-only plan for obsolete copper stubs: preserve all pad-anchored paths.
The resulting UUID list is inspected before applying any deletion.
"""
from pathlib import Path
from collections import defaultdict,deque
import json,math,hashlib,pcbnew as p
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'reports/pcb_sync';path=ROOT/'a2_usb_uart.kicad_pcb';b=p.LoadBoard(str(path))
def xy(v):return (round(p.ToMM(v.x),6),round(p.ToMM(v.y),6))
tracks=list(b.GetTracks());pads=[a for f in b.GetFootprints() for a in f.Pads()];plan=[]
for net in sorted(set(t.GetNetCode() for t in tracks)):
 ts=[t for t in tracks if t.GetNetCode()==net];name=ts[0].GetNetname()
 if name=='GND':continue
 nodes={};edges=[];adj=defaultdict(set);anchors=set()
 def node(x,y,z):
  key=(round(x,5),round(y,5),z)
  if key not in nodes:nodes[key]=len(nodes)
  return nodes[key]
 for t in ts:
  a=xy(t.GetStart());c=xy(t.GetEnd())
  z=0 if t.IsOnLayer(p.F_Cu) else 1
  u=node(*a,z);v=node(*a,1) if isinstance(t,p.PCB_VIA) else node(*c,z)
  edges.append([u,v,t]);e=len(edges)-1;adj[u].add(e);adj[v].add(e)
 inv={n:k for k,n in nodes.items()}
 for n,(x,y,z) in inv.items():
  for pad in pads:
   if pad.GetNetCode()==net and pad.IsOnLayer(p.F_Cu if z==0 else p.B_Cu) and pad.HitTest(p.VECTOR2I(p.FromMM(x),p.FromMM(y))):anchors.add(n);break
 # Protect junctions along segment interiors even when no common endpoint is stored.
 for n,(x,y,z) in inv.items():
  for u,v,t in edges:
   if n in [u,v] or isinstance(t,p.PCB_VIA) or z!=(0 if t.IsOnLayer(p.F_Cu) else 1):continue
   a=xy(t.GetStart());c=xy(t.GetEnd());dx=c[0]-a[0];dy=c[1]-a[1];ll=dx*dx+dy*dy
   if ll<1e-12:continue
   k=((x-a[0])*dx+(y-a[1])*dy)/ll
   if 0<k<1 and math.hypot(x-a[0]-k*dx,y-a[1]-k*dy)<p.ToMM(t.GetWidth())/2+.0001:anchors.add(n)
 removed=set();queue=deque(n for n in nodes.values() if len(adj[n])<=1 and n not in anchors)
 while queue:
  n=queue.popleft()
  if n in anchors or len(adj[n])!=1:continue
  e=next(iter(adj[n]));u,v,t=edges[e];removed.add(e)
  for q in {u,v}:
   adj[q].discard(e)
   if q not in anchors and len(adj[q])<=1:queue.append(q)
 # Also inspect wholly isolated same-net components with no pad anchors.
 seen=set()
 for n in nodes.values():
  if n in seen:continue
  stack=[n];part=set();es=set()
  while stack:
   q=stack.pop()
   if q in part:continue
   part.add(q);seen.add(q)
   for e in adj[q]:
    es.add(e);u,v,t=edges[e];stack.extend([u,v])
  if not (part & anchors):removed.update(es)
 for e in sorted(removed):
  t=edges[e][2];plan.append({'uuid':t.m_Uuid.AsString(),'net':name,'start':xy(t.GetStart()),'end':xy(t.GetEnd()),'via':isinstance(t,p.PCB_VIA),'length':0 if isinstance(t,p.PCB_VIA) else p.ToMM(t.GetLength())})
result={'board_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'proposed':plan}
(OUT/'stub_cleanup_plan.json').write_text(json.dumps(result,indent=2),encoding='utf8')
for x in plan:print(x)
print('PROPOSED',len(plan),'total length',sum(x['length'] for x in plan))
