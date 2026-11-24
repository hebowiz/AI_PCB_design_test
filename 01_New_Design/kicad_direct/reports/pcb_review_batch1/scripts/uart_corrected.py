from common import *
fan=json.loads((OUT/'fanouts.json').read_text())
for t in list(b.GetTracks()):
 if t.GetNetname()=='GND' and not isinstance(t,p.PCB_VIA) and math.dist(xy(t.GetStart()),(108.1375,131.275))<.0001 and math.dist(xy(t.GetEnd()),(109.175,130.625))<.0001:remove(t)
fan['U2.8']=[107.1,131.275]
a=pad('U2',7);assert a.GetNetname()=='/FT_CTS_N';pt=xy(a.GetPosition());new=[109.175,pt[1]];tr(pt,new,a.GetNetname(),w=.15);fan['U2.7']=new
(OUT/'fanouts.json').write_text(json.dumps(fan,indent=2));save();drc('uart_corrected')
