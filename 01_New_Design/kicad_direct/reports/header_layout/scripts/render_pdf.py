from pathlib import Path
import pypdfium2 as pdf
from PIL import Image,ImageChops,ImageDraw,ImageFont
p=Path(__file__).resolve().parents[1]/'images'
for name in ['front','back','before_front']:
 doc=pdf.PdfDocument(p/(name+'.pdf'));im=doc[0].render(scale=3).to_pil().convert('RGB');box=ImageChops.difference(im,Image.new('RGB',im.size,'white')).getbbox();im=im.crop((max(0,box[0]-20),max(0,box[1]-20),min(im.width,box[2]+20),min(im.height,box[3]+20)));im.save(p/(name+'.png'))
a=Image.open(p/'before_front.png');b=Image.open(p/'front.png');h=1800
a=a.resize((round(a.width*h/a.height),h));b=b.resize((round(b.width*h/b.height),h));im=Image.new('RGB',(a.width+b.width+60,h+70),'white');d=ImageDraw.Draw(im);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',28);d.text((20,20),'Before: cd672333',fill='black',font=font);d.text((a.width+40,20),'R-0034 candidate',fill='black',font=font);im.paste(a,(10,60));im.paste(b,(a.width+40,60));im.save(p/'comparison.png')
# Corresponding lower 55 percent shows all changed placements.
for name in ['front','back','after_top']:
 im=Image.open(p/(name+'.png'));im.crop((0,int(im.height*.47),im.width,im.height)).save(p/(name+'_detail.png'))
