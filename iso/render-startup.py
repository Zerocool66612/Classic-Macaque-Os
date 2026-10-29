"""Generate original code-drawn boot/login assets. Requires Pillow on the authoring host only."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
root=Path(__file__).resolve().parent.parent
out=root/'iso/startup';(out/'plymouth').mkdir(parents=True,exist_ok=True)
def font(size,bold=False):return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans'+('-Bold' if bold else '')+'.ttf',size)
logo=Image.open(root/'iso/branding/macaque-logo.png').convert('RGBA')
def center(d,y,text,size=20,bold=False,width=640):d.text((width/2,y),text,font=font(size,bold),fill='#171717',anchor='mt')
def frame(d,rect):
 x,y,x2,y2=rect;d.rectangle(rect,fill='#d5d5d5',outline='#242424',width=2);d.line((x+2,y+2,x2-2,y+2),fill='white',width=2);d.line((x+2,y+2,x+2,y2-2),fill='white',width=2);d.line((x+3,y2-2,x2-2,y2-2),fill='#777777',width=2)
card=Image.new('RGB',(640,400),'#aaaaaa');d=ImageDraw.Draw(card);d.rectangle((7,9,639,399),fill='#777777');frame(d,(1,1,632,390))
for y in range(9,35,4):d.line((12,y,620,y),fill='#999999')
d.rectangle((226,4,410,36),fill='#d5d5d5');center(d,8,'Macaque Classic',16,True)
card.paste(logo.resize((100,100)),(270,60),logo.resize((100,100)))
center(d,182,'Welcome to Macaque Classic',25,True);center(d,230,'Starting up…',16)
d.rectangle((88,301,552,323),fill='white',outline='#303030',width=2);d.line((90,303,550,303),fill='#777777')
center(d,350,'Classic character. A fresh start.',14)
card.save(out/'plymouth/startup.png')
bar=Image.new('RGB',(458,16),'#5485ba');bd=ImageDraw.Draw(bar)
for y in range(2,16,4):bd.line((0,y,458,y),fill='#99b6da')
bar.save(out/'plymouth/progress.png')
logo.resize((96,96)).save(out/'user.png')
bg=Image.new('RGB',(1600,1000),'#aaaaaa');d=ImageDraw.Draw(bg)
for y in range(0,1000,4):d.line((0,y,1600,y),fill='#b2b2b2')
bg.paste(logo.resize((94,94)),(753,130),logo.resize((94,94)));center(d,242,'Macaque Classic',32,True,1600);center(d,291,'Welcome back.',18,False,1600)
bg.save(out/'login.png')
# Illustrative preview: real authentication controls are supplied by LightDM.
preview=bg.copy();d=ImageDraw.Draw(preview);frame(d,(560,390,1040,735));center(d,416,'Log in to your computer',20,True,1600)
for y,label,value in [(473,'User','Your account'),(561,'Password','••••••••')]:
 d.text((592,y),label,font=font(16),fill='#171717');d.rectangle((591,y+28,1009,y+70),fill='white',outline='#777777',width=2);d.text((605,y+37),value,font=font(17),fill='#333333')
frame(d,(892,677,1009,715));d.text((950,686),'Log In',font=font(16,True),fill='#171717',anchor='mt')
preview.save(root/'login-design-preview.png')
boot=Image.new('RGB',(1100,760),'#aaaaaa');boot.paste(card,(230,180));boot.paste(bar.crop((0,0,290,16)),(321,484));boot.save(root/'boot-design-preview.png')
print('Rendered startup, login and illustrative previews')
