from common import *
rs=json.loads((OUT/'vio_shortcut_result.json').read_text());ids={r['uuid'] for r in rs['new'] if not r['via']};log=[]
for t in b.GetTracks():
 if uid(t) not in ids:continue
 initial=k.ToMM(t.GetWidth())
 for w in [.3,.25,.2]:
  t.SetWidth(k.FromMM(w));save();p=OUT/'checks/width_trial.json';subprocess.run([str(CLI),'pcb','drc','--format','json','--severity-all','-o',str(p),str(BOARD)],stdout=subprocess.DEVNULL,check=True);r=json.loads(p.read_text())
  if not r['violations'] and not r['unconnected_items']:break
  t.SetWidth(k.FromMM(initial))
 log.append(record(t));print('width',uid(t),k.ToMM(t.GetWidth()),flush=True)
(OUT/'vio_widths.json').write_text(json.dumps(log,indent=2));save()
for ref,y in [('R7',132.4),('R8',133.85)]:
 f=fps[ref].Reference();f.SetPosition(v(109.7,y));f.SetTextAngle(k.EDA_ANGLE(90,k.DEGREES_T));f.SetTextSize(v(.6,.6))
drc('widths_labels')
