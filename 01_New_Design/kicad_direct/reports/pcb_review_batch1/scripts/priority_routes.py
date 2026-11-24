from common import *
# Primary differential span width .80, edge gap .20, pair pitch 1.00.
for t in list(b.GetTracks()):
 if t.GetNetname() in ['/USB_D+','/USB_D-']:remove(t)
line([(110,104.75),(110,105.8),(110.5,106.3),(110.5,109.25)],'/USB_D-',w=.8)
line([(112,104.75),(112,105.8),(111.5,106.3),(111.5,109.25)],'/USB_D+',w=.8)
# Narrow transitions and the only USB layer crossover (2 through vias).
line([(110.5,109.25),(110.5,109.5)],'/USB_D-',w=.3);via(110.5,109.5,'/USB_D-')
line([(110.5,109.5),(111.3,110.3),(111.3,110.4)],'/USB_D-',p.B_Cu,.3);via(111.3,110.4,'/USB_D-')
line([(111.3,110.4),(111.25,110.45),(111.25,111.8375)],'/USB_D-',w=.15)
line([(111.5,109.25),(111.5,109.65),(110.75,110.4),(110.75,111.8375)],'/USB_D+',w=.15)
# ESD pads meet the outer edge of the through route; no long signal stubs.
line([xy(pad('D1',1).GetPosition()),(111.5,107.0)],'/USB_D+',w=.2)
line([xy(pad('D5',1).GetPosition()),(110.5,107.0)],'/USB_D-',w=.2)
# Crystal: short parallel escape, then fanout to opposed crystal pads.
for t in list(b.GetTracks()):
 if t.GetNetname() in ['/XTAL_IN','/XTAL_OUT']:remove(t)
line([(113.75,111.8375),(113.75,110.8),(113.85,110.7),(117.6,110.7),(117.6,110.25),(116.85,109.5)],'/XTAL_IN',w=.15)
line([(113.25,111.8375),(113.25,109.3),(115.15,107.4),(115.15,107.3)],'/XTAL_OUT',w=.15)
line([xy(pad('C13',1).GetPosition()),(118.6,109.5),(116.85,109.5)],'/XTAL_IN',w=.15)
line([xy(pad('C14',1).GetPosition()),(113.35,107.3),(115.15,107.3)],'/XTAL_OUT',w=.15)
# Backside signal/via reservation. Ground fill remains enabled.
for rect,name in [((109.7,105.85,112.3,109.1),'USB reference plane'),((112.95,106.6,119.1,110.95),'Crystal reference plane')]:
 z=p.ZONE(b);z.SetLayer(p.B_Cu);z.SetIsRuleArea(True);z.SetZoneName(name);z.SetDoNotAllowTracks(True);z.SetDoNotAllowVias(True);z.SetDoNotAllowZoneFills(False);z.SetDoNotAllowPads(False);poly=z.Outline();poly.NewOutline();x0,y0,x1,y1=rect
 for x,y in [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]:poly.Append(v(x,y))
 b.Add(z)
# Keep same-layer ground distant from the uniform pair to retain microstrip model.
z=p.ZONE(b);z.SetLayer(p.F_Cu);z.SetIsRuleArea(True);z.SetZoneName('USB microstrip top copper separation');z.SetDoNotAllowTracks(False);z.SetDoNotAllowVias(False);z.SetDoNotAllowZoneFills(True);z.SetDoNotAllowPads(False);poly=z.Outline();poly.NewOutline()
for x,y in [(108.9,105.9),(113.1,105.9),(113.1,109.2),(108.9,109.2)]:poly.Append(v(x,y))
b.Add(z)
pro=json.loads((ROOT/'a2_usb_uart.kicad_pro').read_text());nc=dict(pro['net_settings']['classes'][0]);nc.update(name='USB_90ohm',diff_pair_width=.8,diff_pair_gap=.2,diff_pair_via_gap=.5,track_width=.8,via_diameter=.6,via_drill=.3);pro['net_settings']['classes']=[c for c in pro['net_settings']['classes'] if c['name']!='USB_90ohm']+[nc];pro['net_settings']['netclass_patterns']=[{'netclass':'USB_90ohm','pattern':'/USB_D*'}]
(ROOT/'a2_usb_uart.kicad_pro').write_text(json.dumps(pro,indent=2)+'\n')
d=drc('priority');print('violations',len(d['violations']),'unconnected',len(d['unconnected_items']))
