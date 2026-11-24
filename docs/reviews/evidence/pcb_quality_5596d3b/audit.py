"""Read-only PCB quality audit. Candidates, not automatic deletion or approval rules.
Run using KiCad 10 Python; install shapely/networkx into TEMP/a2-pcb-quality-packages.
Default board is the separate reviewed worktree. No board/project is saved.
"""
from pathlib import Path
import os,sys,json,math,hashlib,subprocess,itertools,csv
sys.path.insert(0,str(Path(os.environ['TEMP'])/'a2-pcb-quality-packages'))
import pcbnew as k
import networkx as nx
from shapely.geometry import Point,LineString,Polygon,box
from shapely.ops import unary_union,nearest_points
from shapely import affinity
OUT=Path(__file__).resolve().parent
BOARD=Path(sys.argv[1]) if len(sys.argv)>1 else Path('C:/Users/hebow/.codex/worktrees/a2-pcb-review/99_AI_PCB_design_test/01_New_Design/kicad_direct/a2_usb_uart.kicad_pcb')
BASE='5596d3bc8802687b89b21fd9c57e1117ec9382e5';START=hashlib.sha256(BOARD.read_bytes()).hexdigest()
assert subprocess.check_output(['git','hash-object',str(BOARD)],cwd=BOARD.parent,text=True).strip()==subprocess.check_output(['git','rev-parse',BASE+':01_New_Design/kicad_direct/a2_usb_uart.kicad_pcb'],cwd=BOARD.parent,text=True).strip()
b=k.LoadBoard(str(BOARD));KEEP=list(b.GetTracks());fps=list(b.GetFootprints());EPS=1e-5;CLEAR=.127
xy=lambda q:(round(k.ToMM(q.x),6),round(k.ToMM(q.y),6))
uid=lambda q:q.m_Uuid.AsString()
def write(n,obj): (OUT/n).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def polyconvert(poly):
 parts=[]
 for i in range(poly.OutlineCount()):
  ring=poly.COutline(i);pts=[xy(ring.CPoint(j)) for j in range(ring.PointCount())]
  if len(pts)>=3:parts.append(Polygon(pts))
 return unary_union(parts)
tracks=[];vias=[];pads=[]
for t in KEEP:
 rec={'uuid':uid(t),'net':t.GetNetname(),'a':xy(t.GetStart()),'b':xy(t.GetEnd()),'layer':t.GetLayer(),'width':k.ToMM(t.GetWidth(k.F_Cu) if isinstance(t,k.PCB_VIA) else t.GetWidth())}
 if isinstance(t,k.PCB_VIA):rec['hole']=k.ToMM(t.GetDrillValue());vias.append(rec)
 else:rec['length']=k.ToMM(t.GetLength());tracks.append(rec)
for f in fps:
 for p in f.Pads():
  if not p.GetNetCode():continue
  layers=[z for z in [k.F_Cu,k.B_Cu] if p.IsOnLayer(z)]
  poly=k.SHAPE_POLY_SET();p.TransformShapeToPolygon(poly,layers[0],0,k.FromMM(.001),k.ERROR_OUTSIDE)
  geom=polyconvert(poly)
  pads.append({'uuid':uid(p),'pin':f.GetReference()+'.'+p.GetNumber(),'ref':f.GetReference(),'net':p.GetNetname(),'at':xy(p.GetPosition()),'size':xy(p.GetSize()),'angle':p.GetOrientationDegrees(),'layers':layers,'poly':list(geom.exterior.coords) if geom.geom_type=='Polygon' else [],'geom':geom})
