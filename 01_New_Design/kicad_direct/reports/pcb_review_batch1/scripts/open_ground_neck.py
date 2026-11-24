from common import *
old=(111.35,118.25);new=(111.35,117.55)
for t in b.GetTracks():
 if t.GetNetname()!='/FT_TXD':continue
 if isinstance(t,p.PCB_VIA):
  if xy(t.GetPosition())==old:t.SetPosition(v(*new))
 else:
  if xy(t.GetStart())==old:t.SetStart(v(*new))
  if xy(t.GetEnd())==old:t.SetEnd(v(*new))
# Restore the LED link temporarily removed during ground-path diagnosis.
tr((110.05,121.7),(110.05,116.65),'/RXLED_N',p.B_Cu,.15)
drc('ground_neck_open')
