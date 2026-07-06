import subprocess, sys, csv, numpy as np, webrtcvad
sys.path.insert(0,'/sessions/wonderful-admiring-galileo/mnt/outputs/synccheck')
from srt_slice import parse
BASE="/sessions/wonderful-admiring-galileo/mnt/김실버유튜브"
VID=f"{BASE}/workspace/inputs/2026-06-30 00-23-03.mp4"
SRT=f"{BASE}/workspace/inputs/2026-06-30 00-23-03.srt"
CSVP=f"{BASE}/workspace/outputs/analysis/roughcut_cutlist.csv"
DUR=4924.0; SR=16000; FR=0.03
blocks=parse(SRT)
vad=webrtcvad.Vad(3)

def ts2s(t):
    p=t.split(':'); return int(p[0])*3600+int(p[1])*60+float(p[2])
def s2ts(s):
    s=round(s,1); h=int(s//3600); m=int(s%3600//60); sec=s-h*3600-m*60
    if abs(sec-round(sec))<1e-9: return f"{h:02d}:{m:02d}:{int(round(sec)):02d}"
    return f"{h:02d}:{m:02d}:{sec:04.1f}"
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

rows=list(csv.reader(open(CSVP,encoding='utf-8-sig')))
hdr,rows=rows[0],rows[1:]
cuts=[[ts2s(a),ts2s(b),lab] for a,b,lab in rows]

# 수동 오버라이드 (자막 교차검증 완료)
OV_START={33:2701.7, 36:2963.4, 44:4375.6}   # 1-based idx
OV_END={2:53.2, 8:347.0, 32:2701.7}
SKIP=set()
SKIP_START={1,4,10,21,23,35}  # 훅, 01c(VAD오탐), 30 등 검증결과 유지
SKIP_END={1,21,35}
SHARED_EDGES={(10,11),(12,13),(13,14)}  # 05|06,07|08,08|09
for a,b in SHARED_EDGES: SKIP_END.add(a); SKIP_START.add(b)

changes=[]
for i,(a,b,lab) in enumerate(cuts,1):
    na,nb=a,b
    ss=segs(a-5,10); es=segs(b-5,10)
    # blocks around
    first_blk=next((blk for blk in blocks if blk[1]>a+0.01),None)
    prev_blk_end=max([blk[1] for blk in blocks if blk[1]<=a+0.01] or [0])
    last_blk_end=max([blk[1] for blk in blocks if blk[0]<b-0.01] or [0])
    next_blk_start=next((blk[0] for blk in blocks if blk[0]>b+0.01),DUR)
    # START
    if i in OV_START: na=OV_START[i]
    elif i not in SKIP_START:
        st=[s for s in ss if s[0]<a<s[1]]
        mid_block = first_blk and first_blk[0]<a-2.5  # 의도적 블록중간 시작
        if st and not mid_block and a-st[0][0]<=2.0:
            cand=max(st[0][0]-0.4, prev_blk_end+0.1, 0)
            if cand<a-0.05: na=cand
    # END
    if i in OV_END: nb=OV_END[i]
    elif i not in SKIP_END:
        en=[s for s in es if s[0]<b<s[1]]
        if en and en[0][1]-b<=2.5:
            nxt_on=next((s[0] for s in es if s[0]>en[0][1]),DUR)
            cand=min(en[0][1]+0.4, nxt_on-0.15, next_blk_start-0.1, DUR)
            if cand>b+0.05: nb=cand
        else:
            near=[s for s in es if b-0.1<=s[0]<=b+0.35]
            if near:
                cand=max(near[0][0]-0.15, last_blk_end+0.05)
                if cand<b-0.02: nb=cand
    na,nb=round(na,1),round(nb,1)
    if na!=a or nb!=b:
        changes.append((i,lab,a,na,b,nb))
    cuts[i-1]=[na,nb,lab]

# 무결성: 순방향/이웃 겹침 검사 (컷 순서는 타임라인 순서=CSV 순서, 원본시간 순서 아님(훅))
err=0
for i,(a,b,lab) in enumerate(cuts,1):
    if not (0<=a<b<=DUR): print("!! 범위오류",i,lab); err+=1
srt_sorted=sorted(cuts[1:],key=lambda c:c[0])  # 훅 제외 원본시간순
for c1,c2 in zip(srt_sorted,srt_sorted[1:]):
    if c1[1]>c2[0]+0.01: print(f"!! 겹침: {c1[2]}({s2ts(c1[1])}) > {c2[2]}({s2ts(c2[0])})"); err+=1
print(f"무결성: {'FAIL' if err else 'OK'} | 변경 {len(changes)}건 | 합계 {sum(b-a for a,b,_ in cuts)/60:.1f}분")
for i,lab,a,na,b,nb in changes:
    sa=f"{s2ts(a)}→{s2ts(na)}" if na!=a else "-"
    sb=f"{s2ts(b)}→{s2ts(nb)}" if nb!=b else "-"
    print(f"[{i:02d}] {lab[:30]:32s} 시작 {sa:22s} 끝 {sb}")
if not err:
    with open(CSVP,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f); w.writerow(hdr)
        for a,b,lab in cuts: w.writerow([s2ts(a),s2ts(b),lab])
    print("CSV 갱신 완료:",CSVP)
