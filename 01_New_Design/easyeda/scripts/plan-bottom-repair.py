"""Plan local 2D copper paths from official API geometry. Apply only via EasyEDA API.

This is a conservative 0.05 mm grid search, not an ERC/DRC substitute.
All existing foreign-net bottom traces and through vias are obstacles.
The search omits standalone mechanical pad obstacles; final native DRC is mandatory. Pours are rebuilt in CAD.
"""
import json, math, heapq
from pathlib import Path
import numpy as np
b=Path(__file__).resolve().parents[1]
src=json.loads((b/'reports/bottom-repair-input.json').read_text(encoding='utf-8-sig'))['value']
step=.05; x0,y0=.4,.4; nx,ny=425,985
xx=x0+np.arange(nx)*step; yy=y0+np.arange(ny)*step
traces=[dict(net=l['net'],a=[l['startX']*.0254,l['startY']*.0254],z=[l['endX']*.0254,l['endY']*.0254],width=l['lineWidth']*.0254) for l in src['lines'] if l['layer']==2]
vias=[dict(net=v['net'],p=[v['x']*.0254,v['y']*.0254],d=v['diameter']*.0254) for v in src['vias']]
for v in vias:
    if v['net']=='EECLK' and math.dist(v['p'],[14.8,36.7502])<.01:v['p']=[16.0,36.35]
power_pins=[['FB1',1,19.5,45.5,.6,.3],['R3',1,20,43.45,.6,.3],['U5',8,20.9,39.85,.4572,.2032],['C17',1,20.4,35.18,.6,.3],['C10',1,17.2749,35.8,.6,.3]]
vias.extend(dict(net='V3V3',p=p[2:4],d=p[4]) for p in power_pins)
def capsule(block,a,z,r):
    ix0=max(0,int(math.floor((min(a[0],z[0])-r-x0)/step)));ix1=min(nx,int(math.ceil((max(a[0],z[0])+r-x0)/step))+1)
    iy0=max(0,int(math.floor((min(a[1],z[1])-r-y0)/step)));iy1=min(ny,int(math.ceil((max(a[1],z[1])+r-y0)/step))+1)
    if ix0>=ix1 or iy0>=iy1:return
    X=xx[ix0:ix1][None,:];Y=yy[iy0:iy1][:,None]; dx=z[0]-a[0];dy=z[1]-a[1];l2=dx*dx+dy*dy
    t=np.clip(((X-a[0])*dx+(Y-a[1])*dy)/(l2 or 1),0,1)
    block[iy0:iy1,ix0:ix1]|=(X-a[0]-t*dx)**2+(Y-a[1]-t*dy)**2<=r*r
def route(net,start,end,width=.18):
    blocked=np.zeros((ny,nx),dtype=bool);margin=width/2+.127+.025
    for t in traces:
        if t['net']!=net:capsule(blocked,t['a'],t['z'],t['width']/2+margin)
    for v in vias:
        if v['net']!=net:capsule(blocked,v['p'],v['p'],v['d']/2+margin)
    def node(p):return (round((p[0]-x0)/step),round((p[1]-y0)/step))
    s=node(start);g=node(end)
    for p in [s,g]:
        if not (0<=p[0]<nx and 0<=p[1]<ny):raise ValueError('Endpoint outside region')
        if blocked[p[1],p[0]]:raise ValueError(f'{net}: endpoint is blocked {p}')
    dist={s:0.};parents={};queue=[(math.dist(s,g),0.,s)];found=False
    moves=[(a,c,math.hypot(a,c)) for a,c in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]]
    while queue:
        _,cost,p=heapq.heappop(queue)
        if cost>dist[p]+1e-9:continue
        if p==g:found=True;break
        for dx,dy,d in moves:
            q=(p[0]+dx,p[1]+dy)
            if not (0<=q[0]<nx and 0<=q[1]<ny) or blocked[q[1],q[0]]:continue
            if dx and dy and (blocked[p[1],q[0]] or blocked[q[1],p[0]]):continue
            nc=cost+d
            if nc<dist.get(q,float('inf')):
                dist[q]=nc;parents[q]=p;heapq.heappush(queue,(nc+math.dist(q,g),nc,q))
    if not found:raise ValueError(f'No path {net}: {start} -> {end}')
    seq=[g]
    while seq[-1]!=s:seq.append(parents[seq[-1]])
    seq.reverse();simple=[seq[0]]
    for i in range(1,len(seq)-1):
        if (seq[i][0]-seq[i-1][0],seq[i][1]-seq[i-1][1])!=(seq[i+1][0]-seq[i][0],seq[i+1][1]-seq[i][1]):simple.append(seq[i])
    simple.append(seq[-1]);pts=[start]+[[round(x0+x*step,5),round(y0+y*step,5)] for x,y in simple]+[end]
    pts=[p for i,p in enumerate(pts) if i==0 or math.dist(p,pts[i-1])>.00001]
    for a,z in zip(pts,pts[1:]):traces.append(dict(net=net,a=a,z=z,width=width))
    return dict(net=net,layer=2,width=width,path=pts,length=sum(math.dist(a,z) for a,z in zip(pts,pts[1:])))
jobs=[('V3V3',[14.8778,35.6900],[14.8,37.75]),('EECLK',[16.0,36.35],[15.5951,40.5302]),('V3V3',[17.2749,35.8],[14.8,37.75]),('V3V3',[20.4,35.18],[17.2749,35.8]),('V3V3',[20.9,39.85],[20.4,35.18]),('V3V3',[20,43.45],[20.9,39.85]),('V3V3',[19.5,45.5],[20,43.45])]
out=[]
for net,a,z in jobs:
    p=route(net,a,z,.127 if net=="EECLK" else .18);out.append(p);print(net,len(p['path']),round(p['length'],3))
(b/'reports/bottom-repair-plan.json').write_text(json.dumps(dict(routes=out,powerPins=power_pins,gridMm=step,clearanceMm=.127,planningMarginMm=.025),indent=2)+'\n',encoding='utf-8')
