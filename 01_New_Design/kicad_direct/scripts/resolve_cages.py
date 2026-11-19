"""Re-route two generated nets that boxed in three FT232H pads."""
import sys,json
sys.argv=['repair','--continue-existing']
import route as r
p=r.p
ROOT=r.ROOT
padmap={(f.GetReference(),pad.GetNumber()):pad for f in r.b.GetFootprints() for pad in f.Pads()}
jobs=[(('U1','5'),('R1','1')),(('U1','3'),('FB1','2')),
      (('FB1','2'),('C11','1')),(('C11','1'),('C9','1')),
      (('U1','1'),('Y1','1')),(('Y1','1'),('C13','1'))]
result=[]
for aa,cc in jobs:
    a=padmap[aa];c=padmap[cc];net=a.GetNetCode();ax,ay=r.xy(a.GetPosition());cx,cy=r.xy(c.GetPosition())
    mask,vm=r.obstacles(net);path,vis=r.astar(r.node(ax,ay),[r.node(cx,cy)],mask,vm,maxvisit=850000)
    entry={'net':a.GetNetname(),'from':aa,'to':cc,'visited':vis,'success':bool(path)}
    if path:
        r.savepath(path,net);r.track((ax,ay),r.coord(path[0])[:2],0,net);r.track((cx,cy),r.coord(path[-1])[:2],0,net)
    result.append(entry);print(entry,flush=True)
    p.SaveBoard(str(ROOT/'a2_usb_uart.kicad_pcb'),r.b)
(ROOT/'reports/routing_cage_repairs.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
