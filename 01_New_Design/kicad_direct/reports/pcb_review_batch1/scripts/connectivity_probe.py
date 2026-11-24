from local_tools import *
b.BuildConnectivity(); cn=b.GetConnectivity()
for ref,n in [('U1',43),('U2',12),('U1',45)]:
 a=pad(ref,n);ts=list(cn.GetConnectedItems(a));print(ref,n,[(str(type(t)),t.GetNetname()) for t in ts][:5],len(ts));print('tracks',len(list(cn.GetConnectedTracks(a))))
