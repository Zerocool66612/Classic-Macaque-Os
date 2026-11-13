"""Reproducible Macaque boot-menu artwork. Pillow is authoring-only."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import math
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'iso/grub-theme';OUT.mkdir(exist_ok=True)
def font(n,bold=False):return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans'+('-Bold' if bold else '')+'.ttf',n)
def background(size):
 w,h=size;im=Image.new('RGB',size,'#145264');d=ImageDraw.Draw(im)
 for i,color in enumerate(['#1b606e','#236e7a','#307d87','#41909a','#5ba0a7']):
  pts=[(x,int(h*(.30+i*.125)+h*.035*math.sin(x/w*math.pi*2+i*.8))) for x in range(0,w+4,4)]
  d.polygon(pts+[(w,h),(0,h)],fill=color)
 return im
background((1600,1000)).save(OUT/'background.png')
logo=Image.open(ROOT/'iso/branding/macaque-logo.png').convert('RGBA');logo.resize((72,72),Image.Resampling.LANCZOS).save(OUT/'logo.png')
header=Image.new('RGB',(600,32),'#3b474e');d=ImageDraw.Draw(header)
for y in range(4,30,3):d.line((4,y,595,y),fill='#66747b')
for x,c in [(17,'#ed6c5d'),(35,'#efc24c'),(53,'#6bbd62')]:d.ellipse((x-5,11,x+5,21),fill=c,outline='#18262c')
header.save(OUT/'header.png')
# Nine-slice styled boxes: preserve borders while GRUB sizes the menu.
for prefix,color,border in [('panel','#202b31','#899ba1'),('select','#367b9c','#8dc5d9')]:
 im=Image.new('RGB',(24,24),color);d=ImageDraw.Draw(im);d.rectangle((0,0,23,23),outline='#17262c');d.rectangle((1,1,22,22),outline=border)
 for suffix,box in {'nw':(0,0,4,4),'n':(4,0,20,4),'ne':(20,0,24,4),'w':(0,4,4,20),'c':(4,4,20,20),'e':(20,4,24,20),'sw':(0,20,4,24),'s':(4,20,20,24),'se':(20,20,24,24)}.items():im.crop(box).save(OUT/(prefix+'_'+suffix+'.png'))
# Syslinux BIOS fallback has a fixed 640x480 canvas.
bios=background((640,480));d=ImageDraw.Draw(bios);bios.paste(logo.resize((58,58)),(291,30),logo.resize((58,58)));d.text((320,101),'Macaque Classic',font=font(24,True),fill='white',anchor='mm');d.rectangle((45,149,594,385),fill='#202b31',outline='#899ba1',width=2);bios.paste(header.resize((550,30)),(45,132));d.text((320,147),'Startup Options',font=font(15,True),fill='white',anchor='mm');bios.save(OUT/'bios-splash.png')
# Layout illustration uses the same assets; it is not a firmware screenshot.
preview=background((1024,768));d=ImageDraw.Draw(preview);preview.paste(Image.open(OUT/'logo.png'),(476,90),Image.open(OUT/'logo.png'));d.text((512,208),'Macaque Classic',font=font(16),fill='white',anchor='mm');d.text((512,244),'Choose how to start your computer',font=font(16),fill='#dcf0f0',anchor='mm');preview.paste(header.resize((656,32)),(184,276));d.text((512,292),'Startup Options',font=font(16,True),fill='white',anchor='mm');d.rectangle((184,315,840,607),fill='#202b31',outline='#899ba1',width=2)
for y,text in [(340,'Macaque Classic'),(382,'Advanced options for Macaque Classic'),(424,'UEFI Firmware Settings')]:
 if y==340:d.rectangle((197,y-15,827,y+17),fill='#367b9c',outline='#8dc5d9')
 d.text((216,y),text,font=font(16),fill='white',anchor='lm')
d.text((512,658),'Starting the selected entry in 7 seconds',font=font(16),fill='white',anchor='mm');d.text((512,698),'Arrow keys: select   Enter: start   E: edit   C: console',font=font(14),fill='#e0eeee',anchor='mm');d.text((512,741),'Theme layout preview — firmware rendering not yet verified',font=font(12),fill='#d1e1e5',anchor='mm');preview.save(ROOT/'docs/grub-theme-preview.png')
print('Rendered GRUB assets and layout preview')
