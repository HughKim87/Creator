import subprocess, sys, numpy as np, webrtcvad
sys.path.insert(0,'/sessions/wonderful-admiring-galileo/mnt/outputs/synccheck')
from srt_slice import parse
VID="/sessions/wonderful-admiring-galileo/mnt/김실버유튜브/workspace/inputs/2026-06-30 00-23-03.mp4"
SRT="/sessions/wonderful-admiring-galileo/mnt/김실버유튜브/workspace/inputs/2026-06-30 00-23-03.srt"
blocks=parse(SRT); SR=16000; FR=0.03  # 30ms frames

def speech_segs(lo,dur,aggr=3):
    raw=subprocess.run(["ffmpeg","-v","error","-ss",str(lo),"-t",str(dur),"-i",VID,
        "-vn","-ac","1","-ar",str(SR),"-f","s16le","-"],capture_output=True).stdout
    vad=webrtcvad.Vad(aggr); n=int(SR*FR)*2
    flags=[vad.is_speech(raw[i:i+n],SR) for i in range(0,len(raw)-n,n)]
    # merge into segments (gap tolerance 0.3s, min dur 0.2s)
    segs=[]; cur=None; gap=0
    for i,f in enumerate(flags):
        t=lo+i*FR
        if f:
            if cur is None: cur=[t,t+FR]
            else: cur[1]=t+FR
            gap=0
        elif cur:
            gap+=1
            if gap>10: segs.append(cur); cur=None
    if cur: segs.append(cur)
    return [s for s in segs if s[1]-s[0]>=0.2]

def report(name, clip_lo, clip_hi):
    print(f"== {name} (컷 {clip_lo}~{clip_hi}) ==")
    segs=speech_segs(clip_lo-6,(clip_hi-clip_lo)+12)
    print(" VAD 음성구간:", "; ".join(f"{a:.1f}-{b:.1f}" for a,b in segs))
    bl=[(a,c,t) for a,c,t in blocks if c>=clip_lo-6 and a<=clip_hi+6]
    for a,c,t in bl:
        # nearest VAD onset to block start
        cand=[s for s in segs if abs(s[0]-a)<3]
        d=f"{min(cand,key=lambda s:abs(s[0]-a))[0]-a:+.2f}s" if cand else "  none<3s"
        print(f"  srt[{a:8.2f}-{c:8.2f}] vs 실제발화시작 {d} | {t[:30]}")
    # speech crossing cut boundaries?
    for edge,label in [(clip_lo,'컷 시작'),(clip_hi,'컷 끝')]:
        cross=[s for s in segs if s[0]<edge<s[1]]
        if cross:
            s=cross[0]; print(f"  ⚠ {label} {edge}s가 발화 중간을 자름 (발화 {s[0]:.1f}~{s[1]:.1f})")
        else:
            print(f"  ✓ {label} {edge}s: 발화 경계 침범 없음")

report("CLIP01a", 34.3, 53.3)
report("CLIP26", 2597.5, 2634)
report("CLIP42", 4581.9, 4610.2)
