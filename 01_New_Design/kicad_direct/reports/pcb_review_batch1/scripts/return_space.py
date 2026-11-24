from common import *
logs=[]
def remap(net,mapping):
 for t in list(b.GetTracks()):
  if isinstance(t,p.PCB_VIA) or t.GetNetname()!=net or t.GetLayer()!=p.F_Cu:continue
  for getter,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
   a=xy(getter())
   for old,new in mapping.items():
    if math.dist(a,old)<.00001:setter(v(*new));logs.append({'uuid':t.m_Uuid.AsString(),'old':old,'new':new});break
# Move the distribution branch away from the decoupler ground returns.
remap('+3V3',{(118.5,117.95):(119.4,117.95),(118.5,120.35):(119.4,120.35),(118.5,120.45):(119.4,120.45)})
# Restore spacing alongside the enable line without a new layer change.
remap('USB5V',{(110,124.6):(109.95,124.55),(110,133.3):(109.95,133.35)})
# Make physical space for C16's ground return; preserve R4 pin nets/attributes.
fps['R4'].SetPosition(v(103.9,125.6));remap('/EE_DO',{(104.49,125.6):(103.39,125.6),(104.5,125.6):(103.4,125.6)})
remap('/EE_DATA',{(105.51,125.6):(104.41,125.6),(105.5,125.6):(104.4,125.6),(105.5,124.8):(104.4,124.8),(104.1,127.0):(103.0,127.0)})
# C12 (DNP) remains on its original nets; relocate to clear C3's return.
fps['C12'].SetPosition(v(103.0,109.0));remap('VPLL',{(105.25,109.8):(103.95,109.0),(105.25,109.55):(104.5,109.55)})
# Actual copper shape changes, no DRC exemptions.
for z in b.Zones():
 if not z.GetIsRuleArea():z.SetThermalReliefGap(p.FromMM(.15));z.SetThermalReliefSpokeWidth(p.FromMM(.15))
(OUT/'return_space_changes.json').write_text(json.dumps(logs,indent=2));drc('return_space')
