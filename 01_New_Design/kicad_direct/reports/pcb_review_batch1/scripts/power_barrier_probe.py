from common import *
for t in b.GetTracks():
 if not isinstance(t,p.PCB_VIA) and t.GetLayer()==p.B_Cu and 121<xy(t.GetStart())[1]<122.5:print(t.GetNetname(),t.m_Uuid.AsString(),xy(t.GetStart()),xy(t.GetEnd()))
