from local_tools import *
from scipy.ndimage import label
b.BuildConnectivity();cn=b.GetConnectivity()
for ref,num in [('U2',7),('U1',15)]:
 a=pad(ref,num);net=a.GetNetCode();mask,vm=masks(net);lab,n=label(~mask.reshape(2,r.H,r.W)[0],np.ones((3,3)))
 q=endpoint(a);x,y,z=r.decode(r.node(*q));region=lab==lab[y,x];valid=region&~vm.reshape(r.H,r.W)
 print(ref,num,a.GetNetname(),'endpoint',q,'blocked',mask[r.node(*q)],'area',int(region.sum()),'legalvias',int(valid.sum()))
 ts=list(cn.GetConnectedItems(a));print([(type(t).__name__,xy(t.GetPosition()),xy(t.GetEnd()) if isinstance(t,p.PCB_TRACK) else '') for t in ts if not isinstance(t,p.ZONE)])
