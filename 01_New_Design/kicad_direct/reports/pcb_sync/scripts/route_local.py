"""Add copper only for DRC-reported missing connections after schematic sync.
Uses the original A-2 local path-finder definitions, never its whole-board driver.
"""
from pathlib import Path
import sys,json,types,pcbnew as p
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'reports/pcb_sync'
report=OUT/'after'/sys.argv[1]
b=p.LoadBoard(str(ROOT/'a2_usb_uart.kicad_pcb'))
for f in b.GetFootprints():
 ref=f.GetReference()
 if ref in ['SW1','SW2','SW3']:
  name='unconnected-('+ref+('-1V8{slash}open-Pad1)' if ref=='SW1' else '-OFF{slash}open-Pad1)')
  net=b.FindNet(name)
  if net is None:net=p.NETINFO_ITEM(b,name);b.Add(net)
  next(a for a in f.Pads() if a.GetNumber()=='1').SetNet(net)
# Only function definitions and obstacle setup before the original router's main guard.
source=(ROOT/'scripts/route.py').read_text(encoding='utf-8').split("if __name__ == '__main__':")[0]
source=source.replace('from design import ROOT','')
import __main__
__main__.ROUTER_BOARD=b
sys.argv=['local-routing','--continue-existing']
r=types.ModuleType('local_router');r.ROOT=ROOT
exec(compile(source,str(ROOT/'scripts/route.py'),'exec'),r.__dict__)
d=json.loads(report.read_text(encoding='utf8'));log=[]
lookup={t.m_Uuid.AsString():t for t in b.GetTracks()};lookup.update({a.m_Uuid.AsString():a for f in b.GetFootprints() for a in f.Pads()})
for index,v in enumerate(d['unconnected_items']):
 if len(v['items'])!=2:continue
 ia,ic=[lookup.get(q['uuid']) for q in v['items']]
 if ia is None or ic is None:continue
 net=ia.GetNetCode();assert net==ic.GetNetCode()
 ax,ay=r.xy(ia.GetPosition() if isinstance(ia,p.PAD) else ia.GetStart());cx,cy=r.xy(ic.GetPosition() if isinstance(ic,p.PAD) else ic.GetStart())
 az=0 if ia.IsOnLayer(p.F_Cu) else 1;cz=0 if ic.IsOnLayer(p.F_Cu) else 1
 mask,vm=r.obstacles(net)
 start=r.node(ax,ay,az);goal=r.node(cx,cy,cz)
 path,vis=r.astar(start,[goal],mask,vm,maxvisit=300000)
 result={'index':index,'net':ia.GetNetname(),'from':v['items'][0],'to':v['items'][1],'visited':vis,'success':bool(path)}
 if path:
  r.savepath(path,net);r.track((ax,ay),r.coord(path[0])[:2],az,net);r.track((cx,cy),r.coord(path[-1])[:2],cz,net)
 print(json.dumps({k:v for k,v in result.items() if k not in ['from','to']}),flush=True);log.append(result)
 p.SaveBoard(str(ROOT/'a2_usb_uart.kicad_pcb'),b)
(OUT/'after'/('routing_'+report.stem+'.json')).write_text(json.dumps(log,indent=2,ensure_ascii=False),encoding='utf8')
p.SaveBoard(str(ROOT/'a2_usb_uart.kicad_pcb'),b)
