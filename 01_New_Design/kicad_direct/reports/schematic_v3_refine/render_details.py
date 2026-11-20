from pathlib import Path
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent
boxes={'usb_esd':(15,25,95,68),'ft232h':(88,48,194,133),'uart_caps':(235,44,310,90),'ldos':(21,172,108,247),'eeprom':(229,166,330,205),'load_switch':(23,287,142,315),'label_stubs':(258,240,334,282),'crystal':(87,29,144,55),'uart_crossings':(174,64,379,109),'coils':(90,48,138,88)}
for version in ['before','after']:
 im=Image.open(H/version/('detail_source.png' if version=='after' else 'schematic.png')).convert('RGB');f=im.width/(594/1.27)
 for name,box in boxes.items():im.crop(tuple(round(v*f) for v in box)).save(H/version/f'detail_{name}.png')
 im.resize((1680,1188)).save(H/version/'overview.png')
canvas=Image.new('RGB',(3360,1218),'white');dr=ImageDraw.Draw(canvas)
for i,version in enumerate(['before','after']):
 canvas.paste(Image.open(H/version/'overview.png'),(i*1680,30));dr.text((i*1680+20,10),'V3 BASELINE' if i==0 else 'V3 REFINE',fill='black')
canvas.save(H/'comparison_v3_refine.png')
for name in boxes:
 pics=[Image.open(H/v/f'detail_{name}.png') for v in ['before','after']];height=max(p.height for p in pics)
 pics=[p.resize((round(p.width*height/p.height),height)) for p in pics]
 c=Image.new('RGB',(sum(p.width for p in pics),height+30),'white');d=ImageDraw.Draw(c);x=0
 for v,p in zip(['V3 BASELINE','V3 REFINE'],pics):c.paste(p,(x,30));d.text((x+10,10),v,fill='black');x+=p.width
 c.save(H/f'comparison_{name}.png')
