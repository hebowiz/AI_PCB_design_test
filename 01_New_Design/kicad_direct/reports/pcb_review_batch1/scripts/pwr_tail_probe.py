from common import *
for t in b.GetTracks():
 if t.GetNetname()=='/PWR_EN' and not isinstance(t,p.PCB_VIA) and 136<max(xy(t.GetStart())[1],xy(t.GetEnd())[1]):print(t.m_Uuid.AsString(),xy(t.GetStart()),xy(t.GetEnd()))
