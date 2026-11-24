"""Independent quasi-static 2-D finite-volume odd-mode microstrip estimate.
Half-plane symmetry: pair center x=0 at 0 V, right conductor at 1 V.
Zdiff=2/(c*sqrt(Codd*Codd_air)); infinite straight pair, not a via/pad model.
"""
from pathlib import Path
import sys,os,json,math
sys.path.insert(0,str(Path(os.environ['TEMP'])/'a2-pcb-calculation-packages'))
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
OUT=Path(__file__).resolve().parents[1]
def solve(w,s,h=1.51,t=.035,er=4.5,fine=.02,extent=10):
 # Nonuniform mesh with nodes exactly on conductor and substrate interfaces.
 a=s/2;end=a+w
 x=np.unique(np.r_[np.linspace(0,a,max(4,int(a/fine)+1)),np.linspace(a,end,int(w/fine)+2),end+np.geomspace(fine,extent,55)])
 y=np.unique(np.r_[np.linspace(0,h,int(h/(fine*2))+2),h+np.linspace(0,t,5),h+t+np.geomspace(fine/2,extent,65)])
 nx,ny=len(x),len(y);xx,yy=np.meshgrid(x,y)
 metal=(xx>=a-1e-9)&(xx<=end+1e-9)&(yy>=h-1e-9)&(yy<=h+t+1e-9)
 fixed=metal.copy();fixed[:,0]=True;fixed[0,:]=True;fixed[:,-1]=True;fixed[-1,:]=True
 dx=np.diff(x);dy=np.diff(y);xdual=np.r_[dx[0]/2,(dx[:-1]+dx[1:])/2,dx[-1]/2];ylo=np.r_[y[0],(y[:-1]+y[1:])/2];yhi=np.r_[(y[:-1]+y[1:])/2,y[-1]]
 ids=np.arange(nx*ny).reshape(ny,nx);free=~fixed.ravel();values=np.zeros(nx*ny);values[metal.ravel()]=1
 results=[]
 for eps in [er,1]:
  yinteg=(yhi-ylo)+(eps-1)*np.maximum(0,np.minimum(yhi,h)-np.minimum(ylo,h))
  gx=yinteg[:,None]/dx[None,:]
  gy=np.where(y[:-1]<h-1e-9,eps,1)[:,None]*xdual[None,:]/dy[:,None]
  l=np.r_[ids[:,:-1].ravel(),ids[:-1,:].ravel()];r=np.r_[ids[:,1:].ravel(),ids[1:,:].ravel()];g=np.r_[gx.ravel(),gy.ravel()]
  mat=coo_matrix((np.r_[g,g,-g,-g],(np.r_[l,r,l,r],np.r_[l,r,r,l])),shape=(nx*ny,nx*ny)).tocsr()
  rhs=-(mat@values)[free];pot=values.copy();pot[free]=spsolve(mat[free][:,free],rhs)
  charge=(mat@pot)[metal.ravel()].sum()*8.8541878128e-12
  residual=float(np.max(np.abs((mat@pot)[free])))
  results.append([charge,residual])
 return {'width_mm':w,'gap_mm':s,'height_mm':h,'copper_mm':t,'er':er,'mesh_step_mm':fine,'far_boundary_mm':extent,'nodes':nx*ny,'Zdiff_ohm':2/(299792458*math.sqrt(results[0][0]*results[1][0])),'Codd_F_per_m':results[0][0],'Codd_air_F_per_m':results[1][0],'max_residual':max(z[1] for z in results),'model':'2-D quasi-static uncoated coupled microstrip; vias, pad transitions, soldermask and dispersive loss excluded'}
if __name__=='__main__':
 results=[]
 for w in [.5,.6,.7,.8,1.0,1.2]:
  r=solve(w,.2);results.append(r);print(w,round(r['Zdiff_ohm'],3),flush=True)
 (OUT/'impedance_sweep.json').write_text(json.dumps(results,indent=2))
