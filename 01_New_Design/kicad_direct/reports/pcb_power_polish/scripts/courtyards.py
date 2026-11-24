from geom import *
for r in ['C1','C2','C3','C5','C6','C7','C8','C11','C12','C23','FB1','U1','Y1']:
 f=fps[r];pts=[xy(q) for g in f.GraphicalItems() if g.GetLayer()==k.F_CrtYd for q in [g.GetStart(),g.GetEnd()]]
 print(r,xy(f.GetPosition()),[min(p[j] for p in pts) for j in [0,1]]+[max(p[j] for p in pts) for j in [0,1]])
