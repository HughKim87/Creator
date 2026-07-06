import subprocess, sys, csv, numpy as np, webrtcvad
sys.path.insert(0,'/sessions/wonderful-admiring-galileo/mnt/outputs/synccheck')
BASE="/sessions/wonderful-admiring-galileo/mnt/김실버유튜브"
VID=f"{BASE}/workspace/inputs/2026-06-30 00-23-03.mp4"
CSVP=f"{BASE}/workspace/outputs/analysis/roughcut_cutlist.csv"
SR=16000; FR=0.03

def ts2s(t):
    p=t.split(':'); 
    return int(p[0])*3600+int(p[1])*60+float(p[2])
def s2ts(s):
    h=int(s//3600); m=int(s%3600//60); sec=s%60
    return f"{h:02d}:{m:02d}:{sec:04.1f}".rstrip('0').rstrip('.') if sec%1 else f"{h:02d}:{m:02d}:{int(sec):02d}"

vad=webrtcvad.Vad(3)
def segs(lo,dur):
    raw=subprocess.run(["ffmpeg","-v","error","-ss",str(lo),"-t",str(dur),"-i",VID,
        "-vn","-ac","1","-ar",str(SR),"-f","s16le","-"],capture_output=True).stdout
    n=int(SR*FR)*2
    flags=[vad.is_speech(raw[i:i+n],SR) for i in range(0,len(raw)-n,n)]
    out=[]; cur=None; gap=0
    for i,f in enumerate(flags):
        t=lo+i*FR
        if f:
            if cur is None: cur=[t,t+FR]
            else: cur[1]=t+FR
            gap=0
        elif cur:
            gap+=1
            if gap>10: out.append(cur); cur=None
    if cur: out.append(cur)
    return [s for s in out if s[1]-s[0]>=0.25]

rows=list(csv.reader(open(CSVP,encoding='utf-8-sig')))[1:]
cuts=[(ts2s(a),ts2s(b),lab) for a,b,lab in rows]
SKIP_START={'00_훅_오픈루프_사망직전프리즈'}   # 의도적 경계
SKIP_END={'00_훅_오픈루프_사망직전프리즈'}
shared={}  # boundary equality
for i in range(len(cuts)-1):
    pass

print("### 경계 스캔 (start/end 각각: 침범여부, 제안)")
for idx,(a,b,lab) in enumerate(cuts):
    ss=segs(a-5,10); es=segs(b-5,10)
    msgs=[]
    # START
    if lab not in SKIP_START:
        st=[s for s in ss if s[0]<a<s[1]]
        if st:
            s0,s1=st[0]
            if a-s0<=2.0: msgs.append(f"START 발화중간({a-s0:.2f}s 침범) → {s2ts(max(s0-0.4,0))} 제안")
            else: msgs.append(f"START 발화중간(침범 {a-s0:.2f}s>2s) → 수동확인")
        else:
            nxt=[s for s in ss if s[0]>=a]
            if nxt and nxt[0][0]-a>2.5: msgs.append(f"START 유휴 {nxt[0][0]-a:.1f}s (발화 {s2ts(nxt[0][0])}) → 당김 검토")
    # END
    if lab not in SKIP_END:
        en=[s for s in es if s[0]<b<s[1]]
        if en:
            s0,s1=en[0]
            if s1-b<=2.5:
                # cap: next onset
                nxt=[s for s in es if s[0]>s1]
                cap=nxt[0][0]-0.15 if nxt else s1+0.4
                msgs.append(f"END 발화중간(잔여 {s1-b:.2f}s) → {s2ts(min(s1+0.4,cap))} 제안")
            else: msgs.append(f"END 발화중간(잔여 {s1-b:.2f}s>2.5s) → 수동확인")
        else:
            nxt=[s for s in es if b-0.1<=s[0]<=b+0.35]
            if nxt: msgs.append(f"END 직후 {nxt[0][0]-b:+.2f}s 새발화 유입 위험 → {s2ts(nxt[0][0]-0.15)} 제안")
    if msgs: print(f"[{idx+1:02d}] {lab} ({s2ts(a)}~{s2ts(b)})\n      " + "\n      ".join(msgs))

print("\n### 인접 컷 갭 (0 < gap ≤ 3s → 병합 후보)")
for i in range(len(cuts)-1):
    g=cuts[i+1][0]-cuts[i][1]
    if 0<g<=3: print(f"  {cuts[i][2]} → {cuts[i+1][2]}: 갭 {g:.1f}s")
    elif abs(g)<0.01: print(f"  {cuts[i][2]} → {cuts[i+1][2]}: 공유 경계 (짝 이동 필요)")
