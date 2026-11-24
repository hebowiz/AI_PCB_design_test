from common import *
fan=json.loads((OUT/'fanouts.json').read_text());log=[]
for key in ['U1.16','U1.43','U1.44','U1.45','U2.10','U2.11','U5.1','U5.2']:
 ref,num=key.split('.');a=pad(ref,num);pt=xy(a.GetPosition());old=fan[key];new=[round(2*pt[i]-old[i],6) for i in [0,1]]
 # Each target is a pad and its single, isolated fanout from this editing session.
 ts=[t for t in list(b.GetTracks()) if not isinstance(t,p.PCB_VIA) and t.GetNetCode()==a.GetNetCode() and {xy(t.GetStart()),xy(t.GetEnd())}=={pt,tuple(old)}]
 assert len(ts)==1,(key,len(ts))
 remove(ts[0]);tr(pt,new,a.GetNetname(),w=.15);fan[key]=new;log.append({'pin':key,'before':old,'after':new})
(OUT/'fanouts.json').write_text(json.dumps(fan,indent=2));(OUT/'inward_fanout_changes.json').write_text(json.dumps(log,indent=2));save();drc('inward')
