from common import *
# Three VPHY segments created during this batch cross beneath the crystal pin escapes.
uids=['26797e96-6b31-47eb-a690-f77aa8c3351c','58ba5abd-366e-4568-b72f-ff8b700daa1a','b868166d-2017-4a71-8d92-1f435aaacbfd']
log=[]
for uid in uids:
 t=next(t for t in b.GetTracks() if t.m_Uuid.AsString()==uid)
 assert t.GetNetname()=='VPHY' and t.GetLayer()==p.B_Cu
 log.append({'uuid':uid,'a':xy(t.GetStart()),'b':xy(t.GetEnd())});remove(t)
line([(112.625,108.65),(112.55,108.725),(112.55,112.95),(114.4,112.95),(114.4,111.25)],'VPHY',p.B_Cu,.15)
z=p.ZONE(b);z.SetIsRuleArea(True);z.SetLayer(p.B_Cu);z.SetZoneName('Crystal pin reference plane');z.SetDoNotAllowTracks(True);z.SetDoNotAllowVias(False);z.SetDoNotAllowZoneFills(False);poly=z.Outline();poly.NewOutline()
for x,y in [(113.025,110.9),(113.975,110.9),(113.975,111.95),(113.025,111.95)]:poly.Append(p.FromMM(x),p.FromMM(y))
b.Add(z);KEEP.append(z)
rules=ROOT/'a2_usb_uart.kicad_dru';s=rules.read_text().replace("A.intersectsArea('Crystal reference plane'))","A.intersectsArea('Crystal reference plane') || A.intersectsArea('Crystal pin reference plane'))");rules.write_text(s)
(OUT/'crystal_underpass_correction.json').write_text(json.dumps({'removed':log,'new_path':[[112.625,108.65],[112.55,108.725],[112.55,112.95],[114.4,112.95],[114.4,111.25]]},indent=2));drc('crystal_underpass')
