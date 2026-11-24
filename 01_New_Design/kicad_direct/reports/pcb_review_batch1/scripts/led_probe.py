from common import *
for t in b.GetTracks():
 if not isinstance(t,p.PCB_VIA) and t.GetNetname()=='/RXLED_N':print(t.m_Uuid.AsString(),t.GetLayer(),xy(t.GetStart()),xy(t.GetEnd()))
