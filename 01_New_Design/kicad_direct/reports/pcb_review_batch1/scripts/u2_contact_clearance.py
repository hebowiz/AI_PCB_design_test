from common import *
for t in list(b.GetTracks()):
 if t.GetNetname()=='/FT_RTS_N':
  if isinstance(t,p.PCB_VIA):
   if xy(t.GetPosition())==(109.4,128.85):t.SetPosition(v(109.4,129.5))
  else:
   for get,set in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
    if xy(get())==(109.4,128.85):set(v(109.4,129.5))
 elif t.GetNetname()=='/RTS_N' and not isinstance(t,p.PCB_VIA) and t.GetLayer()==p.F_Cu:
  for get,set in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
   pt=xy(get())
   if pt==(111.975,130.25):set(v(112.075,130.25))
   elif pt==(112.9,129.325):set(v(113.0,129.325))
drc('u2_contacts_clearance')
