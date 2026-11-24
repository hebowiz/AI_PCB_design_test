from geom import *
from shapely.geometry import box
removed=[];moves=[]
def path(qs,net,w=.3,z=k.F_Cu):
 for a,c in zip(qs,qs[1:]):track(a,c,net,z,w)
def mv(ref,x,y,ang):
 f=fps[ref];moves.append({'ref':ref,'before':{'at':xy(f.GetPosition()),'angle':f.GetOrientationDegrees()},'after':{'at':[x,y],'angle':ang}});f.SetOrientationDegrees(ang);f.SetPosition(v(x,y))
# Thermal return second spoke for C10; original vertical return remains connected.
path([xy(pad('C10',2).GetPosition()),(108.95,109.22),(108.95,108.9),(109.5,108.35)],'GND',.2)
for t in list(b.GetTracks()):
 a=xy(t.GetStart());c=xy(t.GetEnd());net=t.GetNetname();take=False
 if net=='VPHY' and not isinstance(t,k.PCB_VIA) and t.GetLayer()==k.F_Cu and min(a[0],c[0])>=114.4:take=True
 if net=='USB5V' and uid(t) in ['16685627-4ae1-4fd8-8eae-e64aa5677631','327b6950-7ec5-48a5-994e-0dbe248d75b9','484b5bb3-0159-4fc3-9f7d-6912e6116930','8f74cbc5-21e5-4d2d-893a-35699878d9cd','dadc7181-ffd5-40a7-8925-96aa86276403','f3e4bc06-523b-4487-99f5-e3ec8babffd6','f91d276b-e84b-412b-937e-216214ba50f7','fbbc249f-cde1-428e-a8ef-f19ef1ae6038','e7a385b8-6da3-430c-8ab0-01c8a9552a52']:take=True
 if net=='+3V3' and t.GetLayer()==k.F_Cu and not isinstance(t,k.PCB_VIA):
  if uid(t)=='c7ac037f-dee5-4e2f-8400-3f895c2c7f51' or uid(t)=='b4f3b50b-e4a3-417d-8fdd-42a82a5b9586':take=True
  if min(a[0],c[0])>=115.15 and min(a[1],c[1])>=117.2 and max(a[1],c[1])<=120.45:take=True
 if net=='GND' and min(a[0],c[0])>117.6 and max(a[0],c[0])<119.5 and min(a[1],c[1])>=116.9 and max(a[1],c[1])<117.7:take=True
 if take:removed.append(record(t));remove(t)
mv('FB1',120,109.55,270);mv('C11',119.2,111.5,0);mv('C1',120.1,114.2,90);mv('C2',120,117.7,270)
# Source on B.Cu is routed in the next stage, staying clear of the priority reference areas.
via((120,108.2),'+3V3');path([(120,108.2),xy(pad('FB1',1).GetPosition())],'+3V3',.25)
path([xy(pad('FB1',2).GetPosition()),(119.3,110.735),(118.25,110.735),xy(pad('C11',1).GetPosition())],'VPHY',.3)
path([xy(pad('C11',1).GetPosition()),(117.8,111.95),(115.1,111.95),(114.4,111.25)],'VPHY',.3)
path([xy(pad('C11',2).GetPosition()),(119.9,111.5),(118.85,112.55)],'GND',.3);via((118.85,112.55),'GND')
path([(121.35,108.649999),(121.35,113.9),xy(pad('C1',1).GetPosition())],'USB5V',.5)
path([xy(pad('C1',1).GetPosition()),(119.5,114.55),(117.45,114.55),(117.02,114.98),xy(pad('C23',1).GetPosition())],'USB5V',.5)
path([xy(pad('C23',1).GetPosition()),(116.3,116.82),(116.3,116.8)],'USB5V',.5)
path([xy(pad('C1',1).GetPosition()),(120.6,115.15),(121.25,115.8)],'USB5V',.5)
# Relocate existing C6/C8 ground vias just enough to retain pad/via clearance.
for old,new in [((119,113.7),(118.85,113.7)),((118.95,119.5),(118.77,119.5))]:
 for t in list(b.GetTracks()):
  if t.GetNetname()!='GND':continue
  if isinstance(t,k.PCB_VIA) and math.dist(xy(t.GetPosition()),old)<.01:t.SetPosition(v(*new))
  elif not isinstance(t,k.PCB_VIA):
   if math.dist(xy(t.GetStart()),old)<.03:t.SetStart(v(*new))
   if math.dist(xy(t.GetEnd()),old)<.03:t.SetEnd(v(*new))
path([xy(pad('C1',2).GetPosition()),(119.3,113.25),(118.85,113.7)],'GND',.3)
path([xy(pad('U1',39).GetPosition()),(116.2,117.75),(116.3,117.85),(118.9,117.85),xy(pad('C2',1).GetPosition())],'+3V3',.15)
path([xy(pad('C2',1).GetPosition()),(119.95,116.7),(117.62,116.7),xy(pad('C5',1).GetPosition())],'+3V3',.3)
path([(118.7,116.7),(118.7,116.4)],'+3V3',.25);via((118.7,116.4),'+3V3')
path([xy(pad('C5',2).GetPosition()),(118.8,117.3)],'GND',.3);via((118.8,117.3),'GND')
path([xy(pad('C2',2).GetPosition()),(120,119.7)],'GND',.4);via((120,119.7),'GND')
via((119.6,120.45),'+3V3');path([(119.6,120.45),(115.55,120.45)],'+3V3',.2)
(OUT/'east_placement.json').write_text(json.dumps(moves,indent=2));(OUT/'east_removed.json').write_text(json.dumps(removed,indent=2));drc('east_trial2')
