from common import *
fps['R13'].Move(v(0,-.3))
for t in list(b.GetTracks()):
 if t.GetNetname()=='USB5V' and xy(t.GetStart()) in [(118.49,103),(118.2,103.29),(118.2,104)]:remove(t)
 if uid(t)=='c8820af6-4a09-4b4f-889a-d1a13246a3a0':t.SetStart(v(119.51,102.7))
pts=[(118.49,102.7),(118.1,103.09),(118.1,104.35),(117.6,104.85),(117.35,104.85)]
for a,c in zip(pts,pts[1:]):track(a,c,'USB5V',w=.5)
drc('clearances_final')
