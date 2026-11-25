from common import *
byid={uid(t):t for t in b.GetTracks()}
def edit(i,a=None,c=None):
 t=byid[i]
 if a:t.SetStart(v(*a))
 if c:t.SetEnd(v(*c))
def replace(i,pts):
 t=byid[i];net=t.GetNetname();layer=t.GetLayer();w=k.ToMM(t.GetWidth());remove(t)
 for a,c in zip(pts,pts[1:]):track(a,c,net,layer,w)
def rm(i):remove(byid[i])
# USB5V follows the moved locator row; keep 0.5 mm widths.
edit('6217b76d-2053-4f7f-b993-e286f254461b',(108,103.85),(115.1,103.85))
edit('e21c575b-8e60-457b-a01f-c99d8ffec5a4',(108,103.85),(107.5,104.35))
edit('f1d24d5b-8196-472b-8e91-e7b5fef1864e',c=(107.5,104.35))
edit('854ad0dd-6682-4c3b-b613-be2b1558fb10',(108.95,104.75),(108.05,103.85))
byid['704aaf7e-0204-4981-a414-bb03e598f9eb'].SetPosition(v(108.95,104.75))
edit('3059052e-e1d4-49b0-a6a5-e0621d43ad51',(109.3,104.4),(108.95,104.75))
edit('43051655-9742-4134-b95b-b6a3e11e46dc',(114.55,104.4),(109.3,104.4))
edit('b50ed579-c961-4070-a369-e39329042449',(115,104.85),(114.55,104.4))
edit('395f7711-05ee-4a2a-b56d-7f7dd797add8',(117.35,104.85),(115,104.85))
byid['412e1af7-e990-43de-b66d-5cb1bf79e865'].SetPosition(v(117.35,104.85))
replace('1fb042c6-f4a2-4ebf-9bfd-02cb8b28307a',[(118.49,103),(118.49,103.71),(117.35,104.85)])
edit('25201e61-6567-44df-820b-ae650f237b3b',(115.1,103.85),(118.6,107.35))
edit('9505f1ee-8f6b-4567-94cf-302060baf7bc',(118.6,107.35))
# C12 GND via moves clear of the new J1 VBUS pad, keeping 0.3/0.6 drill/ring.
byid['46f896ba-725d-43c1-99f3-49f0df793df7'].SetPosition(v(106.3,105.9))
replace('3c3b8792-c263-4c41-86cc-aa52e40bb468',[(107.65,107.7),(106.3,106.35),(106.3,105.9)])
# Shift Y1 0.15 mm left to retain C11 courtyard clearance.
fps['Y1'].Move(v(-.15,-.025))
# D1 ground uses the vertical corridor just left of C14.
for t in list(b.GetTracks()):
 if t.GetNetname()=='GND' and xy(t.GetStart())==(112.55,107.4) and xy(t.GetEnd())==(113.15,106.8):
  remove(t);track((112.55,107.4),(112.8,107.15),'GND');track((112.8,107.15),(112.8,106.8),'GND');track((112.8,106.8),(113.15,106.45),'GND');track((113.15,106.45),(113.15,106.4),'GND')
 # Remove the trial upper stub, replaced by the corridor above.
 elif t.GetNetname()=='GND' and xy(t.GetStart())==(113.15,106.8) and xy(t.GetEnd())==(113.15,106.4):remove(t)
# Remove only old XTAL_IN near-crystal segments; U1 fanout stays fixed.
for i in ['0d5e1e22-bdde-4373-9788-3a8ef6acb0d6','34380ddf-523a-4eec-8e15-ef18779b71df','a14fb41f-5e83-4892-9d11-1dae497a4f88','e579f53b-11d7-407f-9cb5-56e0b629e6e0']:rm(i)
for t in list(b.GetTracks()):
 if t.GetNetname()=='/XTAL_IN' and (xy(t.GetStart()) in [(117.6,110.25),(117.41,110.06)]):remove(t)
edit('e24899b7-23e7-4cbd-ba05-0a0305929efc',c=(113.75,109.3))
pts=[(113.75,109.3),(114.05,109),(117.4,109),(117.6,109.2),(117.6,109.7),(117.225,110.075),(116.7,110.075)]
for a,c in zip(pts,pts[1:]):track(a,c,'/XTAL_IN')
# Existing C13 branch at y109.98 joins the sloping crystal input within 0.1 mm of its end.
# End the upper ground rail at Y1 pad2; no cross through crystal signal corridor.
rm('bd48e421-0551-4bda-8617-e08d423907d8');rm('18ce2857-2829-4e17-a707-b5c1346bd005')
track((116,108.1),(116.225,107.875),'GND');track((116.225,107.875),(116.7,107.875),'GND')
fps['C14'].Reference().SetPosition(v(114,108.75));fps['C14'].Reference().SetTextSize(v(.65,.65))
drc('local_reconnect')
