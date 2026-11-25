from common import *
track(xy(pad('U2',3).GetPosition()),(109.35,128.025),'GND',w=.2)
track(xy(pad('U2',9).GetPosition()),(112.65,131.275),'GND',w=.2)
for r,p in {'U4':(104.6,128.9),'R17':(104.7,133.3),'C19':(108.4,134.2)}.items():fps[r].Reference().SetPosition(v(*p));fps[r].Reference().SetTextSize(v(.55,.55))
drc('gnd_stubs')
