from local_router import *
ids=['c4280ae9-9137-4a6f-90bf-4b2ebab6187b','e0a02a74-35da-4897-84f8-37d36798ad27','ac05593f-69c0-4297-b27a-5e1d2e1836e0','d7876d31-8301-41a6-9f21-96137dd33c48','ea68016a-9977-4c61-b056-5b316378df51']
for t in list(b.GetTracks()):
 if uid(t) in ids or (t.GetNetname()=='VIO' and min(xy(t.GetStart())[1],xy(t.GetEnd())[1])<129.05 and max(xy(t.GetStart())[0],xy(t.GetEnd())[0])<107):remove(t)
a=(106.8,128.35);track(xy(pad('U4',5).GetPosition()),a,'VIO',w=.3)
q=(106.95,128.2);track(a,q,'VIO',w=.3);via(q,'VIO');track(q,(106.1,129.05),'VIO',k.B_Cu,.3)
for r,p in {'U4':(104.6,128.0),'R17':(104.7,130.9),'C19':(108.3,134.0)}.items():fps[r].Reference().SetPosition(v(*p))
save();from ground import stitch_ground
(OUT/'ground_repair.json').write_text(json.dumps(stitch_ground(),indent=2))
drc('finish2')
