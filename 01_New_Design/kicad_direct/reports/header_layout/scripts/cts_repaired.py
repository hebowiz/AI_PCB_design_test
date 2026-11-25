from local_router import *
# Choose a rule-compliant GND via near pin 9, then preserve that return during CTS reconnection.
mask,vm=masks('GND',.2,['U2.9'],[xy(pad('U2',9).GetPosition())]);q0=xy(pad('U2',9).GetPosition())
options=[]
for x in np.arange(111.8,115.5,.05):
 for y in np.arange(130.7,132.5,.05):
  q=(round(x,2),round(y,2));n=node(q,0)
  if not vm[n] and not mask[n]:options.append((math.dist(q,q0),q))
print('via candidates',options[:8],flush=True)
for _,q in sorted(options):
 path,_=astar(node(q0,0),node(q,0),mask,vm,False)
 if path:
  via(q,'GND');assert route(q0,q,'GND',.2,['U2.9'],[q0,q],0,0);save();print('chosen',q,flush=True);break
# CTS: existing right hand pin branch plus untouched lower B.Cu endpoint.
q0=xy(pad('U2',10).GetPosition());end=(114.25,131.95)
assert route(q0,end,'/CTS_N',.15,['U2.10','R12.2'],[q0,end],0,1)
drc('cts_repaired')
