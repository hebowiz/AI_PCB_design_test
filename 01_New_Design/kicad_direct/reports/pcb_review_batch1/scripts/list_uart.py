from common import *
for t in b.GetTracks():
 if t.GetNetname() in ['/RXD','/RTS_N','/FT_CTS_N','/TXD','/FT_RTS_N','/CTS_N'] and (min(xy(t.GetStart())[1],xy(t.GetEnd())[1])<132 and max(xy(t.GetStart())[1],xy(t.GetEnd())[1])>125):print(t.m_Uuid.AsString(),t.GetNetname(),t.GetLayerName(),xy(t.GetStart()),xy(t.GetEnd()),isinstance(t,p.PCB_VIA))
