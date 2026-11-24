from geom import *
assert hashlib.sha256(BOARD.read_bytes()).hexdigest()=='3050da346a6d76e879fd3505c282a47a194f6da79f6527ffc4a8f0e8ac686526'
changes=[]
def move(ref,x,y,ang):
 f=fps[ref];changes.append({'ref':ref,'before':{'at':xy(f.GetPosition()),'angle':f.GetOrientationDegrees()},'after':{'at':[x,y],'angle':ang}});f.SetOrientationDegrees(ang);f.SetPosition(v(x,y))
def path(qs,net,w=.3,z=k.F_Cu):
 for a,c in zip(qs,qs[1:]):track(a,c,net,z,w)
removed=[]
for t in list(b.GetTracks()):
 rec=record(t);a=xy(t.GetStart());c=xy(t.GetEnd())
 take=t.GetNetname()=='VPLL'
 take|=t.GetNetname()=='/REF12K' and t.GetLayer()==k.F_Cu and max(a[1],c[1])<108.2 and min(a[0],c[0])<107
 take|=t.GetNetname()=='+3V3' and max(a[0],c[0])<109 and max(a[1],c[1])<=111.8375
 take|=uid(t) in ['42ce39e8-a731-44bf-ad8b-d7e87231fbdc','5fb032b2-819f-4a82-8a81-e781936cf89e','fe7e31c0-79ec-45f3-90e7-15a02effb3c0','84af11de-9488-4aff-995a-cd00db71d8b8','6d71f4de-2b59-4e71-9e27-1b9840517b74','b47028ce-7631-467c-bd29-7a963c8741fe','162e20fd-a920-4da4-b672-d699d76d0d4c','36a68bc1-0a08-4b52-9f83-cc685afebd86']
 if take:removed.append(rec);remove(t)
move('FB2',105,108.6,0);move('C12',107.65,108.5,90);move('C10',109.5,109.7,90);move('C3',106.0,110.4,90)
path([xy(pad('FB2',2).GetPosition()),(106.5,108.6),(107.35,109.45),xy(pad('C12',1).GetPosition())],'VPLL',.3)
path([xy(pad('C12',1).GetPosition()),(107.65,109.7),(108.13,110.18),xy(pad('C10',1).GetPosition())],'VPLL',.3)
path([xy(pad('C10',1).GetPosition()),(109.95,110.18),(110.25,110.48),xy(pad('U1',8).GetPosition())],'VPLL',.15)
path([(103.45,111.55),(103.45,110.5),(104.515,109.435),xy(pad('FB2',1).GetPosition())],'+3V3',.25)
path([(103.45,111.55),(103.45,111.1),(103.67,110.88),xy(pad('C3',1).GetPosition())],'+3V3',.25)
path([xy(pad('C3',1).GetPosition()),(108.25,110.88),xy(pad('U1',12).GetPosition())],'+3V3',.15)
for ref,viaq in [('C12',(107.65,106.5)),('C10',(109.5,108.35)),('C3',(105.1,109.92))]:
 path([xy(pad(ref,2).GetPosition()),viaq],'GND',.3);via(viaq,'GND')
move('R1',104.2,107,0)
path([xy(pad('R1',1).GetPosition()),(103.75,107.6),(104.1,107.95),(106.35,107.95)],'/REF12K',.15)
path([xy(pad('R1',2).GetPosition()),(105.5,107)],'GND',.25);via((105.5,107),'GND')
path([xy(pad('D5',2).GetPosition()),(109.3,107),(108.8,106.5)],'GND',.15);via((108.8,106.5),'GND')
via((106.35,107.95),'/REF12K')
(OUT/'pll_placement.json').write_text(json.dumps(changes,indent=2));(OUT/'pll_removed.json').write_text(json.dumps(removed,indent=2));drc('pll_trial3')
