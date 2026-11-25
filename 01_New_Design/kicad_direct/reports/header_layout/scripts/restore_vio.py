from common import *
ids=['ff8ac4ed-aa1b-4c24-9ab8-a856c7ace0ef','fa7cd2e2-c7f9-44a4-ac05-c4c76e247cfd','4beecd6a-c5ed-415e-bca6-20b859296485','6f607523-c4cd-447f-a0e8-e9309ae85f60']
for r in json.loads((OUT/'new_routes.json').read_text()):
 if r['uuid'] in ids:track(r['a'],r['b'],r['net'],r['layer'],r['width'])
for r,p in {'U4':(104.6,129.4),'R17':(104.7,133.0),'C19':(108,132.1)}.items():fps[r].Reference().SetPosition(v(*p));fps[r].Reference().SetTextSize(v(.6,.6))
save();drc('restore')
