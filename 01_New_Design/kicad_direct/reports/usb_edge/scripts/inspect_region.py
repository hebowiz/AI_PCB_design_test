from common import *
for f in sorted(fps.values(),key=lambda f:f.GetPosition().y):
 if xy(f.GetPosition())[1]<113: print('FP',f.GetReference(),xy(f.GetPosition()),f.GetOrientationDegrees())
for t in b.GetTracks():
 if max(xy(t.GetStart())[1],xy(t.GetEnd())[1])<113:
  print(json.dumps(record(t)))
