from local_tools import *
from scipy.ndimage import label
net=b.FindNet('GND').GetNetCode();mask,vm=masks(net);lab,n=label(~mask.reshape(2,r.H,r.W)[0],np.ones((3,3)))
for ref in ['C23','C8','C7','C10']:
 a=pad(ref,2);q=endpoint(a);x,y,z=r.decode(r.node(*q));reg=lab==lab[y,x];valid=reg&~vm.reshape(r.H,r.W);ys,xs=np.where(valid);print(ref,q,'blocked',mask[r.node(*q)],'area',reg.sum(),'vias',valid.sum());print('closest',sorted([(math.hypot(xx*r.STEP-q[0],yy*r.STEP-q[1]),xx*r.STEP+100,yy*r.STEP+100) for xx,yy in zip(xs,ys)])[:3])
