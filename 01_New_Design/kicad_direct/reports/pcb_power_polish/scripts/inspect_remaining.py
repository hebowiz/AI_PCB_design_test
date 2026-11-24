from geom import *
for t in b.GetTracks():
 a=xy(t.GetStart());c=xy(t.GetEnd())
 if (t.GetNetname()=='+3V3' and min(a[0],c[0])<108.5 and min(a[1],c[1])>126 and max(a[1],c[1])<128) or (t.GetNetname()=='GND' and min(a[0],c[0])>107 and max(a[0],c[0])<111 and min(a[1],c[1])>135.5 and max(a[1],c[1])<137):print(record(t))
for r in json.loads((OUT/'corner_edits.json').read_text()):
 if 'corner' in r and ((r['net']=='GND' and 135<r['corner'][1]<137) or (r['net']=='+3V3' and r['corner'][0]<105 and r['corner'][1]<112)):print('EDIT',r)