T={t['uuid']:t for t in tracks};P={p['uuid']:p for p in pads}
for t in tracks:t['geom']=LineString([t['a'],t['b']]);t['copper']=t['geom'].buffer(t['width']/2,quad_segs=16)
serial=lambda r:{kk:vv for kk,vv in r.items() if kk not in ['geom','copper']}
write('geometry.json',{'tracks':[serial(t) for t in tracks],'vias':vias,'pads':[serial(p) for p in pads]})
# Actual noding: center-line intersections, projected finite-width contacts, pads and vias.
netrows=[];turns=[];cycles=[];stubs=[];detours=[];duplicates=[];networks={};graphs={};splitgraphs={}
for net in sorted({t['net'] for t in tracks}|{p['net'] for p in pads}):
 ts=[t for t in tracks if t['net']==net];ps=[p for p in pads if p['net']==net];vs=[v for v in vias if v['net']==net]
 if not ts:continue
 cuts={t['uuid']:{0.0,t['geom'].length} for t in ts};connect=[]
 def cut(t,pt):
  d=t['geom'].project(Point(pt));cuts[t['uuid']].add(round(d,9));return (t['layer'],*tuple(round(q,5) for q in t['geom'].interpolate(d).coords[0]))
 def points(g):
  if g.is_empty:return []
  if g.geom_type=='Point':return [g.coords[0]]
  if g.geom_type in ['LineString','LinearRing']:return [g.coords[0],g.coords[-1]]
  return [p for child in g.geoms for p in points(child)]
 for a,c in itertools.combinations(ts,2):
  if a['layer']!=c['layer']:continue
  inter=a['geom'].intersection(c['geom'])
  if not inter.is_empty:
   for q in points(inter):connect.append((cut(a,q),cut(c,q)))
   if inter.length>EPS:duplicates.append({'net':net,'uuids':[a['uuid'],c['uuid']],'overlap_mm':round(inter.length,6),'layer':a['layer'],'bounds':inter.bounds})
  elif a['geom'].distance(c['geom'])<=(a['width']+c['width'])/2+EPS:
   q,r=nearest_points(a['geom'],c['geom']);connect.append((cut(a,q.coords[0]),cut(c,r.coords[0])))
 for p in ps:
  for t in ts:
   if t['layer'] not in p['layers']:continue
   if t['copper'].distance(p['geom'])>EPS:continue
   inter=t['geom'].intersection(p['geom']);qpts=points(inter)
   if not qpts:qpts=[nearest_points(t['geom'],p['geom'])[0].coords[0]]
   for q in qpts:connect.append((('pad',p['uuid']),cut(t,q)))
 for v in vs:
  for t in ts:
   if t['geom'].distance(Point(v['a']))<=(v['width']+t['width'])/2+EPS:
    q=nearest_points(t['geom'],Point(v['a']))[0];connect.append((('via',v['uuid']),cut(t,q.coords[0])))
 G0=nx.Graph();pos={};term={};vianodes=set()
 for t in ts:
  pts=[(t['layer'],*tuple(round(q,5) for q in t['geom'].interpolate(d).coords[0])) for d in sorted(cuts[t['uuid']])]
  for n in pts:pos[n]=n[1:]
  for a,c in zip(pts,pts[1:]):
   if a==c:continue
   dist=math.dist(a[1:],c[1:]);prev=G0.get_edge_data(a,c)
   if prev:prev['uuids'].add(t['uuid'])
   else:G0.add_edge(a,c,length=dist,uuids={t['uuid']},layer=t['layer'])
 class StableUF:
  def __init__(self,seq):self.parent={q:q for q in seq}
  def __getitem__(self,q):
   self.parent.setdefault(q,q)
   if self.parent[q]!=q:self.parent[q]=self[self.parent[q]]
   return self.parent[q]
  def union(self,a,c):
   x,y=self[a],self[c]
   if x!=y:self.parent[max([x,y],key=repr)]=min([x,y],key=repr)
 uf=StableUF(list(G0.nodes)+[n for edge in connect for n in edge])
 for a,c in connect:uf.union(a,c)
 for p in ps:
  n=('pad',p['uuid']);pos[n]=p['at'];term[n]=p['pin']
 for v in vs:pos[('via',v['uuid'])]=v['a'];vianodes.add(('via',v['uuid']))
 groups={}
 for n in list(G0.nodes)+list(term)+list(vianodes):groups.setdefault(uf[n],set()).add(n)
 def nodepos(n):
  g=sorted(groups[n],key=repr);preferred=next((q for q in g if q in term),None) or next((q for q in g if q in vianodes),None) or next(iter(g));return pos[preferred]
 G=nx.Graph()
 for n,g in groups.items():G.add_node(n,pos=nodepos(n),pins=sorted(term[q] for q in g if q in term),via=any(q in vianodes for q in g),raw=g)
 for a,c,d in G0.edges(data=True):
  aa,cc=uf[a],uf[c]
  if aa==cc:continue
  if G.has_edge(aa,cc):G[aa][cc]['uuids'].update(d['uuids']);G[aa][cc]['length']=min(G[aa][cc]['length'],d['length'])
  else:G.add_edge(aa,cc,**{**d,'uuids':set(d['uuids'])})
 graphs[net]=G;splitgraphs[net]=G0
 # Turning is measured only at unambiguous degree-2, same-layer, non-pad/non-via vertices.
 for n,d in G.nodes(data=True):
  if G.degree(n)!=2 or d['pins'] or d['via'] or len(d['raw'])!=1:continue
  aa,cc=list(G.neighbors(n));e1,e2=G[n][aa],G[n][cc]
  if e1['layer']!=e2['layer']:continue
  # Local segment endpoint directions (not remote collapsed pad centers).
  raw=next(iter(d['raw']));ns=list(G0.neighbors(raw))
  if len(ns)!=2:continue
  va=[ns[0][i+1]-raw[i+1] for i in [0,1]];vc=[ns[1][i+1]-raw[i+1] for i in [0,1]]
  if min(math.hypot(*va),math.hypot(*vc))<EPS:continue
  angle=180-math.degrees(math.acos(max(-1,min(1,sum(a*c for a,c in zip(va,vc))/math.hypot(*va)/math.hypot(*vc)))))
  if angle>=89.9:turns.append({'net':net,'at':d['pos'],'layer':e1['layer'],'turn_deg':round(angle,3),'uuids':sorted(e1['uuids']|e2['uuids'])})
 for cyc in nx.cycle_basis(G,root=next(iter(G))):
  edges=[G[a][c] for a,c in zip(cyc,cyc[1:]+cyc[:1])];length=sum(e['length'] for e in edges)
  if length<.05:continue
  cycles.append({'net':net,'length_mm':round(length,5),'points':[G.nodes[n]['pos'] for n in cyc],'uuids':sorted(set().union(*(e['uuids'] for e in edges))),'classification':'GND exception candidate' if net=='GND' else 'power/parallel review' if not net.startswith('/') or net in ['/USB5V_SW'] else 'signal review'})
 for n,d in G.nodes(data=True):
  if G.degree(n)!=1 or d['pins']:continue
  path=[n];prev=None;cur=n;uuids=set();length=0
  while True:
   nxt=[q for q in G.neighbors(cur) if q!=prev]
   if not nxt:break
   q=nxt[0];e=G[cur][q];length+=e['length'];uuids.update(e['uuids']);path.append(q);prev,cur=cur,q
   if G.degree(cur)!=2 or G.nodes[cur]['pins']:break
  stubs.append({'net':net,'end':d['pos'],'via_end':d['via'],'length_mm':round(length,5),'uuids':sorted(uuids),'points':[G.nodes[q]['pos'] for q in path],'zone_exception':net=='GND'})
 terminals=[n for n,d in G.nodes(data=True) if d['pins']];pairs=0
 for a,c in itertools.combinations(terminals,2):
  direct=math.dist(G.nodes[a]['pos'],G.nodes[c]['pos'])
  if direct<1 or not nx.has_path(G,a,c):continue
  path=nx.shortest_path(G,a,c,weight='length');length=sum(G[u][v]['length'] for u,v in zip(path,path[1:]));ratio=length/direct
  if ratio>1.8 and length-direct>3:
   pairs+=1;detours.append({'net':net,'pins':[G.nodes[a]['pins'],G.nodes[c]['pins']],'route_mm':round(length,4),'direct_mm':round(direct,4),'ratio':round(ratio,3),'excess_mm':round(length-direct,4),'points':[G.nodes[n]['pos'] for n in path],'uuids':sorted(set().union(*(G[u][v]['uuids'] for u,v in zip(path,path[1:]))))})
 complete=nx.Graph();centers=[p['at'] for p in ps]
 for ia,ic in itertools.combinations(range(len(centers)),2):complete.add_edge(ia,ic,weight=math.dist(centers[ia],centers[ic]))
 mst=sum(e['weight'] for _,_,e in nx.minimum_spanning_tree(complete).edges(data=True))
 row={'net':net,'segments':len(ts),'total_mm':round(sum(t['length'] for t in ts),5),'vias':len(vs),'min_width':min(t['width'] for t in ts),'max_width':max(t['width'] for t in ts),'pad_count':len(ps),'pad_center_MST_reference_mm':round(mst,5),'graph_components_with_pads':sum(any(G.nodes[n]['pins'] for n in comp) for comp in nx.connected_components(G)),'detour_pair_candidates':pairs,'turn_ge90':sum(q['net']==net for q in turns),'independent_cycle_candidates':sum(q['net']==net for q in cycles),'leaf_candidates':sum(q['net']==net for q in stubs)}
 netrows.append(row)
