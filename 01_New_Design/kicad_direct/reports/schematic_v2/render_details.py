"""Rendered-PDF crops; no schematic or design data is edited."""
from pathlib import Path
from PIL import Image
H=Path(__file__).resolve().parent
im=Image.open(H/'after/detail_source.png')
boxes={'usb_clock_reset':(10,16,200,145),'uart_io':(190,16,380,140),'vio_feedback':(110,233,255,320),
'eeprom':(215,155,335,225),'load_switch':(320,233,455,295),'indicators':(390,35,462,110),
'fixed_3v3':(15,230,100,312),'enable':(255,226,315,312),'ft_supply_bank':(15,147,198,233)}
for name,box in boxes.items():
 f=im.width/(594/1.27);im.crop(tuple(round(v*f) for v in box)).save(H/f'after/detail_{name}.png')
im.resize((1680,1188)).save(H/'after/overview.png')
# Equal page scales for V0/V1/V2; these are evidence images, not edited circuit drawings.
thumbs=[]
for d in ['before','v1_reference','after']:
 a=Image.open(H/d/'schematic.png').convert('RGB');a.thumbnail((1400,990));thumbs.append(a)
out=Image.new('RGB',(4200,990),'white')
for i,a in enumerate(thumbs):out.paste(a,(i*1400,0))
out.save(H/'comparison_v0_v1_v2.png')
