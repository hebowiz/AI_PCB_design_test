from common import *
for t in b.GetTracks():
 if not isinstance(t,p.PCB_VIA) and t.GetNetname()=='+3V3' and t.GetLayer()==p.F_Cu and min(xy(t.GetStart())[0],xy(t.GetEnd())[0])>116 and 113<min(xy(t.GetStart())[1],xy(t.GetEnd())[1])<118:print(t.m_Uuid.AsString(),xy(t.GetStart()),xy(t.GetEnd()))
