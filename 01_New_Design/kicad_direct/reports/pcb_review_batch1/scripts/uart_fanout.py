from common import *
fan=json.loads((OUT/'fanouts.json').read_text());log=[]
for key in ['U2.11','U2.13','U2.5']:
 ref,num=key.split('.');a=pad(ref,num);pt=xy(a.GetPosition());old=fan[key];new=[round(2*pt[i]-old[i],6) for i in [0,1]]
 ts=[t for t in list(b.GetTracks()) if not isinstance(t,p.PCB_VIA) and t.GetNetCode()==a.GetNetCode() and min(math.dist(xy(t.GetStart()),pt)+math.dist(xy(t.GetEnd()),old),math.dist(xy(t.GetEnd()),pt)+math.dist(xy(t.GetStart()),old))<.0001];assert len(ts)==1,(key,len(ts));remove(ts[0]);tr(pt,new,a.GetNetname(),w=.15);fan[key]=new;log.append({'pin':key,'old':old,'new':new})
(OUT/'fanouts.json').write_text(json.dumps(fan,indent=2));(OUT/'uart_fanout_adjustments.json').write_text(json.dumps(log,indent=2));save();drc('uart_fanout')
