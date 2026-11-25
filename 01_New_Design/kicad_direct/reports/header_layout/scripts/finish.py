from common import *
for t in list(b.GetTracks()):
 if t.GetNetname()=='VIO' and (math.dist(xy(t.GetStart()),(106.95,128.2))<.01 or math.dist(xy(t.GetEnd()),(106.95,128.2))<.01):remove(t)
 # replace U4 output launch
 elif t.GetNetname()=='VIO' and t.GetLayer()==0 and xy(t.GetEnd())==(106.8,128.35):remove(t)
q=(106.9,127.5);via(q,'VIO')
pts=[xy(pad('U4',5).GetPosition()),(106.6,128.35),(106.6,127.8),q]
for a,c in zip(pts,pts[1:]):track(a,c,'VIO',w=.3)
track(q,(106.1,128.3),'VIO',k.B_Cu,.3);track((106.1,128.3),(106.1,129.05),'VIO',k.B_Cu,.3)
pts=[xy(pad('R8',2).GetPosition()),(111.9,133.85),(112.27,134.22),xy(pad('J3',3).GetPosition())]
for a,c in zip(pts,pts[1:]):track(a,c,'GND',w=.2)
for r,p in {'U4':(104.6,127.1),'R17':(104.7,133.2),'R7':(111,131.5),'R8':(111,134.8),'C19':(108,134.1)}.items():fps[r].Reference().SetPosition(v(*p))
drc('finish1')
