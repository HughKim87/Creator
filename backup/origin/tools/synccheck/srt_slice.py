import re, sys
def ts2s(t):
    h,m,rest = t.split(':'); s,ms = rest.split(',')
    return int(h)*3600+int(m)*60+int(s)+int(ms)/1000
def parse(path):
    txt = open(path, encoding='utf-8-sig').read()
    blocks=[]
    for b in re.split(r'\n\s*\n', txt.strip()):
        lines=b.strip().split('\n')
        if len(lines)>=2 and '-->' in lines[1]:
            a,c = [x.strip() for x in lines[1].split('-->')]
            blocks.append((ts2s(a), ts2s(c), ' '.join(lines[2:])))
    return blocks
if __name__=='__main__':
    srt=sys.argv[1]; lo=float(sys.argv[2]); hi=float(sys.argv[3])
    for a,c,t in parse(srt):
        if c>=lo and a<=hi:
            print(f"{a:9.3f} -> {c:9.3f} | {t}")
