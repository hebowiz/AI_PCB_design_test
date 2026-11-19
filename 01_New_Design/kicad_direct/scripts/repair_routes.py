"""Route KiCad-reported missing connections; keep all existing copper."""
import sys,json,math
sys.argv=['repair','--continue-existing']
import route as r

report=json.loads((r.ROOT/'reports/drc_routed2.json').read_text(encoding='utf-8'))
results=[]
for v in report['unconnected_items']:
 a,c=v['items'];ax=a['pos']['x']-100;ay=a['pos']['y']-100;cx=c['pos']['x']-100;cy=c['pos']['y']-100
 # Get the original net code from the actual board item, not translated text.
 lookup={t.m_Uuid.AsString():t for t in r.b.GetTracks()}
 lookup.update({p.m_Uuid.AsString():p for f in r.b.GetFootprints() for p in f.Pads()})
 ia=lookup[a['uuid']];ic=lookup[c['uuid']];net=ia.GetNetCode()
 az=0 if ia.GetLayer()==r.p.F_Cu else 1;cz=0 if ic.GetLayer()==r.p.F_Cu else 1
 mask,vm=r.obstacles(net)
 path,vis=r.astar(r.node(ax,ay,az),[r.node(cx,cy,cz)],mask,vm,maxvisit=700000)
 result={'net':r.b.FindNet(net).GetNetname(),'visited':vis,'success':bool(path)}
 if path:
  r.savepath(path,net);r.track((ax,ay),r.coord(path[0])[:2],az,net);r.track((cx,cy),r.coord(path[-1])[:2],cz,net)
 results.append(result);print(result,flush=True)
 r.p.SaveBoard(str(r.ROOT/'a2_usb_uart.kicad_pcb'),r.b)
(r.ROOT/'reports/routing_repairs.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
