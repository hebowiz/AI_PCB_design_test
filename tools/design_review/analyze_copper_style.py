"""Read-only KiCad copper/route style investigation; findings are review candidates.
KiCad Python + shapely/networkx/Pillow. Never saves or refills the source PCB.
"""
import argparse, collections, hashlib, json, math, sys
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--board',required=True,type=Path)
    ap.add_argument('--out',required=True,type=Path)
    ap.add_argument('--packages',type=Path)
    args=ap.parse_args()
    if args.packages: sys.path.insert(0,str(args.packages))
    import pcbnew as k
    import shapely
    import networkx as nx
    from shapely.geometry import Point,LineString,Polygon,box
    from shapely.geometry.polygon import orient
    from shapely.ops import unary_union
    from PIL import Image,ImageDraw,ImageFont
    args.out.mkdir(parents=True,exist_ok=True)
    initial=hashlib.sha256(args.board.read_bytes()).hexdigest()
    b=k.LoadBoard(str(args.board));tracks=[];vias=[];pads=[];zones=[]
    xy=lambda q:(round(k.ToMM(q.x),6),round(k.ToMM(q.y),6))
    uid=lambda q:q.m_Uuid.AsString()
    layers=[k.F_Cu,k.B_Cu];ln={k.F_Cu:'F.Cu',k.B_Cu:'B.Cu'}
    def polys(g):
        if g.is_empty:return []
        if g.geom_type=='Polygon':return [g]
        return [p for c in getattr(g,'geoms',[]) for p in polys(c)]
    def ring(r):return [xy(r.CPoint(i)) for i in range(r.PointCount())]
    def fromset(s):
        res=[]
        for i in range(s.OutlineCount()):
            p=Polygon(ring(s.COutline(i)),[ring(s.CHole(i,j)) for j in range(s.HoleCount(i))])
            res.append(p if p.is_valid else p.buffer(0))
        return unary_union(res)
    for t in b.GetTracks():
        if isinstance(t,k.PCB_ARC):raise ValueError('Arc tracks require an arc-aware analyzer; not approximated as chords.')
        r={'uuid':uid(t),'net':t.GetNetname(),'at':xy(t.GetStart())}
        if isinstance(t,k.PCB_VIA):
            r.update(diameter=k.ToMM(t.GetWidth(k.F_Cu)),drill=k.ToMM(t.GetDrillValue()))
            r['g']=Point(r['at']).buffer(r['diameter']/2);vias.append(r)
        else:
            r.update(end=xy(t.GetEnd()),layer=t.GetLayer(),width=k.ToMM(t.GetWidth()),length=k.ToMM(t.GetLength()))
            r['line']=LineString([r['at'],r['end']]);r['g']=r['line'].buffer(r['width']/2,quad_segs=16);tracks.append(r)
    for f in b.GetFootprints():
        for p in f.Pads():
            for layer in layers:
                if not p.IsOnLayer(layer):continue
                s=k.SHAPE_POLY_SET();p.TransformShapeToPolygon(s,layer,0,k.FromMM(.001),k.ERROR_OUTSIDE)
                pads.append({'uuid':uid(p),'pin':f.GetReference()+'.'+p.GetNumber(),'net':p.GetNetname(),'at':xy(p.GetPosition()),'layer':layer,'g':fromset(s)})
    for z in b.Zones():
        if z.GetIsRuleArea():continue
        for layer in layers:
            if not z.IsOnLayer(layer):continue
            zones.append({'uuid':uid(z),'net':z.GetNetname(),'layer':layer,'g':fromset(z.GetFilledPolysList(layer))})
    plain=lambda r:{a:c for a,c in r.items() if a not in ('g','line')}
    nearpins=lambda p:[q['pin'] for q in sorted(pads,key=lambda q:Point(p).distance(q['g']))[:4]]
    # Split centerlines at true intersections; terminal coverage uses real pad/via copper.
    branches=[];turns=[];pseudo=[];via_rows=[];excursions=[]
    nets=sorted({t['net'] for t in tracks}|{v['net'] for v in vias})
    for net in nets:
        nt=[t for t in tracks if t['net']==net];nv=[v for v in vias if v['net']==net]
        via_rows.append({'net':net,'count':len(nv),'uuids':[v['uuid'] for v in nv], 'positions':[v['at'] for v in nv], 'ground_exempt':net=='GND','track_length_mm':round(sum(t['length'] for t in nt),6)})
        for layer in layers:
            ts=[t for t in nt if t['layer']==layer]
            if not ts:continue
            geom=unary_union([t['line'] for t in ts]);lines=[geom] if geom.geom_type=='LineString' else list(geom.geoms)
            G=nx.Graph()
            for line in lines:
                for a,c in zip(list(line.coords),list(line.coords)[1:]):
                    a=tuple(round(x,5) for x in a);c=tuple(round(x,5) for x in c)
                    if a==c:continue
                    mid=Point(( (a[0]+c[0])/2,(a[1]+c[1])/2))
                    sources=[t for t in ts if t['line'].distance(mid)<.00002]
                    G.add_edge(a,c,length=math.dist(a,c),width=max(t['width'] for t in sources),uuids=[t['uuid'] for t in sources])
            term=unary_union([p['g'] for p in pads if p['net']==net and p['layer']==layer]+[v['g'] for v in nv])
            for n in G:
                neighbors=list(G[n]);terminal=term.distance(Point(n))<.005
                if len(neighbors)>=3:
                    branches.append({'net':net,'layer':ln[layer],'at':n,'degree':len(neighbors),'at_pad_or_via':terminal,'uuids':sorted({i for v in neighbors for i in G[n][v]['uuids']})})
                if len(neighbors)!=2 or terminal:continue
                a,c=neighbors;u=(n[0]-a[0],n[1]-a[1]);v=(c[0]-n[0],c[1]-n[1])
                angle=math.degrees(math.atan2(u[0]*v[1]-u[1]*v[0],u[0]*v[0]+u[1]*v[1]))
                if abs(angle)>1:
                    turns.append({'net':net,'layer':ln[layer],'at':n,'angle_deg':round(abs(angle),3),'uuids':sorted(set(G[n][a]['uuids']+G[n][c]['uuids']))})
            # Two same-sign 45-degree turns separated by a short link: sensitivity is reported.
            for a,c,d in G.edges(data=True):
                if G.degree(a)!=2 or G.degree(c)!=2 or term.distance(Point(a))<.005 or term.distance(Point(c))<.005:continue
                aa=next(v for v in G[a] if v!=c);cc=next(v for v in G[c] if v!=a)
                def turn(x,y,z):
                    u=(y[0]-x[0],y[1]-x[1]);v=(z[0]-y[0],z[1]-y[1]);return math.degrees(math.atan2(u[0]*v[1]-u[1]*v[0],u[0]*v[0]+u[1]*v[1]))
                t1,t2=turn(aa,a,c),turn(a,c,cc)
                if abs(abs(t1)-45)<.2 and abs(abs(t2)-45)<.2 and t1*t2>0 and d['length']<=max(1.0,2*d['width']):
                    pseudo.append({'net':net,'layer':ln[layer],'at':a,'end':c,'middle_length_mm':round(d['length'],6),'width_mm':d['width'],'length_width_ratio':round(d['length']/d['width'],3),'within_proposed_limit':d['length']<=max(.5,2*d['width']),'uuids':sorted(set(G[a][aa]['uuids']+d['uuids']+G[c][cc]['uuids'])),'near_pins':nearpins(a)})
            # Via-to-via back-layer components: geometric screening, no rerouting.
            if layer==k.B_Cu and net!='GND':
                for component in nx.connected_components(G):
                    sub=G.subgraph(component)
                    touched=[]
                    for v in nv:
                        nodes=[n for n in sub if Point(n).distance(v['g'])<.005]
                        if nodes:touched.append((v,min(nodes,key=lambda n:math.dist(n,v['at']))))
                    if len(touched)!=2:continue
                    (va,na),(vc,nc)=touched
                    if any(p['layer']==layer and p['net']==net and any(p['g'].distance(Point(n))<.005 for n in sub) for p in pads):continue
                    if not all(any(t['layer']==k.F_Cu and t['g'].distance(v['g'])<.005 for t in nt) for v in (va,vc)):continue
                    length=nx.shortest_path_length(sub,na,nc,weight='length')
                    length += math.dist(na,va['at'])+math.dist(nc,vc['at'])
                    width=min(t['width'] for t in ts)
                    direct=LineString([va['at'],vc['at']]).buffer(width/2+.127)
                    obstacles=[t['uuid'] for t in tracks if t['layer']==k.F_Cu and t['net']!=net and t['g'].intersects(direct)]
                    obstacles += [v['uuid'] for v in vias if v['net']!=net and v['g'].intersects(direct)]
                    obstacles += [p['pin'] for p in pads if p['layer']==k.F_Cu and p['net']!=net and p['g'].intersects(direct)]
                    excursions.append({'net':net,'via_uuids':[va['uuid'],vc['uuid']],'positions':[va['at'],vc['at']],'back_path_estimate_mm':round(length,6),'direct_mm':round(math.dist(va['at'],vc['at']),6),'screen_width_mm':width,'screen_clearance_mm':.127,'front_direct_obstacles':sorted(set(obstacles)),'protected_usb':net.startswith('/USB_D'),'note':'Path estimate includes radial contact offsets; opposite-layer zone copper and routing rules are not part of this straight-line feasibility screen; no removal is authorized.'})
    # Compare routing copper and actual saved filled copper (zones included).
    coppers={};routed={};acute=[]
    for layer in layers:
        for net in sorted(set(nets)|{z['net'] for z in zones}):
            objects=[t['g'] for t in tracks if t['net']==net and t['layer']==layer]+[v['g'] for v in vias if v['net']==net]+[p['g'] for p in pads if p['net']==net and p['layer']==layer]
            routed[(layer,net)]=unary_union(objects)
            coppers[(layer,net)]=unary_union(objects+[z['g'] for z in zones if z['net']==net and z['layer']==layer])
        for net in sorted(nets):
            for kind,geom in [('route_and_pad',routed[(layer,net)]),('saved_copper',coppers[(layer,net)])]:
                for p in polys(geom.simplify(.003,preserve_topology=True)):
                    p=orient(p,sign=1)
                    for rr in [p.exterior,*p.interiors]:
                        cs=list(rr.coords)[:-1]
                        for j,c in enumerate(cs):
                            a=cs[j-1];e=cs[(j+1)%len(cs)];la=math.dist(a,c);lb=math.dist(c,e)
                            if min(la,lb)<.02:continue
                            u=(c[0]-a[0],c[1]-a[1]);v=(e[0]-c[0],e[1]-c[1]);ta=math.degrees(math.atan2(u[0]*v[1]-u[1]*v[0],u[0]*v[0]+u[1]*v[1]));inner=180-ta
                            if inner<89.9 or inner>270.1:
                                acute.append({'net':net,'layer':ln[layer],'scope':kind,'at':[round(q,5) for q in c],'copper_interior_deg':round(inner,3),'type':'copper_tip' if inner<90 else 'acute_void_notch','edge_lengths_mm':[round(la,5),round(lb,5)],'near_pins':nearpins(c)})
    # Morphological opening highlights <1mm features. It is not a local-width proof.
    ground=[];narrow=[];islands=[];ng_id=0
    for layer in layers:
        g=coppers.get((layer,'GND'),Polygon())
        zone=unary_union([z['g'] for z in zones if z['layer']==layer and z['net']=='GND'])
        opened=zone.buffer(-.5,quad_segs=16).buffer(.5,quad_segs=16).intersection(zone)
        residual=zone.difference(opened.buffer(.01))
        core_parts=polys(zone.buffer(-.5,quad_segs=16))
        ground.append({'layer':ln[layer],'saved_zone_area_mm2':round(zone.area,6),'saved_zone_components':len(polys(zone)),'ground_copper_components':len(polys(g)),'one_mm_core_components':len(core_parts),'residual_area_mm2':round(residual.area,6)})
        for p in polys(g):
            if p.area>.002:
                contacts=[x['pin'] for x in pads if x['net']=='GND' and x['layer']==layer and x['g'].intersects(p)]
                vs=[x['uuid'] for x in vias if x['net']=='GND' and x['g'].intersects(p)]
                if not contacts and not vs:islands.append({'layer':ln[layer],'area_mm2':p.area,'bounds':p.bounds})
        for part in polys(residual):
            if part.area<.02:continue
            # Remove isolated numerical crumbs; keep rounded corners as candidates with explicit labels.
            gp=[x for x in pads if x['net']=='GND' and x['layer']==layer and x['g'].distance(part)<.02]
            vv=[x for x in vias if x['net']=='GND' and x['g'].distance(part)<.02]
            ng_id+=1;center=part.representative_point().coords[0]
            widths={}
            for axis,cut in [('horizontal',LineString([(center[0]-100,center[1]),(center[0]+100,center[1])])),('vertical',LineString([(center[0],center[1]-100),(center[0],center[1]+100)]))]:
                section=zone.intersection(cut);segments=[section] if section.geom_type=='LineString' else list(getattr(section,'geoms',[]));hit=[seg.length for seg in segments if seg.distance(Point(center))<.000001];widths[axis]=round(min(hit),6) if hit else None
            narrow.append({'id':ng_id,'layer':ln[layer],'area_mm2':round(part.area,6),'bounds':[round(q,5) for q in part.bounds],'at':list(center),'section_width_mm':widths,'core_contact_regions':len(polys(part.buffer(.03).intersection(opened))),'ground_pads':[x['pin'] for x in gp],'ground_vias':[x['uuid'] for x in vv],'near_pins':nearpins(center),'classification':'terminal_or_thermal_candidate' if gp or vv else 'no_direct_terminal_candidate','g':part})
    mid=[x for x in branches if not x['at_pad_or_via']]
    summary={'footprints':len(list(b.GetFootprints())),'tracks':len(tracks),'vias':len(vias),'ground_vias':sum(v['net']=='GND' for v in vias),'signal_power_vias':sum(v['net']!='GND' for v in vias),'mid_track_branches':len(mid),'terminal_branches':len(branches)-len(mid),'turns_ge90_outside_terminals':sum(t['angle_deg']>=89.9 for t in turns),'pseudo_right_angle_candidates':sum(p['within_proposed_limit'] for p in pseudo),'pseudo_sensitivity_lengths_mm':{str(th):sum(p['middle_length_mm']<=th for p in pseudo) for th in [.25,.5,1.]},'acute_counts':dict(collections.Counter(x['scope']+':'+x['type'] for x in acute)),'narrow_regions_candidates':len(narrow),'narrow_without_direct_terminal_candidates':sum(x['classification']=='no_direct_terminal_candidate' for x in narrow),'ground_no_terminal_islands':len(islands),'two_via_back_excursions':len(excursions),'front_direct_clear_excursions':sum(not x['front_direct_obstacles'] and not x['protected_usb'] for x in excursions)}
    result={'schema_version':1,'board_sha256':initial,'tools':{'kicad':k.Version(),'shapely':shapely.__version__,'networkx':nx.__version__},'method':{'centerlines':'Same-net same-layer noding; pad/via-covered nodes classified separately. Finite-width-only contacts not counted as centerline branches.','acute':'Union of track/pad/via copper, and saved filled zones; simplify 0.003mm, incident edges >=0.02mm, angle tolerance 0.1deg. Copper tips <90deg distinguished from reentrant copper >270deg (void angle <90deg).','pseudo':'Two consecutive same-sign 45deg turns, no intermediate pad/via/branch, middle <= max(0.5mm,2*width); proposed screening threshold only.','ground':'Saved zone morphological opening with radius0.5mm, residual outside 0.01mm buffer, components >=0.02mm2. Rounded corners/thermal spokes also detected: visual assessment required. No medial-axis local-width guarantee.','vias':'Count by net; necessity requires route and return-path review; GND exempt.','status':'Investigation only; not a validated design rule or automatic violation count.'},'summary':summary,'branches':branches,'turns':turns,'pseudo_right_angles':pseudo,'via_by_net':via_rows,'via_details':[plain(v) for v in vias],'back_layer_excursions':excursions,'acute_copper':acute,'zone_thermal_settings':[{'net':z.GetNetname(),'layer':ln[z.GetLayer()],'spoke_mm':k.ToMM(z.GetThermalReliefSpokeWidth()),'gap_mm':k.ToMM(z.GetThermalReliefGap())} for z in b.Zones() if not z.GetIsRuleArea() and z.GetLayer() in layers],'ground_layers':ground,'narrow_ground':[plain(n) for n in narrow],'ground_no_terminal_islands':islands}
    assert initial==hashlib.sha256(args.board.read_bytes()).hexdigest()
    (args.out/'metrics.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    # Direct geometry plots show saved fill; drill holes are drawn over copper for clarity.
    fontpath='C:/Windows/Fonts/arial.ttf'
    def render(layer,bounds,width,title,markers=()):
        scale=width/(bounds[2]-bounds[0]);head=48;im=Image.new('RGB',(width,round((bounds[3]-bounds[1])*scale)+head),(23,28,34));d=ImageDraw.Draw(im)
        cv=lambda q:((q[0]-bounds[0])*scale,head+(q[1]-bounds[1])*scale)
        def drawgeom(g,color):
            for p in polys(g.intersection(box(*bounds))):
                d.polygon([cv(q) for q in p.exterior.coords],fill=color)
                for h in p.interiors:d.polygon([cv(q) for q in h.coords],fill=(23,28,34))
        for z in zones:
            if z['layer']==layer:drawgeom(z['g'],(73,49,48) if layer==k.F_Cu else (36,48,79))
        for t in tracks:
            if t['layer']==layer:drawgeom(t['g'],(218,92,78) if layer==k.F_Cu else (85,125,232))
        for p in pads:
            if p['layer']==layer:drawgeom(p['g'],(180,151,91))
        for v in vias:
            if not box(*bounds).intersects(v['g']):continue
            drawgeom(v['g'],(206,169,79));x,y=cv(v['at']);rad=v['drill']/2*scale;d.ellipse((x-rad,y-rad,x+rad,y+rad),fill=(23,28,34))
        font=ImageFont.truetype(fontpath,16)
        if bounds[2]-bounds[0]<15:
            for p in pads:
                if p['layer']==layer and box(*bounds).contains(Point(p['at'])):d.text(cv(p['at']),p['pin'],font=font,fill='white',anchor='mm',stroke_width=1,stroke_fill='black')
        for label,q in markers:
            x,y=cv(q);d.ellipse((x-8,y-8,x+8,y+8),outline=(100,255,130),width=3);d.text((x+10,y-15),label,font=font,fill=(130,255,155))
        # Actual rectangular Edge.Cuts extents used for this board; no outline change.
        for ed in b.GetDrawings():
            if ed.GetLayer()==k.Edge_Cuts:d.line([cv(xy(ed.GetStart())),cv(xy(ed.GetEnd()))],fill=(240,240,240),width=2)
        d.rectangle((0,0,width,head),fill=(12,16,20));d.text((12,12),title,font=ImageFont.truetype(fontpath,21),fill='white')
        d.text((12,head+4),f'X {bounds[0]:.2f}..{bounds[2]:.2f}  Y {bounds[1]:.2f}..{bounds[3]:.2f} mm',font=font,fill='white')
        return im
    render(k.F_Cu,(99.5,99.5,122.5,150.5),1150,'F.Cu - saved copper (top view)').save(args.out/'pcb_front.png')
    render(k.B_Cu,(99.5,99.5,122.5,150.5),1150,'B.Cu - saved copper (top projection)').save(args.out/'pcb_back.png')
    # Representative selection remains recorded, so reviewed crop coordinates are reproducible.
    scenes=[]
    aa=[x for x in acute if x['scope']=='saved_copper' and x['type']=='acute_void_notch' and x['net']!='GND']
    for title,items in [('Acute notch',aa),('Short 45deg link',[x for x in pseudo if x['within_proposed_limit']]),('Mid-track branch',mid),('GND no-terminal region',sorted([x for x in narrow if not x['ground_pads'] and not x['ground_vias'] and x['core_contact_regions']==1],key=lambda x:-x['area_mm2']))]:
        for i,item in enumerate(items[:2]):
            q=item['at'];layer=k.F_Cu if item['layer']=='F.Cu' else k.B_Cu;bounds=(q[0]-2.4,q[1]-2.4,q[0]+2.4,q[1]+2.4)
            if title.startswith('GND'):
                bb=item['bounds'];mx=(bb[0]+bb[2])/2;my=(bb[1]+bb[3])/2;half=max(bb[2]-bb[0],bb[3]-bb[1])/2+.4;bounds=(mx-half,my-half,mx+half,my+half)
            scenes.append((title+' '+str(i+1)+' '+item['layer']+' '+item.get('net','GND'),layer,bounds,q))
    pick=next((x for x in pseudo if x['net']=='/FT_TXD' and x['within_proposed_limit']),None)
    if pick:
        q=pick['at'];scenes.append(('U2.4 short-link /FT_TXD',k.F_Cu,(q[0]-2.4,q[1]-2.4,q[0]+2.4,q[1]+2.4),q))
    pick=next((x for x in excursions if x['net']=='/EE_CS'),None)
    if pick:
        a,c=pick['positions'];q=((a[0]+c[0])/2,(a[1]+c[1])/2);scenes.append(('Via excursion /EE_CS B.Cu',k.B_Cu,(q[0]-2.4,q[1]-2.4,q[0]+2.4,q[1]+2.4),q))
    for item in [x for x in excursions if not x['front_direct_obstacles'] and not x['protected_usb']][:2]:
        a,c=item['positions'];q=((a[0]+c[0])/2,(a[1]+c[1])/2);scenes.append(('Via reduction '+item['net']+' F.Cu',k.F_Cu,(q[0]-2.4,q[1]-2.4,q[0]+2.4,q[1]+2.4),q))
    panels=[render(layer,bounds,740,title,[('candidate',q)]) for title,layer,bounds,q in scenes]
    if panels:
        h=max(x.height for x in panels);out=Image.new('RGB',(1480,h*math.ceil(len(panels)/2)),(255,255,255))
        for i,im in enumerate(panels):out.paste(im,((i%2)*740,(i//2)*h))
        out.save(args.out/'details.png')
    result['detail_crops']=[{'title':a,'layer':ln[l],'bounds':bb,'at':q} for a,l,bb,q in scenes]
    (args.out/'metrics.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
