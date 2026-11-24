from local_tools import *
b.BuildConnectivity();cn=b.GetConnectivity()
for ref in ['U1','U2','U5']:
 for a in fps[ref].Pads():
  key=ref+'.'+a.GetNumber()
  if key not in fanouts:continue
  items=list(cn.GetConnectedItems(a))
  if len(items)<5: print(key,a.GetNetname(),len(items),[xy(t.GetPosition()) for t in items])
