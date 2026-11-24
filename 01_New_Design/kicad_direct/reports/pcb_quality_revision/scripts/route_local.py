from local_router import *
from ground import stitch_ground
assert BOARD.parent==OUT.resolve()/'candidate'
net=sys.argv[1];tag=net.replace('/','').replace('+','')+'_local';snapshot=BOARD.read_bytes();ok=False;old=[];new=[]
try:
 if net=='+3V3_cleanup':
  net='+3V3';ids=['b84639b8-d3cf-4c5a-9d6d-244344c9a4ea','def2b4b0-077c-4a51-857b-722be1457c98','b6d5fbf3-0a07-411e-b7d4-d604e86e4ff2','8817c669-9b45-4699-adb1-2f463955be92']
  old=[t for t in b.GetTracks() if uid(t) in ids];assert len(old)==len(ids)
  for t in old:remove(t)
  new=[track((105.5,118.75),(107.85,121.1),net)]
  t=next(t for t in b.GetTracks() if uid(t)=='01e2c207-0024-4deb-b3c8-f9eb145f3fc2');t.SetEnd(v(107.85,122.025))
  t=next(t for t in b.GetTracks() if uid(t)=='61fe9b99-736a-4105-a4ba-af69942a772b');t.SetStart(v(107.85,122.05))
 elif net=='RXD_move':
  net='/RXD'
  ids=['f8d6ea99-3204-4623-b0b2-42e42c989011','abde24d2-b352-4397-84ca-b6865742bee7','90dee4e8-559f-4ef2-a6e5-77cbe8e5016f','5a059fba-7a6e-4ebb-8ef8-f182d99ac2bd','7780e166-20c5-4147-9627-b56df6851670','e1df9015-bef6-4a4b-a30a-d162caaea5fe','58a93222-4ce6-40b5-88c8-36b67f75f121','e7952fee-98c1-40e2-b4da-33ff9785a504']
  old=[t for t in b.GetTracks() if uid(t) in ids];assert len(old)==len(ids)
  for t in old:remove(t)
  q=(117.1,128.2);new=[via(q,net)]
  for a,c,pins,layer in [(xy(pad('R11',2).GetPosition()),q,['R11.2'],0),(q,(115.4,129.949999),[],1)]:
   rr=route(a,c,net,.15,pins,[a,c],layer,layer)
   if not rr:raise RuntimeError('RXD local relocation route failed')
   new+=rr
 elif net in ['/EE_CLK','/EE_DATA']:
  vv=[t for t in b.GetTracks() if t.GetNetname()==net and isinstance(t,k.PCB_VIA)];assert len(vv)==2
  old=[t for t in b.GetTracks() if t.GetNetname()==net and not isinstance(t,k.PCB_VIA) and t.GetLayer()==k.B_Cu]
  for t in old:remove(t)
  a,c=[xy(t.GetPosition()) for t in vv]
  new=route(a,c,net,.15,(),[a,c],1,1)
 elif net=='/PWREN_N':
  import local_router as lr
  lr.STEP=.025;lr.W=881;lr.H=2001;lr.PLANE=lr.W*lr.H
  ids=['d933afac-8a13-416e-891d-476c6363960c','255a05c4-1c18-45ba-8da3-82d39bb3fd0f','1b132cea-24a6-4774-bac9-9f996e9c38ba','40367966-b4dd-4b7e-813e-0902a84758cf','4a12a2d2-911b-42bf-90a0-b216a83d173a','bcc32354-0191-48e8-929d-c07259281f47','f4060ec6-5590-4a56-90b4-c60cba5f835d','5eb69b78-6784-4f94-b359-557f1446c014','fd5234ea-92e1-4e4e-a538-a6a47f92a3ca','2d15f809-55e6-4ef4-accb-9d7257e959d0']
  old=[t for t in b.GetTracks() if uid(t) in ids];assert len(old)==len(ids)
  for t in old:remove(t)
  for id in ['027e2ead-f8ad-468a-999a-38bc83af5874','7e36d34e-68ef-4065-825c-e5608e8d8bcc']:
   t=next(t for t in b.GetTracks() if uid(t)==id);t.SetEnd(v(114.925,xy(t.GetEnd())[1]))
  new=[track((114.925,127.375),(114.925,128.025),net,w=.15)]
  q=(115.45,127.65);new.append(via(q,net));new.append(track((114.925,127.7),(115.4,127.7),net));new.append(track((115.4,127.7),q,net))
  rr=route((112.2,121.65),q,net,.15,(),[(112.2,121.65),q],1,1)
  if rr:new+=rr
  else:new=None
 else:raise ValueError(net)
 if not new:raise RuntimeError('no feasible local route')
 if net in ['/EE_CLK','/EE_DATA']:
  before=sum(k.ToMM(t.GetLength()) for t in old);after=sum(k.ToMM(t.GetLength()) for t in new if not isinstance(t,k.PCB_VIA))
  print('length',before,after)
  if after>=before-.1:raise RuntimeError('no length improvement')
 stitches=stitch_ground();result=drc(tag)
 (OUT/(tag+'.json')).write_text(json.dumps({'before':[record(t) for t in old],'after':[record(t) for t in new],'ground':stitches},indent=2))
 if result['violations'] or result['unconnected_items']:raise RuntimeError('DRC gate failed')
 ok=True
finally:
 if not ok:
  if BOARD.read_bytes()!=snapshot:(OUT/'checks'/(tag+'_failed.kicad_pcb')).write_bytes(BOARD.read_bytes());BOARD.write_bytes(snapshot)
