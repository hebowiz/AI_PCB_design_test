from local_tools import *
pts={(104.5,110.75),(102.8,110.75),(102.8,108.0),(106.6,108.0),(107.1,108.5)};removed=[]
for t in list(b.GetTracks()):
 if not isinstance(t,p.PCB_VIA) and t.GetNetname()=='+3V3' and t.GetLayer()==p.F_Cu and xy(t.GetStart()) in pts and xy(t.GetEnd()) in pts:removed.append(t.m_Uuid.AsString());remove(t)
refresh();ok,n=route((4.5,10.75,0),endpoint(pad('FB2',1)),b.FindNet('+3V3').GetNetCode(),True);assert ok;print('FB2 supply',ok,n);(OUT/'fb2_supply_reroute.json').write_text(json.dumps({'removed':removed,'ok':ok,'visited':n},indent=2));drc('fb2_supply')
b.BuildConnectivity();cn=b.GetConnectivity();floating=[]
for t in list(b.GetTracks()):
 if not isinstance(t,p.PCB_VIA) or t.GetNetname()!='GND':continue
 connected=list(cn.GetConnectedItems(t));ps=[a for a in connected if isinstance(a,p.PAD)]
 if not ps:floating.append({'uuid':t.m_Uuid.AsString(),'pos':xy(t.GetPosition()),'items':len(connected)})
(OUT/'floating_ground_probe.json').write_text(json.dumps(floating,indent=2));print('floating GND',floating)
