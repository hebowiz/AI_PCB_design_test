"""Local geometric repair for four nets omitted/incomplete after SES import.
export/import modes use KiCad Python; solve uses numpy and Pillow.
Conservative raster obstacles are checked again with KiCad DRC after import.
"""
import json, math, os, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
NETS=os.environ.get('A1_ROUTE_NETS','FT_TXD,FT_RXD').split(','); GRID=.05
def export():
    import pcbnew as k
    b=k.LoadBoard(str(ROOT/'board/a1.kicad_pcb'));tracks=list(b.GetTracks());zones=list(b.Zones())
    for z in zones:b.Remove(z)
    for t in tracks:
        if t.GetNetname() in NETS:b.Remove(t)
    k.SaveBoard(str(ROOT/'board/a1.kicad_pcb'),b)
    xy=lambda v:[k.ToMM(v.x),k.ToMM(v.y)]
    pads=[];lines=[];vias=[]
    for f in b.GetFootprints():
        for p in f.Pads():
            r=p.GetBoundingBox();dr=p.GetDrillSize()
            pads.append(dict(ref=f.GetReference(),pin=p.GetNumber(),net=p.GetNetname(),pos=xy(p.GetPosition()),
                box=[k.ToMM(r.GetLeft()),k.ToMM(r.GetTop()),k.ToMM(r.GetRight()),k.ToMM(r.GetBottom())],
                layers=[i for i,l in enumerate([k.F_Cu,k.B_Cu]) if p.IsOnLayer(l)],
                hole=[k.ToMM(dr.x),k.ToMM(dr.y)]))
    for t in b.GetTracks():
        if isinstance(t,k.PCB_VIA):vias.append(dict(net=t.GetNetname(),pos=xy(t.GetPosition()),size=k.ToMM(t.GetWidth(k.F_Cu))))
        else:lines.append(dict(net=t.GetNetname(),a=xy(t.GetStart()),b=xy(t.GetEnd()),width=k.ToMM(t.GetWidth()),layer=0 if t.GetLayer()==k.F_Cu else 1))
    (ROOT/'.local/geometry.json').write_text(json.dumps(dict(pads=pads,lines=lines,vias=vias)))
    print('Prepared four-net repair geometry');sys.stdout.flush();os._exit(0)
