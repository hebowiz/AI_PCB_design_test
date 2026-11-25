from common import *
plans=[(['71252d23-0a08-49c3-bfb5-5c2d2dc8b800','dfd4f114-2f58-4e65-85c7-a8157a6c5fa2','e9e80068-2c29-41e8-a4ba-ada8e395794a'],'USB5V',.5,[xy(pad('U4',1).GetPosition()),(102.15,128.55),(101.8,128.2),(101.7,128.2)]),(['a1875b06-203b-472d-987f-cfc0a9fb6556','c34f7aae-b96c-4003-9536-4a49f73474d4'],'/PWR_EN',.15,[xy(pad('U4',3).GetPosition()),(102.05,130.45),(102.05,133.15),(102.4,133.5)]),(['8cbd9ba7-31d5-41d1-9b83-980b1a55d3dd','c6044e6d-bc4c-4273-8f06-4b32dd0200cc','ef4b8c37-f672-4dfe-aab3-7e077f33c1de','fc2b6cf2-875e-4d34-9637-16d5d6a7349c'],'/FB',.15,[xy(pad('U4',4).GetPosition()),(106.3,130.45),(106.55,130.2),(106.55,130.0),(106.1,129.55),(105.5,129.55),(105.5,129.4)]),(['0da900fe-2a98-4dac-94a9-ca0d849e5952','17517666-a2de-45f5-b2a9-71d9573e2d04','491962b2-3ff0-440a-9f88-fcd3e7f67b33'],'VIO',.3,[xy(pad('U4',5).GetPosition()),(106.2,128.55),(106.55,128.2)])]
for ids,net,w,pts in plans:
 for t in list(b.GetTracks()):
  if uid(t) in ids:remove(t)
 for a,c in zip(pts,pts[1:]):track(a,c,net,w=w)
drc('escapes')