# Non-connected same-net pad/track proximity. Copper outline, not merely centerlines.
near=[];normal_extensions=[]
def local(p,q):
 x,y=q[0]-p['at'][0],q[1]-p['at'][1];a=math.radians(p['angle']);return x*math.cos(a)-y*math.sin(a),x*math.sin(a)+y*math.cos(a)
for p in pads:
 for t in tracks:
  if p['net']!=t['net'] or t['layer'] not in p['layers']:continue
  gap=p['geom'].distance(t['copper'])
  if gap>=CLEAR-EPS:continue
  centerhit=t['geom'].distance(p['geom'])<=.002 # 2um polygon/numeric tolerance
  if centerhit:continue # Intentional contacts checked separately using previous short-edge audit.
  q=nearest_points(t['geom'],p['geom'])[0].coords[0];qL=local(p,q);L=0 if p['size'][0]>=p['size'][1] else 1;S=1-L
  # Short-edge outward continuation is a normal connection region; preserve its list for review.
  if abs(qL[L])>=p['size'][L]/2-EPS and abs(qL[S])<=p['size'][S]/2-t['width']/2+EPS:
   normal_extensions.append({'pin':p['pin'],'uuid':t['uuid'],'gap_mm':round(gap,6)});continue
  near.append({'net':p['net'],'pin':p['pin'],'pad_uuid':p['uuid'],'track_uuid':t['uuid'],'gap_mm':round(gap,6),'at':q,'layer':t['layer'],'a':t['a'],'b':t['b'],'copper_contact':gap<EPS})