def solve():
    import heapq
    import numpy as np
    from PIL import Image, ImageDraw
    d=json.loads((ROOT/'.local/geometry.json').read_text());routes=[];results=[]
    W,H=441,1001
    pt=lambda p:(round(p[0]/GRID),round(p[1]/GRID))
    jobs=[]
    for net in NETS:
        if net=='XO':jobs.extend([(net,('U1','Y1')),(net,('Y1','C13'))])
        else:jobs.append((net,None))
    for net,refs in jobs:
        boards=[];vboards=[]
        for rad,out in [(.075,boards),(.25,vboards)]:
            for layer in [0,1]:
                im=Image.new('L',(W,H),0);dr=ImageDraw.Draw(im)
                margin=math.ceil((.3+rad)/GRID);dr.rectangle((0,0,W-1,H-1),outline=255,width=margin)
                def circle(pos,r):
                    x,y=pt(pos);rr=math.ceil(r/GRID);dr.ellipse((x-rr,y-rr,x+rr,y+rr),fill=255)
                for p in d['pads']:
                    if layer in p['layers'] and p['net']!=net:
                        x1,y1,x2,y2=p['box'];g=rad+.16
                        dr.rectangle((math.floor((x1-g)/GRID),math.floor((y1-g)/GRID),math.ceil((x2+g)/GRID),math.ceil((y2+g)/GRID)),fill=255)
                    if max(p['hole']) and not p['net']:circle(p['pos'],max(p['hole'])/2+.26+rad)
                for t in d['lines']:
                    if t['layer']==layer and t['net']!=net:
                        r=t['width']/2+rad+.16
                        dr.line([pt(t['a']),pt(t['b'])],fill=255,width=math.ceil(2*r/GRID)+1);circle(t['a'],r);circle(t['b'],r)
                for v in d['vias']:
                    if v['net']!=net:circle(v['pos'],v['size']/2+rad+.16)
                out.append(np.asarray(im)>0)
        vblocked=vboards[0]|vboards[1]
        pads=[p for p in d['pads'] if p['net']==net and (refs is None or p['ref'] in refs)]
        assert len(pads)==2,(net,len(pads))
        sx,sy=pt(pads[0]['pos']);gx,gy=pt(pads[1]['pos'])
        start=(0,sx,sy);goal=(0,gx,gy)
        if boards[0][sy,sx] or boards[0][gy,gx]:
            results.append(dict(net=net,result='Endpoint blocked'));continue
        def h(x,y,z):return math.hypot(gx-x,gy-y)+ (0 if z==0 else 25)
        heap=[(h(sx,sy,0),0,start)];cost={start:0};prev={};found=False
        while heap:
            _,g,u=heapq.heappop(heap)
            if g!=cost.get(u):continue
            if u==goal:found=True;break
            z,x,y=u
            for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
                xx=x+dx;yy=y+dy
                if not(0<=xx<W and 0<=yy<H) or boards[z][yy,xx]:continue
                if dx and dy and (boards[z][y,xx] or boards[z][yy,x]):continue
                v=(z,xx,yy);ng=g+(1.41421356237 if dx and dy else 1)
                if ng<cost.get(v,float('inf')):cost[v]=ng;prev[v]=u;heapq.heappush(heap,(ng+h(xx,yy,z),ng,v))
            if not vblocked[y,x]:
                v=(1-z,x,y);ng=g+60
                if ng<cost.get(v,float('inf')):cost[v]=ng;prev[v]=u;heapq.heappush(heap,(ng+h(x,y,1-z),ng,v))
        if not found:results.append(dict(net=net,result='No path',visited=len(cost)));print(results[-1],flush=True);continue
        path=[goal]
        while path[-1]!=start:path.append(prev[path[-1]])
        path.reverse();route=dict(net=net,path=path,start=pads[0]['pos'],end=pads[1]['pos']);routes.append(route)
        for a,b in zip(path,path[1:]):
            za,x,y=a;zb,xx,yy=b
            if za!=zb:d['vias'].append(dict(net=net,pos=[x*GRID,y*GRID],size=.5))
            else:d['lines'].append(dict(net=net,a=[x*GRID,y*GRID],b=[xx*GRID,yy*GRID],width=.15,layer=za))
        results.append(dict(net=net,result='Routed',visited=len(cost),steps=len(path)));print(results[-1],flush=True)
    (ROOT/'.local/local-routes.json').write_text(json.dumps(routes))
    (ROOT/'reports/local_route.json').write_text(json.dumps(results,indent=2))
def apply():
    import pcbnew as k
    b=k.LoadBoard(str(ROOT/'board/a1.kicad_pcb'));vec=lambda p:k.VECTOR2I(k.FromMM(p[0]),k.FromMM(p[1]))
    routes=json.loads((ROOT/'.local/local-routes.json').read_text())
    for r in routes:
        net=b.FindNet(r['net']).GetNetCode();path=r['path'];segments=[]
        for a,c in zip(path,path[1:]):
            z,x,y=a;zz,xx,yy=c
            if z!=zz:
                v=k.PCB_VIA(b);v.SetPosition(vec([x*GRID,y*GRID]));v.SetWidth(k.FromMM(.5));v.SetDrill(k.FromMM(.25));v.SetViaType(k.VIATYPE_THROUGH);v.SetLayerPair(k.F_Cu,k.B_Cu);v.SetNetCode(net);b.Add(v)
            else:
                p=[x*GRID,y*GRID];q=[xx*GRID,yy*GRID]
                if segments and segments[-1][0]==z and segments[-1][2]==p:
                    old=segments[-1];dx=old[2][0]-old[1][0];dy=old[2][1]-old[1][1]
                    if abs(dx*(q[1]-p[1])-dy*(q[0]-p[0]))<1e-8:old[2]=q;continue
                segments.append([z,p,q])
        for z,p,q in [[0,r['start'],[path[0][1]*GRID,path[0][2]*GRID]],*segments,[0,[path[-1][1]*GRID,path[-1][2]*GRID],r['end']]]:
            if p==q:continue
            t=k.PCB_TRACK(b);t.SetStart(vec(p));t.SetEnd(vec(q));t.SetWidth(k.FromMM(.15));t.SetLayer(k.F_Cu if z==0 else k.B_Cu);t.SetNetCode(net);b.Add(t)
    k.SaveBoard(str(ROOT/'board/a1.kicad_pcb'),b);print('Imported',len(routes),'local net repairs');sys.stdout.flush();os._exit(0)
if __name__=='__main__':{'export':export,'solve':solve,'apply':apply}[sys.argv[1]]()
