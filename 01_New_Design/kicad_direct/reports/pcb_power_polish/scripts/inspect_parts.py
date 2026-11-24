from common import *
for ref,f in sorted(fps.items()):
 if ref.startswith(('C','FB','U')):
  print(ref,f.GetValue(),xy(f.GetPosition()),f.GetOrientationDegrees(),[(p.GetNumber(),p.GetNetname(),xy(p.GetPosition()),xy(p.GetSize())) for p in f.Pads()])