# IC inter-pad corridors between facing long sides. Exclude zones; count actual track copper penetration.
corridors=[]
for a,c in itertools.combinations([p for p in pads if p['ref'].startswith('U')],2):
 if a['ref']!=c['ref'] or abs(a['angle']-c['angle'])>EPS:continue
 sz=a['size'];L=0 if sz[0]>sz[1] else 1;S=1-L;q=local(a,c['at']);pitch=abs(q[S])
 if abs(q[L])>.02 or not (.15<pitch<=1.0) or sz!=c['size']:continue
 # Only immediately adjacent pads; a middle pad's ordinary fanout is not inter-pad routing.
 if any(z['ref']==a['ref'] and z['uuid'] not in [a['uuid'],c['uuid']] and abs(local(a,z['at'])[L])<.02 and min(0,q[S])+EPS<local(a,z['at'])[S]<max(0,q[S])-EPS for z in pads):continue
 lo=min(0,q[S])+sz[S]/2;hi=max(0,q[S])-sz[S]/2
 if hi-lo<.01:continue
 geom=box(-sz[L]/2,lo,sz[L]/2,hi) if L==0 else box(lo,-sz[L]/2,hi,sz[L]/2)
 geom=affinity.rotate(geom,-a['angle'],origin=(0,0));geom=affinity.translate(geom,*a['at']).buffer(-.002)
 for t in tracks:
  if t['layer'] not in a['layers']:continue
  overlap=t['copper'].intersection(geom)
  if overlap.area>.0001:
   corridors.append({'pads':[a['pin'],c['pin']],'net':t['net'],'uuid':t['uuid'],'layer':t['layer'],'area_mm2':round(overlap.area,6),'at':list(overlap.centroid.coords)[0],'centerline_inside_mm':round(t['geom'].intersection(geom).length,5)})
