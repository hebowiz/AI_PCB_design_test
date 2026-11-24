from common import *
fps['D1'].Reference().SetPosition(v(110.55,107.65))
for t in list(b.GetTracks()):
 if uid(t)=='55786471-5082-4b8d-85ec-c8201fc57321':remove(t)
 if uid(t)=='1a051c6a-b57d-44ee-ae86-bc5cd2eaf62f':t.SetEnd(v(106.85,126.6));track((106.85,126.6),(106.9,126.6),'+3V3',k.F_Cu,.18)
drc('release')
