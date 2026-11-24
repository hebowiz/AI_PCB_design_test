from geom import *
for t in b.GetTracks():
 if t.GetNetname()=='+3V3' and min(xy(t.GetStart())[0],xy(t.GetEnd())[0])<108 and min(xy(t.GetStart())[1],xy(t.GetEnd())[1])<112:print(record(t))
