from ground import *
import local_router as lr
orig=lr.masks
def gm(net,width,freepins=(),junctions=()):
 if net=='GND':
  freepins=[f.GetReference()+'.'+p.GetNumber() for f in fps.values() for p in f.Pads() if p.GetNetname()=='GND']
  junctions=list(junctions)+[xy(t.GetStart()) for t in b.GetTracks() if t.GetNetname()=='GND']+[xy(t.GetEnd()) for t in b.GetTracks() if t.GetNetname()=='GND']
 return orig(net,width,freepins,junctions)
lr.masks=gm
(OUT/'ground_repair.json').write_text(json.dumps(stitch_ground(),indent=2))
drc('ground')
