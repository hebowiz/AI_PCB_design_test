from common import *
for t in b.GetTracks():
 if not isinstance(t,p.PCB_VIA) and t.GetNetname()=='+3V3' and t.GetLayer()==p.F_Cu and 118<max(xy(t.GetStart())[1],xy(t.GetEnd())[1])<121.5:print(t.m_Uuid.AsString(),xy(t.GetStart()),xy(t.GetEnd()))
