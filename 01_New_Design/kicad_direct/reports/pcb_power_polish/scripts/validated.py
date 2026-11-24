from geom import *
fps['D1'].Reference().SetPosition(v(110.6,107.65))
# Remove the overlapping C16 source tail; the source joins the same straight bus.
for t in b.GetTracks():
 if uid(t)=='55786471-5082-4b8d-85ec-c8201fc57321':t.SetEnd(v(106.9,126.6))
drc('validated')
