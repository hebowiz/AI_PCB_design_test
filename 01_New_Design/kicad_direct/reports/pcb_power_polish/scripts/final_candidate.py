from common import *
f=fps['C14'].Reference();f.SetTextSize(v(.6,.6));f.SetTextThickness(k.FromMM(.1))
fps['D5'].Reference().SetPosition(v(109.4,107.8))
drc('final_candidate')
