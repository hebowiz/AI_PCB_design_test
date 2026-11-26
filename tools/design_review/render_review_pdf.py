"""Render existing KiCad copper PDFs to fixed review PNG names; does not touch CAD."""
import argparse
from pathlib import Path
import pypdfium2 as pdf
from PIL import Image, ImageChops, ImageDraw, ImageFont


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--front',required=True,type=Path)
    parser.add_argument('--back',required=True,type=Path)
    parser.add_argument('--out',required=True,type=Path)
    parser.add_argument('--font',required=True,type=Path)
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    for side,source in [('front',args.front),('back',args.back)]:
        with pdf.PdfDocument(source) as doc:
            im=doc[0].render(scale=8).to_pil().convert('RGB')
        bounds=ImageChops.difference(im,Image.new('RGB',im.size,'white')).getbbox()
        if bounds is None:raise ValueError('Blank plot: '+str(source))
        im=im.crop(bounds);im.thumbnail((1600,3200))
        sheet=Image.new('RGB',(im.width,im.height+64),'white');sheet.paste(im,(0,64))
        ImageDraw.Draw(sheet).text((10,10),'KiCad saved copper: '+side+' (top projection)',fill='black',font=ImageFont.truetype(str(args.font),22))
        sheet.save(args.out/('pcb_'+side+'.png'))


if __name__=='__main__':main()
