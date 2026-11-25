from local_router import *
free=[f.GetReference()+'.'+p.GetNumber() for f in fps.values() for p in f.Pads() if p.GetNetname()=='GND']
for a,c in [(('J3',3),('C19',2)),(('U2',3),('U2',8)),(('U2',9),('C17',2))]:
 qa=xy(pad(*a).GetPosition());qc=xy(pad(*c).GetPosition());rr=route(qa,qc,'GND',.15,free,[qa,qc],0,0)
 print(a,c,bool(rr),flush=True)
 if rr:save()
drc('gnd_routes')
