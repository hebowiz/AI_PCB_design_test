from local_tools import *
prev=sys.argv[1] if len(sys.argv)>1 else 'reconnect2';name=sys.argv[2] if len(sys.argv)>2 else 'islands';j=json.loads((OUT/'after'/('drc_'+prev+'.json')).read_text());logs=[]
def points(items,mask):
 out={}
 for t in items:
  if isinstance(t,p.PAD):qs=[endpoint(t)]
  elif isinstance(t,p.PCB_VIA):
   x,y=r.xy(t.GetPosition());qs=[(x,y,z) for z in [0,1]]
  elif isinstance(t,p.PCB_TRACK):
   a,c=xy(t.GetStart()),xy(t.GetEnd());z=0 if t.GetLayer()==p.F_Cu else 1;n=max(1,math.ceil(math.dist(a,c)/.4));qs=[(a[0]+(c[0]-a[0])*i/n-100,a[1]+(c[1]-a[1])*i/n-100,z) for i in range(n+1)]
  else:continue
  for q in qs:
   node=r.node(*q)
   if not mask[node]:out[node]=q
 return list(out.values())
for e in sorted(j['unconnected_items'],key=lambda e: 'LED' in str(e)):
 idx={str(t.m_Uuid.AsString()):t for t in b.GetTracks()};idx.update({str(a.m_Uuid.AsString()):a for f in b.GetFootprints() for a in f.Pads()})
 ts=[idx.get(x['uuid']) for x in e['items']]
 if not all(t is not None for t in ts) or ts[0].GetNetname()=='GND':continue
 b.BuildConnectivity();cn=b.GetConnectivity();aa=list(cn.GetConnectedItems(ts[0]));cc=list(cn.GetConnectedItems(ts[1]));uids={t.m_Uuid.AsString() for t in aa}
 if ts[1].m_Uuid.AsString() in uids:continue
 net=ts[0].GetNetCode();mask,_=masks(net);ap=points(aa,mask);cp=points(cc,mask)
 if len(ap)>len(cp):ap,cp=cp,ap
 if not ap or not cp:print('no points',ts[0].GetNetname(),len(ap),len(cp),flush=True);continue
 ap.sort(key=lambda a:min(math.dist(a[:2],c[:2]) for c in cp))
 ok=False
 for a in ap[:8]:
  ok,n=route(a,cp[0],net,True,targets=cp)
  if ok:break
 logs.append({'net':ts[0].GetNetname(),'ok':ok,'start_candidates':len(ap),'target_candidates':len(cp),'visited':n});print(logs[-1],flush=True)
 if ok:save();refresh()
(OUT/(name+'_reconnect.json')).write_text(json.dumps(logs,indent=2));drc(name)
