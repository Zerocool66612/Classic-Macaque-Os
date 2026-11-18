"""Generate an original, warm Macaque Classic startup chime (no sampled audio)."""
import math,struct,wave
from pathlib import Path
def write(path,rate=22050):
    notes=[(261.63,0.0,1.1),(329.63,0.07,1.2),(392.0,0.14,1.25),(523.25,0.23,1.35),(783.99,0.32,1.25)]
    out=[]
    for i in range(int(1.8*rate)):
        t=i/rate;v=0.0
        for freq,on,dur in notes:
            u=t-on
            if 0<=u<dur:
                env=min(1.0,u/.045)*min(1.0,(dur-u)/.35)*math.exp(-u*.5)
                v+=env*(math.sin(math.tau*freq*u)+.22*math.sin(math.tau*2*freq*u)+.07*math.sin(math.tau*3*freq*u))
        out.append(v)
    peak=max(abs(v) for v in out) or 1
    pcm=[round(v/peak*14500) for v in out]
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(path),'wb') as wav:
        wav.setparams((1,2,rate,0,'NONE','not compressed'))
        wav.writeframes(struct.pack('<'+'h'*len(pcm),*pcm))
if __name__=='__main__':write(Path(__file__).parent/'sounds/startup.wav')
