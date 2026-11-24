from common import *
# Resolve the transition clearance without adding another layer change.
for t in list(b.GetTracks()):
 if not isinstance(t,p.PCB_VIA) and t.GetNetname()=='/USB_D+' and t.GetWidth()==p.FromMM(.15):remove(t)
line([(111.5,109.25),(110.75,110.0),(110.75,111.8375)],'/USB_D+',w=.15)
for t in list(b.GetTracks()):
 if not isinstance(t,p.PCB_VIA) and t.GetNetname()=='/XTAL_IN' and (xy(t.GetStart())==(118.6,109.98) or xy(t.GetStart())==(118.6,109.5)):remove(t)
line([(118.6,109.98),(117.33,109.98),(116.85,109.5)],'/XTAL_IN',w=.15)
save()
