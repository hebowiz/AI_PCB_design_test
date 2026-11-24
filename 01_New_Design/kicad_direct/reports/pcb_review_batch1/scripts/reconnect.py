from local_tools import *
# Reconnect only DRC-identified missing links in the locally modified board.
name=sys.argv[1] if len(sys.argv)>1 else 'reconnect1'
prev=sys.argv[2] if len(sys.argv)>2 else 'cleanup2'
j=json.loads((OUT/'after'/('drc_'+prev+'.json')).read_text())
idx={str(t.m_Uuid.AsString()):t for t in b.GetTracks()};idx.update({str(a.m_Uuid.AsString()):a for f in b.GetFootprints() for a in f.Pads()})
def ep(t):
 if isinstance(t,p.PAD):return endpoint(t)
 if isinstance(t,p.PCB_VIA):return endpoint(t)
 a,c=xy(t.GetStart()),xy(t.GetEnd())
 for key,pt in fanouts.items():
  if min(math.dist(a,pt),math.dist(c,pt))<.0001:return pt[0]-100,pt[1]-100,0
 return endpoint(t)
log=[]
links=[]
for e in j['unconnected_items']:
 ts=[idx.get(x['uuid']) for x in e['items']]
 if not all(t is not None for t in ts):continue
 a,c=ts
 if a.GetNetname()=='GND':continue
 links.append((math.dist(ep(a)[:2],ep(c)[:2]),a,c))
for _,a,c in sorted(links,key=lambda x:x[0]):
 net=a.GetNetCode();aa,cc=ep(a),ep(c)
 ok,n=route(aa,cc,net,False)
 if not ok:ok,n=route(aa,cc,net,True)
 log.append({'net':a.GetNetname(),'a':aa,'b':cc,'ok':ok,'visited':n});print(log[-1],flush=True)
 if ok:save();refresh()
(OUT/(name+'.json')).write_text(json.dumps(log,indent=2))
j=drc(name);print('DRC',len(j['violations']),len(j['unconnected_items']),flush=True)
