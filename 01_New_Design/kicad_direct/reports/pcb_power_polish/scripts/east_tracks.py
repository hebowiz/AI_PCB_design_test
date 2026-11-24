from common import *
for t in b.GetTracks():
 if (t.GetNetname()=='USB5V' and min(xy(t.GetStart())[0],xy(t.GetEnd())[0])>116 and min(xy(t.GetStart())[1],xy(t.GetEnd())[1])<119) or (t.GetNetname()=='+3V3' and min(xy(t.GetStart())[0],xy(t.GetEnd())[0])>115 and max(xy(t.GetStart())[1],xy(t.GetEnd())[1])<114): print(record(t))
