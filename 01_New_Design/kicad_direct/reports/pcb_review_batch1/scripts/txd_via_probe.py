from common import *
for t in b.GetTracks():
 if isinstance(t,p.PCB_VIA) and t.GetNetname()=='/FT_TXD':print(t.m_Uuid.AsString(),xy(t.GetPosition()))
