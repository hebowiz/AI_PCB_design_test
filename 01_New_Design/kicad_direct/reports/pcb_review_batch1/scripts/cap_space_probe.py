from common import *
for t in b.GetTracks():
 if not isinstance(t,p.PCB_VIA) and t.GetNetname() in ['/EE_DATA','/EE_DO','VPLL'] and t.GetLayer()==p.F_Cu:print(t.m_Uuid.AsString(),t.GetNetname(),xy(t.GetStart()),xy(t.GetEnd()))
