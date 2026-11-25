from common import *
removed=[]
for t in list(b.GetTracks()):
 a,c=xy(t.GetStart()),xy(t.GetEnd())
 if t.GetNetname()=='GND' and (a,c) in [((112.8,107.15),(112.8,106.8)),((112.8,106.8),(113.15,106.45)),((113.15,106.45),(113.15,106.4))]:removed.append(record(t));remove(t)
 if t.GetNetname()=='/XTAL_OUT':
  if a==(115.15,107.4) and c==(116.475,107.4):removed.append(record(t));remove(t)
  elif a==(113.25,109.3) and c==(115.15,107.4):t.SetEnd(v(115.23,107.32))
(OUT/'trial_overlap_cleanup.json').write_text(json.dumps(removed,indent=2));drc('clean_local')
