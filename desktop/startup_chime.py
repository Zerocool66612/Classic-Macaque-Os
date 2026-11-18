"""Generate an original, warm Macaque Classic startup chime (no sampled audio)."""
import math,struct,wave
from pathlib import Path
def write(path,rate=22050):
    notes=[(261.63,0.0,1.55),(329.63,0.09,1.65),(392.0,0.19,1.8),(523.25,0.30,1.9),(783.99,0.45,1.6)]
    out=[]
    for i in range(int(2.5*rate)):
        t=i/rate;v=0.0
        for freq,on,dur in notes:
            u=t-on
            if 0<=u<dur:
                env=min(1.0,u/.045)*min(1.0,(dur-u)/.5)*math.exp(-u*.5)
                v+=env*(math.sin(math.tau*freq*u)+.22*math.sin(math.tau*2*freq*u)+.07*math.sin(math.tau*3*freq*u))
        out.append(v)
    peak=max(abs(v) for v in out) or 1
    pcm=[round(v/peak*14500) for v in out]
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(path),'wb') as wav:
        wav.setparams((1,2,rate,0,'NONE','not compressed'))
        wav.writeframes(struct.pack('<'+'h'*len(pcm),*pcm))
if __name__=='__main__':write(Path(__file__).parent/'sounds/startup.wav')
