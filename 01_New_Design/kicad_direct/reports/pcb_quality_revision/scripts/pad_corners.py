from geom import *
import numpy as np
assert BOARD.parent==OUT.resolve()/'candidate'
snapshot=BOARD.read_bytes();ok=False;changes=[]
try:
 sites=[('/FT_TXD',(108,113.25)),('+3V3',(117,117.75)),('/LED_RX_A',(104.55,112)),('/LED_TX_A',(101.95,112)),('/PWR_EN',(110.25,137.15)),('VPHY',(117.9,111.95)),('/PWREN_N',(114.925,128.025)),('/PWREN_N',(114.925,127.375)),('USB5V',(116.3,117.25))]
 for net,q in sites:
  pair=[t for t in b.GetTracks() if not isinstance(t,k.PCB_VIA) and t.GetNetname()==net and t.GetLayer()==0 and min(math.dist(q,xy(t.GetStart())),math.dist(q,xy(t.GetEnd())))<.00001]
  if len(pair)!=2:continue
  old=[record(t) for t in pair];ends=[]
  for t in pair:
   other=xy(t.GetStart()) if math.dist(q,xy(t.GetEnd()))<.00001 else xy(t.GetEnd());a=np.array(other)-np.array(q);d=min(.12,np.linalg.norm(a)*.35);end=np.array(q)+a/np.linalg.norm(a)*d;ends.append(tuple(end))
   if math.dist(q,xy(t.GetStart()))<.00001:t.SetStart(v(*end))
   else:t.SetEnd(v(*end))
  tnew=track(*ends,net,w=min(k.ToMM(t.GetWidth()) for t in pair));changes.append({'before':old,'after':[record(t) for t in pair]+[record(tnew)]})
 r=drc('pad_approach_corners');(OUT/'pad_approach_corners_second.json').write_text(json.dumps(changes,indent=2))
 if r['violations'] or r['unconnected_items']:raise RuntimeError('DRC gate failed')
 ok=True
finally:
 if not ok:
  (OUT/'checks/pad_corners_failed.kicad_pcb').write_bytes(BOARD.read_bytes());BOARD.write_bytes(snapshot)
