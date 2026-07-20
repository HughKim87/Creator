#!/usr/bin/env python3
"""컷 내부 무음(쉼) 실측 스캔 — 미세 점프컷 후보 검출.

사용: python3 pause_scan.py <full16k.wav> <cutlist.csv> [min_pause=0.5]
cutlist.csv: 시작,끝,라벨 (HH:MM:SS.s)
출력: 컷별 내부 무음 구간(소스 타임코드, 길이) — 발화 온셋/종료 가드 포함.
webrtcvad 필요: pip install webrtcvad-wheels --break-system-packages
"""
import sys, wave, csv
import webrtcvad

def hms(s):
    h=int(s//3600); m=int(s%3600//60); return f"{h:02d}:{m:02d}:{s%60:06.3f}"

def parse_ts(t):
    p=t.strip().split(':'); p=[float(x) for x in p]
    return p[0]*3600+p[1]*60+p[2] if len(p)==3 else p[0]*60+p[1]

def vad_flags(wav_path):
    w=wave.open(wav_path,'rb'); assert w.getframerate()==16000 and w.getnchannels()==1
    vad=webrtcvad.Vad(2); frame=int(16000*0.03)*2  # 30ms
    data=w.readframes(w.getnframes()); flags=[]
    for i in range(0,len(data)-frame+1,frame):
        flags.append(vad.is_speech(data[i:i+frame],16000))
    return flags  # 30ms per flag

def pauses_in(flags, a, b, min_pause):
    fa, fb = int(a/0.03), int(b/0.03)
    seg=flags[fa:fb]; out=[]; run=0
    for j,f in enumerate(seg):
        if not f: run+=1
        else:
            if run*0.03>=min_pause: out.append((a+(j-run)*0.03, a+j*0.03))
            run=0
    if run*0.03>=min_pause: out.append((a+(len(seg)-run)*0.03, a+len(seg)*0.03))
    return out

if __name__=='__main__':
    wav, cl = sys.argv[1], sys.argv[2]
    minp = float(sys.argv[3]) if len(sys.argv)>3 else 0.5
    flags=vad_flags(wav)
    rows=list(csv.reader(open(cl,encoding='utf-8-sig')))[1:]
    for a,b,label in rows:
        a,b=parse_ts(a),parse_ts(b)
        ps=pauses_in(flags,a,b,minp)
        # 컷 가장자리 무음(머리/꼬리)과 내부 무음 구분
        print(f"## {label}  [{hms(a)}-{hms(b)}] dur {b-a:.1f}s")
        for s,e in ps:
            edge = "머리" if s-a<0.05 else ("꼬리" if b-e<0.05 else "내부")
            print(f"  {edge} 무음 {hms(s)} ~ {hms(e)}  ({e-s:.2f}s)")
