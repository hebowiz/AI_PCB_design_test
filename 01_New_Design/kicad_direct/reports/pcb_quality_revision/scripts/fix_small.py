from local_router import *
from ground import stitch_ground
assert BOARD.parent==OUT.resolve()/'candidate'
snapshot=BOARD.read_bytes();ok=False;mode=sys.argv[1];before=[];new=[]
try:
 if mode=='usb_reference_margin':
  for t in list(b.GetTracks()):
   if t.GetNetname()=='USB5V' and not isinstance(t,k.PCB_VIA) and t.GetLayer()==k.B_Cu and max(xy(t.GetStart())[1],xy(t.GetEnd())[1])<104.2:before.append(record(t));remove(t)
  assert len(before)==4
  pts=[(117.35,104.15),(114.9,104.15),(114.55,103.8),(109.3,103.8),(108.95,104.15)]
  new=[track(a,c,'USB5V',k.B_Cu,.5) for a,c in zip(pts,pts[1:])]
 elif mode=='last_stubs':
  jobs=[('/LED_PWR_A',['0cf576c4-b556-4622-86df-0ee80f3bf64f','43923a49-0a8b-4c8c-92ce-f26c0090f793','d39e0e8f-fd70-4253-930e-bbd22b59b11d'],[(119.51,103),(119.51,103.35),(119,103.86),(119,104.2125)]),('/TXD',['194892a6-eacc-4921-b0d4-fba15c378aa6','37c6b96f-84f4-4df1-923e-782677bc3178','56e4a7cb-1d78-4af6-851e-0bae0497c4d9','73d30707-20f8-4d8d-b668-c2fae31e0939'],[(108.45,140.95),(108.45,144.52),(109.73,145.8),(109.73,147.3)])]
  for net,ids,pts in jobs:
   for t in list(b.GetTracks()):
    if uid(t) in ids:before.append(record(t));remove(t)
   new.extend(track(a,c,net) for a,c in zip(pts,pts[1:]))
  for id in ['19c31e4c-f9e5-475e-994a-e5f9d31ef86d','bc7fd6a2-57d2-4cb1-b1d2-08ff211897b9']:
   t=next(t for t in b.GetTracks() if uid(t)==id);before.append(record(t));t.SetStart(v(113.45,130.55))
 elif mode=='power_approaches':
  ids=['b8c9d373-9961-4163-9a0f-f2d87c8b82e3','dace96f7-bbd7-4f82-92f0-b1158f3f3fea','ff69d4a6-a62b-4e76-aad1-bf4b907b08b4']
  for t in list(b.GetTracks()):
   if uid(t) in ids:before.append(record(t));remove(t)
  t=next(t for t in b.GetTracks() if uid(t)=='5ef77dc2-6d76-4fcb-b7da-8a177d49217b');before.append(record(t));t.SetStart(v(107.75,125.95))
  pts=[(107.75,125.95),(107.6,126.1),(107.35,126.1),(107.1,126.35),(107.1,126.725)]
  new=[track(a,c,'+3V3') for a,c in zip(pts,pts[1:])]+[track((105.38,118.75),(106.8375,118.75),'+3V3')]
 elif mode=='headers':
  jobs=[('/RXD',['0ad1312a-5f2e-4d65-9125-e0819cd03e7f','885bbf16-7178-4b13-82f3-ab6e867f97de','aa9af04b-8529-45f7-b188-0593b292c5ea','b8d4bcbf-55fc-42e0-9548-bae899537967','668b620d-8024-4bae-98e5-8229eda392c8'],[(113,145.05),(112.27,145.78),(112.27,147.3)]),('/RTS_N',['110b012c-1499-4f89-82dc-4782a2cd9764','1ecbc5a3-f976-46a5-ae09-ff89c3fd8758','429f7871-e899-40e3-a10d-52fa5ee61075','dd31f523-b5f8-4549-a41c-2adadc32fef7'],[(107.85,140.75),(107.19,141.41),(107.19,143.655)]),('VIO_OUT',['01bdad41-d648-476d-8f33-05d0bc6da5d4','15d0360a-f895-4fbc-901a-bcd16b9f32cb','9394c841-db4d-4a68-8a2d-9e1a9212e150','e4edb783-7f15-449f-979d-e0c5b75d15d2'],[(114.81,140.345),(114.81,141.95),(116.61,143.75),(118.27,143.75)])]
  for net,ids,pts in jobs:
   for t in list(b.GetTracks()):
    if uid(t) in ids:before.append(record(t));remove(t)
   new.extend(track(a,c,net) for a,c in zip(pts,pts[1:]))
 elif mode=='usb_projection':
  t=next(t for t in b.GetTracks() if uid(t)=='10f9e893-f0b9-4655-981f-97dd5fc061e2');before.append(record(t));remove(t)
  pts=[(117.35,104.15),(114.9,104.15),(114.75,104.0),(109.1,104.0),(108.95,104.15)]
  new=[track(a,c,'USB5V',k.B_Cu,.5) for a,c in zip(pts,pts[1:])]
 elif mode=='cycle':
  ids=['1cb26978-5c1f-4a51-bf66-1dd407ccbdb7','8f0940af-7ba3-417e-a8b7-2df2419c2833']
  for t in list(b.GetTracks()):
   if uid(t) in ids:before.append(record(t));remove(t)
  t=next(t for t in b.GetTracks() if uid(t)=='18e39734-d75c-4196-86b5-4ad083affde6');before.append(record(t));t.SetStart(v(113.05,122.5))
 elif mode=='ft_txd':
  net='/FT_TXD'
  for t in list(b.GetTracks()):
   if t.GetNetname()==net and not isinstance(t,k.PCB_VIA) and t.GetLayer()==0 and max(xy(t.GetStart())[1],xy(t.GetEnd())[1])<118:before.append(record(t));remove(t)
  new=[track(xy(pad('U1',13).GetPosition()),(108,113.25),net)]
  rr=route((108,113.25),(111.35,117.55),net,.15,(),[(108,113.25),(111.35,117.55)])
  if not rr:raise RuntimeError('FT_TXD path failed')
  new+=rr
  ids=['04a78638-de51-4809-9bd4-11e1ed713643','31188d4d-8e7d-4a4c-bfaa-9b3443869430','5b1f6e67-2f16-4b02-b054-10f45501af3a','9c6b5c7c-5ac7-4e25-8eb4-c3484ad6e76d','e9b071f8-c580-4c2c-ab7e-3f25d8783be4','b1e82cf6-3739-488f-8ca7-dd2cda2d1192']
  for t in list(b.GetTracks()):
   if uid(t) in ids:before.append(record(t));remove(t)
  new+=[track(xy(pad('U2',4).GetPosition()),(109.0,128.675),net),track((109.0,128.675),(109.1,128.575),net),track((109.1,128.575),(109.1,127.75),net)]
 else:raise ValueError(mode)
 stitches=stitch_ground();r=drc(mode);(OUT/(mode+'_changes.json')).write_text(json.dumps({'before':before,'new':[record(t) for t in new],'ground':stitches},indent=2))
 if r['violations'] or r['unconnected_items']:raise RuntimeError('DRC gate failed')
 ok=True
finally:
 if not ok:
  if BOARD.read_bytes()!=snapshot:(OUT/'checks'/(mode+'_failed.kicad_pcb')).write_bytes(BOARD.read_bytes());BOARD.write_bytes(snapshot)
