from common import *
byid={uid(t):t for t in b.GetTracks()}
def rm(i):remove(byid[i])
def linepts(net,pts,w=.15,z=k.F_Cu):
 for a,c in zip(pts,pts[1:]):track(a,c,net,z,w)
fps['C11'].SetPosition(v(119.2,111.5));fps['D2'].Move(v(0,-.25))
# Drop only the unused end of the old upper ground rail (no pad/via terminates there).
for i in ['3068c697-3ce9-47d7-9c7e-baf4b08e93e8','c55eb208-6b8d-46d8-a41b-c3621a04ea1d','d2ca20b2-dc59-440e-b78e-41e68ed1cc62','717c52d3-3d6f-44e2-9634-dae589694eab']:rm(i)
for t in list(b.GetTracks()):
 if t.GetNetname()=='GND' and xy(t.GetStart()) in [(116,108.1),(116.8,107.3)]:remove(t)
linepts('GND',[(113.0025,106.35),(113.1,106.35),(113.15,106.4)])
via((118,105.9),'GND');linepts('GND',[(118,105.9),(118,106.125),(118.175,106.3),(118.175,107.3)],.2)
# Shorten unused USB5V rail tail now that the continuation is on B.Cu.
byid['6217b76d-2053-4f7f-b993-e286f254461b'].SetEnd(v(108.05,103.85))
# XTAL_IN wraps immediately below Y1; retain C11 in its reviewed original position.
for t in list(b.GetTracks()):
 if t.GetNetname()=='/XTAL_IN':remove(t)
linepts('/XTAL_IN',[(113.75,111.8375),(113.75,110.8),(114.05,110.5),(118.5,110.5),(118.7,110.3),(118.7,110.025),(118.175,109.5)])
linepts('/XTAL_IN',[(119.925,109.98),(118.655,109.98)])
# Filter supply via outside the crystal return corridor.
byid['a13add4e-eb0b-4b38-9e80-15451c2050e3'].SetPosition(v(119.75,106.5))
for t in list(b.GetTracks()):
 if t.GetNetname()=='+3V3' and xy(t.GetStart()) in [(120,108.2),(120,107.715)]:remove(t)
linepts('+3V3',[(119.75,106.5),(119.985,106.5),(120.6,107.115)],.25)
linepts('+3V3',[(119.75,106.5),(120.7,107.45),(120.7,110.2),(120,110.9)],.2,k.B_Cu)
# Filter output skirts C13, with a 0.15 mm local passage between C13 and C11.
for t in list(b.GetTracks()):
 if t.GetNetname()=='VPHY' and xy(t.GetStart()) in [(120.6,108.085),(119.83,108.085),(119.23,108.685),(119.23,110.7),(118.25,111.68)]:remove(t)
linepts('VPHY',[(120.6,108.085),(120.85,108.335),(120.85,110.15),(120.5,110.5),(119.1,110.5),(118.25,111.35),(118.25,111.5)],.15)
fps['C14'].Reference().SetPosition(v(114.2,108.3));fps['C14'].Reference().SetTextSize(v(.6,.6));fps['C14'].Reference().SetTextAngle(k.EDA_ANGLE(90,k.DEGREES_T))
fps['FB1'].Reference().SetPosition(v(121.4,107.7));fps['FB1'].Reference().SetTextSize(v(.6,.6));fps['FB1'].Reference().SetTextAngle(k.EDA_ANGLE(90,k.DEGREES_T))
drc('compact_routes')
