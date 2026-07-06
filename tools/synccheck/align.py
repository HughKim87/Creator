import subprocess, sys, numpy as np
sys.path.insert(0,'/sessions/wonderful-admiring-galileo/mnt/outputs/synccheck')
from srt_slice import parse

VID="/sessions/wonderful-admiring-galileo/mnt/김실버유튜브/workspace/inputs/2026-06-30 00-23-03.mp4"
SRT="/sessions/wonderful-admiring-galileo/mnt/김실버유튜브/workspace/inputs/2026-06-30 00-23-03.srt"
blocks=parse(SRT)
SR=16000; HOP=0.05

def rms_curve(lo, dur):
    cmd=["ffmpeg","-v","error","-ss",str(lo),"-t",str(dur),"-i",VID,
         "-vn","-ac","1","-ar",str(SR),"-f","s16le","-"]
    raw=subprocess.run(cmd,capture_output=True).stdout
    x=np.frombuffer(raw,dtype=np.int16).astype(np.float32)/32768
    n=int(SR*HOP)
    m=len(x)//n
    return np.sqrt((x[:m*n].reshape(m,n)**2).mean(axis=1))

def mask(lo, m_len, lag):
    t=lo+np.arange(m_len)*HOP - lag   # subtitle time shifted by lag
    mk=np.zeros(m_len,bool)
    for a,c,_ in blocks:
        if c<lo-30 or a>lo+m_len*HOP+30: continue
        mk |= (t>=a)&(t<=c)
    return mk

def analyze(name, clip_lo, clip_hi):
    lo=clip_lo-20; dur=(clip_hi-clip_lo)+40
    e=rms_curve(lo,dur)
    # log-energy, normalized
    le=np.log10(e+1e-5)
    best=None; scores=[]
    for lag in np.arange(-15,15.01,0.05):
        mk=mask(lo,len(le),lag)
        if mk.sum()<10 or (~mk).sum()<10: continue
        s=le[mk].mean()-le[~mk].mean()
        scores.append((lag,s))
        if best is None or s>best[1]: best=(lag,s)
    s0=dict((round(l,2),s) for l,s in scores)[0.0]
    print(f"{name}: best_lag={best[0]:+.2f}s (score {best[1]:.3f}) | lag0 score {s0:.3f}")
    # top5 lags
    top=sorted(scores,key=lambda x:-x[1])[:5]
    print("   top lags:", ", ".join(f"{l:+.2f}({s:.3f})" for l,s in top))

analyze("CLIP01a (00:34.3-00:53.3)", 34.3, 53.3)
analyze("CLIP26  (43:17.5-43:54)", 2597.5, 2634)
analyze("CLIP42  (1:16:21.9-1:16:50.2)", 4581.9, 4610.2)
