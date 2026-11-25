from common import *
# Run once on the private candidate copied from 5cce544. No whole-board rerouting.
assert xy(fps['J1'].GetPosition())==(111.0,93.775)
changes={'J1':(0,.6),'D1':(0,.4),'D5':(0,.4),'Y1':(0,.6),'C14':(0,.1),'C12':(0,.15)}
for ref,(dx,dy) in changes.items():fps[ref].Move(v(dx,dy))
byid={uid(t):t for t in b.GetTracks()}
def edit(i,a=None,c=None):
 t=byid[i]
 if a:t.SetStart(v(*a))
 if c:t.SetEnd(v(*c))
def replace(i,pts):
 t=byid[i];net=t.GetNetname();layer=t.GetLayer();w=k.ToMM(t.GetWidth());remove(t)
 for a,c in zip(pts,pts[1:]):track(a,c,net,layer,w)
# Keep the 0.8 mm / 0.2 mm USB pair, layer crossover and U1 fanout.
edit('4ea3a493-742d-4384-9dac-880a989c7fc0',(110,105.35),(110,106.45))
edit('c635de9a-615f-4620-a8f6-aedc2d9600fd',(110,106.45),(110.5,106.95))
edit('03e23a3b-fb7e-441a-8ec9-c445180429bf',(110.5,106.95))
edit('d87fcc24-8c09-45f3-8200-9abf92e9ab2e',(112,105.35),(112,106.45))
edit('2d665e00-6e19-43fe-bd1d-bf389c138011',(112,106.45),(111.5,106.95))
edit('dffb9042-8bd8-4250-bbf7-80d4e0c61503',(111.5,106.95))
edit('b6821417-42e2-4e28-99e1-dee960812839',(110.15,107.4),(110.5,107.4))
edit('d5eda4cd-7080-4ffd-9ab1-9ab6ab451688',(111.85,107.4),(111.5,107.4))
edit('f1d24d5b-8196-472b-8e91-e7b5fef1864e',(107.5,105.35))
# D1 uses its existing upper GND via; remove only the now-colliding duplicate via/spur.
remove(byid['69e4fe37-68bd-4b73-9d54-be9be81b48d4']);remove(byid['e051f4a6-8824-4e8a-bc80-e8f6e9258642'])
replace('64f0058e-34de-4100-8c9b-a4def86af180',[(112.55,107.4),(113.15,106.8),(113.15,106.4)])
edit('7762d1e9-a726-48ad-be9b-18ea15811cba',(109.45,107.4),(109.3,107.4))
replace('f7540016-8e53-496e-999b-a9e50d3468a4',[(109.3,107.4),(108.8,106.9),(108.8,106.5)])
# Y1 moved towards U1. Retain the existing lower XTAL routes, reconnect upper ends.
replace('d8e6d420-3398-4b38-a7e7-fb0e11408bd6',[(113.35,107.32),(113.87,107.32),(114.45,107.9),(115.15,107.9)])
edit('dbd31f0c-27e6-4896-8cc2-d663320cff38',(113.25,109.3),(114.65,107.9))
# Terminate into Y1 pad 1 from its right edge; C13 stays in place.
replace('f1ea4655-4698-4214-913b-37461954eff0',[(117.6,110.25),(117.41,110.06),(116.85,110.06)])
# Upper GND support for the shifted DNP capacitor remains short.
edit('3c3b8792-c263-4c41-86cc-aa52e40bb468',(107.65,107.7))
(OUT/'placement_plan.json').write_text(json.dumps(changes,indent=2))
drc('initial_move')
