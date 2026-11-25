from common import *
ids={'6217b76d-2053-4f7f-b993-e286f254461b','e21c575b-8e60-457b-a01f-c99d8ffec5a4','f1d24d5b-8196-472b-8e91-e7b5fef1864e','854ad0dd-6682-4c3b-b613-be2b1558fb10'}
for t in list(b.GetTracks()):
 if uid(t) in ids:remove(t)
pts=[(107.5,105.35),(107.5,104.15),(107.65,104),(108.2,104),(108.95,104.75)]
for a,c in zip(pts,pts[1:]):track(a,c,'USB5V',w=.5)
drc('final_candidate')