power=[];power_segments=[]
for net in sorted({t['net'] for t in tracks if 'USB5V' in t['net']}):
 ts=[t for t in tracks if t['net']==net];thin=[t for t in ts if t['width']<.5-EPS]
 power.append({'net':net,'total_mm':round(sum(t['length'] for t in ts),5),'min_width_mm':min(t['width'] for t in ts),'max_width_mm':max(t['width'] for t in ts),'under_0_5_segments':len(thin),'under_0_5_total_mm':round(sum(t['length'] for t in thin),5),'widths':{str(w):round(sum(t['length'] for t in ts if t['width']==w),5) for w in sorted({t['width'] for t in ts})}})
 for t in thin:
  close=sorted((p['geom'].distance(t['geom']),p['pin'],min(p['size'])) for p in pads if p['net']==net and t['layer'] in p['layers'])[:2]
  power_segments.append({**serial(t),'near_pads':close,'status':'candidate, necessity not approved'})
write('nets.json',netrows);write('turns_ge90.json',turns);write('cycles.json',cycles);write('open_leaf_candidates.json',stubs);write('detours.json',sorted(detours,key=lambda x:-x['excess_mm']));write('duplicate_overlap.json',duplicates);write('pad_near.json',near);write('normal_short_edge_extensions.json',normal_extensions);write('pad_corridors.json',corridors);write('usb5v_widths.json',power);write('usb5v_thin_segments.json',power_segments)
with (OUT/'net_lengths.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(netrows[0]));w.writeheader();w.writerows(netrows)
summary={'source_commit':BASE,'source_sha256':START,'tracks':len(tracks),'vias':len(vias),'nets_with_tracks':len(netrows),'total_track_mm':round(sum(t['length'] for t in tracks),5),'turn_ge90':len(turns),'detour_pairs':len(detours),'detour_nets':len({q['net'] for q in detours}),'independent_cycles':len(cycles),'non_GND_cycles':sum(q['net']!='GND' for q in cycles),'leaf_candidates':len(stubs),'non_GND_leaf_candidates':sum(q['net']!='GND' for q in stubs),'duplicate_overlap_pairs':len(duplicates),'near_pad_track_pairs':len(near),'near_unique_tracks':len({q['track_uuid'] for q in near}),'corridor_track_pair_hits':len(corridors),'corridor_unique_tracks':len({q['uuid'] for q in corridors}),'usb5v':power,'graph_disconnected_non_GND':[r for r in netrows if r['net']!='GND' and r['graph_components_with_pads']>1]}
assert hashlib.sha256(BOARD.read_bytes()).hexdigest()==START
write('summary.json',summary);print(json.dumps(summary,ensure_ascii=False,indent=2))
