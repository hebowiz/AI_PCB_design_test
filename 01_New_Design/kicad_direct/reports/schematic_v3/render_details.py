from pathlib import Path
from PIL import Image
H=Path(__file__).resolve().parent
im=Image.open(H/'after/detail_source.png');f=im.width/(594/1.27)
boxes={'usb_ft232h':(10,23,194,164),'crystal':(87,29,155,67),'uart_io':(235,39,380,135),'power_tree':(17,167,239,320),'ldo_feedback':(18,215,238,288),'power_ground_symbols':(130,60,183,140),'eeprom':(225,161,329,211),'load_switch':(20,286,224,319)}
for name,box in boxes.items():im.crop(tuple(round(v*f) for v in box)).save(H/f'after/detail_{name}.png')
im.resize((1680,1188)).save(H/'after/overview.png')
canvas=Image.new('RGB',(3360,1188),'white')
for i,d in enumerate(['before','after']):
 pic=Image.open(H/d/'schematic.png').convert('RGB').resize((1680,1188));canvas.paste(pic,(1680*i,0))
canvas.save(H/'comparison_v2_v3.png')
