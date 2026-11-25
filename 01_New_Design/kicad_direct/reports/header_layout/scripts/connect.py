from local_router import *
# Bound added routes to the local repair zone, leaving USB/crystal and upstream copper untouched.
import local_router as lr
orig_masks=lr.masks
def local_masks(*a,**kw):
 mask,vm=orig_masks(*a,**kw);mask=mask.reshape((2,H,W));mask[:,:int((124.5-100)/STEP),:]=True
 vm=vm.reshape((H,W));vm[:int((124.5-100)/STEP),:]=True
 return mask.reshape(-1),vm.reshape(-1)
lr.masks=local_masks
anchors={};new=[]
def launch(ref,num,width=.15):
 key=ref+'.'+str(num)
 if key in anchors:return anchors[key]
 p=pad(ref,num);q=xy(p.GetPosition());f=xy(fps[ref].GetPosition());bb=p.GetBoundingBox();half=[k.ToMM(bb.GetWidth())/2,k.ToMM(bb.GetHeight())/2]
 axis=0 if ref.startswith('U') or ref.startswith('SW') else (1 if ref in ['J2','J3'] else (0 if abs(q[0]-f[0])>abs(q[1]-f[1]) else 1))
 sign=(1 if ref=='J2' or key=='J3.1' else -1 if ref=='J3' else (1 if q[axis]>=f[axis] else -1))
 end=list(q);end[axis]+=sign*(half[axis]+.4)
 end[axis]=(math.ceil(end[axis]*20) if sign>0 else math.floor(end[axis]*20))/20
 # Keep passive fractional pin coordinates; router makes orthogonal/45-degree joins.
 w=min(width,half[1-axis]*2-.05)
 new.append(track(q,end,p.GetNetname(),w=w));anchors[key]=(tuple(end),0,p.GetNetname());return anchors[key]
def raw(q,z,net):return (q,z,net)
def join(a,c,width=.15):
 assert a[2]==c[2]
 rr=route(a[0],c[0],a[2],width,(),[a[0],c[0]],a[1],c[1])
 if not rr:raise RuntimeError('Cannot route '+str((a,c)))
 new.extend(rr);save(False)
# Repair the two cut FT_RXD segments, then power conditioning and feedback.
byid={uid(t):t for t in b.GetTracks()}
def end(id,which):t=byid[id];return raw(xy(t.GetStart() if which==0 else t.GetEnd()),0 if t.GetLayer()==k.F_Cu else 1,t.GetNetname())
# Exact endpoints of remaining isolated copper are selected from the unconnected record.

# Reserve every short-edge launch before solving routes, so later terminals cannot be boxed in.
for ref,num,w in [('U4',1,.5),('U4',3,.15),('U4',4,.15),('U4',5,.3),('C18',1,.5),('C19',1,.3),('R7',1,.3),('R7',2,.15),('R8',1,.15),('R9',1,.15),('R10',1,.15),('R10',2,.15),('R12',1,.3),('SW1',4,.15),('SW2',3,.5),('SW3',3,.3),('SW3',2,.3),('J2',2,.15),('J2',3,.15),('J2',4,.5),('J3',1,.15),('J3',2,.15),('J3',4,.3),('R17',2,.5),('TP2',1,.5)]:launch(ref,num,w)
a=launch('U4',5,.3);c=launch('C19',1,.3)
q=(106.95,128.2);z=(106.1,133.0)
new.extend([track(a[0],(106.95,128.2),'VIO',w=.3),via(q,'VIO'),via(z,'VIO'),track(z,c[0],'VIO',w=.3)])
join(raw(q,1,'VIO'),raw(z,1,'VIO'),.3)
join(end('236b6805-6ff3-459c-9baa-18ce0b834cd4',1),end('1377423d-f81b-4b2c-a3ea-d802c07f29a9',0))
join(launch('U4',3),end('9278c5fb-e0d9-47fd-a7aa-d93dab8856e8',0))
join(launch('J2',2),end('7f6fafd5-5e63-4190-8373-459647155aca',1))
join(launch('U4',4),launch('R8',1))
join(launch('R8',1),launch('R7',2))
join(launch('R7',2),launch('R10',1))
join(launch('R10',1),launch('R9',1))
join(launch('R10',2),launch('SW1',4))
join(launch('J3',1),end('958f9440-dc86-4d9b-9bf1-95d2d0d5cef5',0))
join(launch('C18',1,.5),launch('U4',1,.5),.5)
join(launch('C18',1,.5),end('205d488c-53d0-4557-a73d-3a141332cf28',0),.5)
join(launch('SW2',3,.5),end('205d488c-53d0-4557-a73d-3a141332cf28',0),.5)
join(launch('R17',2,.5),launch('TP2',1,.5),.5)
join(launch('TP2',1,.5),launch('J2',4,.5),.5)
join(launch('C19',1,.3),launch('R7',1,.3),.3)
join(launch('R7',1,.3),launch('R12',1,.3),.3)
join(launch('R12',1,.3),end('4707fe81-e0d1-4568-91e8-068a82b20df1',1),.15)
join(launch('SW3',3,.3),end('ad6bb027-6635-4940-9f98-6284ac00585a',0),.3)
join(launch('J3',4,.3),launch('SW3',2,.3),.3)
join(launch('J2',3),end('bc7fd6a2-57d2-4cb1-b1d2-08ff211897b9',1))
join(launch('J3',2),end('305b272b-6953-4351-aa46-f1a14ee3032e',0))
join(end('302fea01-bdb7-47d1-a975-849851461fcb',0),end('889bb623-8173-4edc-a3eb-1201c3d331bc',1))
(OUT/'new_routes.json').write_text(json.dumps([record(t) for t in new if t],indent=2))
drc('connected')
