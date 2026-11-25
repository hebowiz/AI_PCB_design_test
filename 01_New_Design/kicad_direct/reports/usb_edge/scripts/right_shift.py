from common import *
old=k.LoadBoard(str(OUT/'before/a2_usb_uart.kicad_pcb'));of={f.GetReference():f for f in old.GetFootprints()};ots={uid(t):t for t in old.GetTracks()};byid={uid(t):t for t in b.GetTracks()}
def replace_id(i,pts,w=None):
 t=byid[i];net=t.GetNetname();z=t.GetLayer();width=k.ToMM(t.GetWidth()) if w is None else w;remove(t)
 for a,c in zip(pts,pts[1:]):track(a,c,net,z,width)
def remove_id(i):remove(byid[i])
# Courtyard trial: downward Y1 relocation cannot fit between J1 and U1.
# Retain its orientation and shift right by 1.325 mm instead.
fps['Y1'].SetPosition(v(117.325,108.4));fps['C13'].SetPosition(v(119.925,109.5))
fps['FB1'].SetPosition(v(120.6,107.6));fps['C11'].SetPosition(v(119.2,111.85))
# Restore only the two local oscillator networks from the approved baseline,
# then translate the right-hand portions. All unrelated traces remain untouched.
for t in list(b.GetTracks()):
 if t.GetNetname() in ['/XTAL_IN','/XTAL_OUT']:remove(t)
for o in ots.values():
 if o.GetNetname() not in ['/XTAL_IN','/XTAL_OUT']:continue
 t=o.Duplicate();t.SetParent(b);b.Add(t);KEEP.append(t)
 if t.GetNetname()=='/XTAL_IN':
  for get,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
   x,y=xy(get())
   if x>=117.0 or (x==116.85 and y==109.5):setter(v(x+1.325,y))
 # extend the unchanged OUT cap link into the moved top-left crystal pad
 elif uid(o)=='d8e6d420-3398-4b38-a7e7-fb0e11408bd6':t.SetStart(v(113.35,107.32));t.SetEnd(v(116.475,107.32))
 elif uid(o)=='dbd31f0c-27e6-4896-8cc2-d663320cff38':
  t.SetEnd(v(115.15,107.4));track((115.15,107.4),(116.475,107.4),'/XTAL_OUT')
# Remove the trial Y1 GND rail extensions and reconnect to its original ground rail.
for t in list(b.GetTracks()):
 if t.GetNetname()=='GND' and xy(t.GetStart()) in [(116,108.1),(116.225,107.875)]:remove(t)
# Lower GND via and connection follow Y1; no USB underside signal added.
byid['411d18db-95d9-4336-9df4-225c29e467fa'].SetPosition(v(115.125,109.62))
byid['acb688bd-d713-4d52-92c9-b3da26ad7698'].SetStart(v(116.825,109.6));byid['acb688bd-d713-4d52-92c9-b3da26ad7698'].SetEnd(v(115.125,109.6))
# The upper ground rail feeds Y1 pad2 through filled copper, with explicit link.
track((116,108.1),(116.8,107.3),'GND');track((116.8,107.3),(118.175,107.3),'GND')
# Move the USB5V continuation to the board's right edge on B.Cu, outside USB/XTAL return corridors.
for i in ['25201e61-6567-44df-820b-ae650f237b3b','9505f1ee-8f6b-4567-94cf-302060baf7bc','83baa72f-1930-44fd-8b6c-992a166defea']:remove_id(i)
pts=[(117.35,104.85),(119.8,104.85),(121.35,106.4),(121.35,107.65)]
for a,c in zip(pts,pts[1:]):track(a,c,'USB5V',k.B_Cu,.5)
via((121.35,107.65),'USB5V')
# R13 branch avoids D2 pad2; narrower 0402 pad escape is documented separately.
for t in list(b.GetTracks()):
 if t.GetNetname()=='USB5V' and xy(t.GetStart()) in [(118.49,103),(118.49,103.71)]:remove(t)
track((118.49,103),(118.2,103.29),'USB5V',w=.3)
track((118.2,103.29),(118.2,104),'USB5V',w=.3)
track((118.2,104),(117.35,104.85),'USB5V',w=.3)
# FB1 supply and filtered output follow its local relocation.
replace_id('852b8241-18b6-4051-8b16-71a042caf7e8',[(120,108.2),(120,107.715),(120.6,107.115)])
for i in ['5c399ad8-993e-4c63-afc3-cb536fa5144c','69610d82-d106-4b43-8914-7db80c3ca155','8e25be75-3902-4427-8c89-8131daf488f0','dc6f3d2f-1455-4963-a7be-fdce5f97f951']:remove_id(i)
pts=[(120.6,108.085),(119.83,108.085),(119.23,108.685),(119.23,110.7),(118.25,111.68),(118.25,111.85)]
for a,c in zip(pts,pts[1:]):track(a,c,'VPHY',w=.15)
# Keep the existing C11 output into the VPHY rail and its GND return; pad copper remains connected.
fps['C14'].Reference().SetPosition(v(113.45,108.75));fps['C14'].Reference().SetTextAngle(k.EDA_ANGLE(0,k.DEGREES_T));fps['C14'].Reference().SetTextSize(v(.55,.55))
drc('right_shift')
