from local_router import *
for t in list(b.GetTracks()):
 if t.GetNetname()=='GND' and min(xy(t.GetStart())[1],xy(t.GetEnd())[1])>131.25 and max(xy(t.GetStart())[1],xy(t.GetEnd())[1])<131.91 and max(xy(t.GetStart())[0],xy(t.GetEnd())[0])<113.9:remove(t)
 elif uid(t) in ['305b272b-6953-4351-aa46-f1a14ee3032e','a0e7b2fa-f0a3-4200-b8ba-f7a034496f5f']:
  print('replaceCTS',record(t));remove(t)
q=xy(pad('U2',10).GetPosition());end=(109.85,137.1)
z=(112.6,131.0);via(z,'/CTS_N');pts=[q,(112.85,130.625),(112.6,130.875),z]
for a,c in zip(pts,pts[1:]):track(a,c,'/CTS_N')
assert route(z,end,'/CTS_N',.15,(),[z,end],1,1)
drc('cts_final')
