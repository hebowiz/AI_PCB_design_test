from local_router import *
original=k.LoadBoard(str(OUT/'before/a2_usb_uart.kicad_pcb'));orig={uid(t):t for t in original.GetTracks()}
ids=['cbac571f-4246-46f6-8c0c-c6e57e1a5ec3','0e4e586d-f1a2-4ab7-b305-ef85673ed5db','1869b141-0811-4d20-a8bf-19efffad30a6','449b9f7f-07e0-49b7-9e90-7a086b10a1f6','5301984d-6e73-49ef-8433-0480bbef418e','a2a8d97b-59d3-42b3-a211-7fcccc0b59c7']
assert not(set(ids)&set(orig))
for t in list(b.GetTracks()):
 if uid(t) in ids:remove(t)
oldpins={p.GetNumber():xy(p.GetPosition()) for p in fps['R12'].Pads()};fps['R12'].SetPosition(v(117.0,135.6))
# Rebuild geometry cache after moving this one resistor.
import local_router as lr
lr.PADGEOM[:]=[(p,poly(p)) for f in fps.values() for p in f.Pads()]
for id in ['1d557cae-9671-448d-92e4-865d64e04c91','3bcef50d-2265-44cc-9fb6-af0c9cca8ce7','e2ccc9d7-d6e3-4df7-8822-dbfdac4ddf63','ff2de779-8fc0-46e9-b236-5bb7e4f0b65c','4d4920ea-5702-4976-a952-fbd382e8c27c']:
 t=orig[id]
 if isinstance(t,k.PCB_VIA):via(xy(t.GetPosition()),t.GetNetname())
 else:track(xy(t.GetStart()),xy(t.GetEnd()),t.GetNetname(),t.GetLayer(),k.ToMM(t.GetWidth()))
q=(115.15,131.1);via(q,'GND');track((114.95,131.275),(114.975,131.275),'GND',w=.25);track((114.975,131.275),q,'GND',w=.25)
for t in list(b.GetTracks()):
 if t.GetNetname()=='/CTS_N' and not isinstance(t,k.PCB_VIA) and t.GetLayer()==0 and max(xy(t.GetStart())[0],xy(t.GetEnd())[0])>114.5 and max(xy(t.GetStart())[1],xy(t.GetEnd())[1])<131.2 and min(xy(t.GetStart())[1],xy(t.GetEnd())[1])>130.5:remove(t)
for n in ['1','2']:
 p=pad('R12',n);q=xy(p.GetPosition());name=p.GetNetname();end=oldpins[n]
 if n=='2':end=(114.25,131.95)
 assert route(q,end,name,.15,['R12.'+n],[q,end],0,1 if n=='2' else 0)
drc('r12_clearance')
