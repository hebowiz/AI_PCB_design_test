from pathlib import Path
import sys,runpy,contextlib,io,json,math
OUT=Path(__file__).resolve().parents[1];rows=[];pairs=[('VPLL','C12.1','C10.1'),('VPHY','C11.1','C9.1'),('USB5V','C1.1','C23.1'),('VIO','U4.5','C19.1')]
for stage,board in [('before',OUT/'before/a2_usb_uart.kicad_pcb'),('after',OUT/'candidate/a2_usb_uart.kicad_pcb')]:
 sys.argv=['quality_audit.py',str(board),str(OUT/stage/'analysis')]
 with contextlib.redirect_stdout(io.StringIO()):d=runpy.run_path(str(OUT/'scripts/quality_audit.py'))
 nx=d['nx'];graphs=d['graphs'];fps={f.GetReference():f for f in d['fps']};k=d['k'];xy=d['xy']
 for net,a,c in pairs:
  G=graphs[net];pn={p:n for n,z in G.nodes(data=True) for p in z['pins']};pa=nx.shortest_path(G,pn[a],pn[c],weight='length');l=sum(G[n][m]['length'] for n,m in zip(pa,pa[1:]));rows.append({'stage':stage,'from':a,'to':c,'copper_graph_length_excluding_pad_mm':round(l,4)})
 for ref in ['C1','C2','C11','C12','C18','C19']:
  p=next(p for p in fps[ref].Pads() if p.GetNetname()=='GND');pos=xy(p.GetPosition());vs=[t for t in d['b'].GetTracks() if isinstance(t,k.PCB_VIA) and t.GetNetname()=='GND'];vv=min(vs,key=lambda t:math.dist(pos,xy(t.GetPosition())));rows.append({'stage':stage,'ground_pin':ref+'.'+p.GetNumber(),'nearest_ground_via_mm':round(math.dist(pos,xy(vv.GetPosition())),4),'via':xy(vv.GetPosition()),'metric':'pad center to via center, not extracted inductance or routed length'})
(OUT/'capacitor_metrics.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
