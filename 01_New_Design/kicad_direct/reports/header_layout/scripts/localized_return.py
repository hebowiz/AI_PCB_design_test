from local_router import *
# Replace only this turn's two trial stitching vias and four pin-9 leads.
ids=['cbac571f-4246-46f6-8c0c-c6e57e1a5ec3','0e4e586d-f1a2-4ab7-b305-ef85673ed5db','1869b141-0811-4d20-a8bf-19efffad30a6','449b9f7f-07e0-49b7-9e90-7a086b10a1f6','5301984d-6e73-49ef-8433-0480bbef418e','a2a8d97b-59d3-42b3-a211-7fcccc0b59c7']
original=k.LoadBoard(str(OUT/'before/a2_usb_uart.kicad_pcb'));assert not(set(ids)&{uid(t) for t in original.GetTracks()})
for t in list(b.GetTracks()):
 if uid(t) in ids:remove(t)
q=(112.6,131.0);via(q,'GND');pts=[xy(pad('U2',9).GetPosition()),(112.875,131.275),q]
for a,c in zip(pts,pts[1:]):track(a,c,'GND',w=.2)
q0=xy(pad('U2',10).GetPosition());end=(114.25,131.95);via(end,'/CTS_N')
assert route(q0,end,'/CTS_N',.15,['U2.10','R12.2'],[q0,end],0,0)
drc('localized_return')
