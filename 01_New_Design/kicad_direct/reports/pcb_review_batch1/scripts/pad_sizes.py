from common import *
for ref in ['C12','C23','C8','C7','C2']:
 for a in fps[ref].Pads():print(ref,a.GetNumber(),xy(a.GetPosition()),xy(a.GetSize()),a.GetOrientationDegrees())
