import base64, html, json, re
from pathlib import Path
from html.parser import HTMLParser

ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/'evidence.json').read_text(encoding='utf-8'))

def inline(s):
    s=html.escape(s)
    s=re.sub(r'\[([^\]]+)\]\(([^\s)]+)\)',lambda m:f'<a href="{m[2]}">{m[1]}</a>',s)
    s=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',s)
    return s

def md(source,prefix):
    out=[]; nav=[]; para=[]; in_list=False; count=0
    def flush():
        if para:
            out.append('<p>'+inline(' '.join(para))+'</p>');para.clear()
    lines=source.splitlines();i=0
    while i<len(lines):
        line=lines[i].strip()
        if line.startswith('|'):
            flush()
            if in_list:out.append('</ul>');in_list=False
            group=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                cells=[c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?',c) for c in cells):group.append(cells)
                i+=1
            out.append('<div class="tablewrap"><table><thead><tr>'+''.join('<th>'+inline(c)+'</th>' for c in group[0])+'</tr></thead><tbody>')
            for row in group[1:]:out.append('<tr>'+''.join('<td>'+inline(c)+'</td>' for c in row)+'</tr>')
            out.append('</tbody></table></div>');continue
        h=re.match(r'^(#{1,3}) (.*)',line)
        if h:
            flush()
            if in_list:out.append('</ul>');in_list=False
            level=len(h[1]);count+=1;hid=f'{prefix}-{count}'
            out.append(f'<h{level} id="{hid}">{inline(h[2])}</h{level}>')
            if level==2:nav.append((hid,h[2]))
        elif line.startswith('- '):
            flush()
            if not in_list:out.append('<ul>');in_list=True
            out.append('<li>'+inline(line[2:])+'</li>')
        elif not line:
            flush()
            if in_list:out.append('</ul>');in_list=False
        else:
            if in_list:out.append('</ul>');in_list=False
            para.append(line)
        i+=1
    flush()
    if in_list:out.append('</ul>')
    return '\n'.join(out),nav

report,nav=md((ROOT/'진단보고서.md').read_text(encoding='utf-8'),'report')
workbook,_=md((ROOT/'실험·결정워크북.md').read_text(encoding='utf-8'),'work')
png=base64.b64encode((ROOT/'request-intro-00m07s.png').read_bytes()).decode()
def source_link(e):
    src=e['source']
    if src.startswith('https://') or (ROOT/src).is_file():
        return f'<a href="{html.escape(src,quote=True)}">출처</a>'
    return html.escape(src)
evrows=''.join(f'<tr><td><strong>{e["id"]}</strong><br><small>{html.escape(e["kind"])}</small></td><td>{html.escape(e["claim"])}<br><small>{html.escape(e["period"])}</small></td><td>{source_link(e)}<br>{html.escape(e["limitation"])}</td></tr>' for e in D['evidence'])
official=''.join(f'<li><strong>{s["id"]}</strong> · <a href="{html.escape(s["url"],quote=True)}">{html.escape(s["title"])}</a> · 확인 {s["verified_on_kst"]}</li>' for s in D['official_sources'])
navhtml=''.join(f'<a href="#{hid}" data-report-anchor>{html.escape(title)}</a>' for hid,title in nav)
embedded=json.dumps(D,ensure_ascii=False).replace('</','<\\/')
css='''
:root{--paper:#f5f3ee;--card:#fff;--ink:#182c32;--muted:#59696b;--line:#d8dfdb;--teal:#176c61;--gold:#eadba9;--coral:#a94a37}*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:100px}body{margin:0;font:16px/1.8 "Malgun Gothic","Apple SD Gothic Neo",system-ui,sans-serif;color:var(--ink);background:var(--paper)}a{color:var(--teal);text-underline-offset:3px}button,input,textarea,select{font:inherit}button{cursor:pointer;border:1px solid var(--line);background:white;color:var(--ink);border-radius:7px;padding:8px 14px}button:hover,button:focus-visible{border-color:var(--teal);background:#edf6f2}.shell{max-width:1460px;margin:auto;padding:0 35px}.top{position:sticky;top:0;z-index:5;background:rgba(245,243,238,.98);border-bottom:1px solid var(--line)}.top .shell{display:flex;gap:20px;align-items:center;justify-content:space-between;min-height:74px}.brand{font-size:13px;font-weight:800;letter-spacing:.07em}.topnav{display:flex;gap:7px;flex-wrap:wrap}.topnav button[aria-selected=true]{background:var(--ink);color:white;border-color:var(--ink)}.hero{padding:52px 0 35px;border-bottom:1px solid var(--line)}.eyebrow{color:var(--teal);font-size:12px;letter-spacing:.12em;font-weight:800}.hero h1{font-size:clamp(29px,4vw,49px);line-height:1.35;letter-spacing:-.045em;max-width:980px;margin:14px 0 20px}.lead{max-width:970px;font-size:18px;line-height:1.85}.sub{color:var(--muted);font-size:13px}.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:15px;margin:28px 0}.kpi{background:white;border:1px solid var(--line);border-radius:12px;padding:20px}.kpi b{display:block;font-size:32px;line-height:1.35;letter-spacing:-.03em}.kpi span{font-size:13px;color:var(--muted)}.notice{padding:15px 19px;border-left:4px solid var(--teal);background:#e8efea;border-radius:0 8px 8px 0;font-size:14px}.layout{display:grid;grid-template-columns:235px minmax(0,1fr);gap:36px;padding:32px 0 80px}.side{position:sticky;top:100px;align-self:start;max-height:calc(100vh - 125px);overflow:auto;font-size:12px}.side a{display:block;padding:6px 10px;color:var(--muted);text-decoration:none;border-left:2px solid transparent}.side a:hover{border-color:var(--teal);background:#e8efea}.side strong{display:block;margin:0 0 8px 10px}.content{min-width:0}.panel[hidden]{display:none}.paper{background:#fff;border:1px solid var(--line);border-radius:12px;padding:30px 34px;box-shadow:0 6px 25px #18393105}.paper h1{font-size:26px}.paper h2{font-size:24px;line-height:1.5;border-top:2px solid var(--ink);padding-top:23px;margin-top:44px;letter-spacing:-.025em}.paper h2:first-child{margin-top:0}.paper h3{font-size:19px;margin-top:28px}.paper p{margin:17px 0}.paper ul{padding-left:24px}.paper li{margin:6px 0}strong{font-weight:750}.tablewrap{overflow-x:auto;margin:22px 0;border:1px solid var(--line);border-radius:8px}table{width:100%;border-collapse:collapse;font-size:13px;line-height:1.7}th{background:#edf1ed;color:#234a44;text-align:left;font-weight:750}th,td{padding:12px 13px;border-bottom:1px solid var(--line);vertical-align:top}tr:last-child td{border-bottom:0}tbody tr:nth-child(even){background:#fafbf8}small{font-size:11px;color:var(--muted)}.controls{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:15px 0}input[type=search]{width:min(100%,420px);padding:10px 13px;border:1px solid var(--line);border-radius:7px;background:white}.sim{padding:24px;border:1px solid var(--line);background:#eef4ee;border-radius:10px;margin:20px 0}.simgrid{display:grid;grid-template-columns:1fr 1fr 130px;align-items:center;gap:25px}.sim label{display:block}.sim input{width:100%;accent-color:var(--teal)}.net{font-size:36px;font-weight:800;text-align:center}.notes{display:grid;grid-template-columns:1fr 1fr;gap:15px}.note label{font-size:14px;display:block;font-weight:700}.note textarea{display:block;width:100%;min-height:110px;border:1px solid var(--line);border-radius:7px;padding:12px;font-size:14px;margin-top:8px;resize:vertical;background:#fffefa}.notes-actions{margin:18px 0}.flow{display:flex;gap:14px;align-items:center;justify-content:space-around;padding:23px 14px;border:1px solid var(--line);border-radius:10px;background:#fff;margin:20px 0}.flow b{display:block;font-size:25px}.flow small{display:block}.flow .arrow{font-size:25px;color:var(--muted)}figure{margin:25px 0}figure img{max-width:100%;border:1px solid var(--line);border-radius:8px}figcaption{font-size:12px;color:var(--muted);margin-top:7px}.status{font-size:13px;color:var(--teal)}.sortable{cursor:pointer;white-space:nowrap}.footer{border-top:1px solid var(--line);padding:20px 0;color:var(--muted);font-size:12px}.mobile-title{display:none}.evidence-table td:first-child{min-width:130px}.evidence-table td:nth-child(2){min-width:230px}.sample td:first-child{min-width:290px}.sample th:not(:first-child),.sample td:not(:first-child){white-space:nowrap}.tablecaption{font-size:12px;color:var(--muted)}
@media(max-width:1000px){.shell{padding:0 20px}.layout{grid-template-columns:1fr}.side{position:static;max-height:200px;border:1px solid var(--line);border-radius:8px;padding:12px}.paper{padding:22px}.top .shell{padding:12px 20px;gap:10px}.brand{max-width:110px}.topnav button{font-size:12px;padding:7px}.hero{padding-top:30px}.notes{grid-template-columns:1fr}}
@media(max-width:600px){.kpis{grid-template-columns:1fr}.kpi b{font-size:27px}.simgrid{grid-template-columns:1fr}.flow{display:grid;grid-template-columns:1fr 1fr}.flow .arrow{display:none}.lead{font-size:16px}.paper h2{font-size:21px}}
@media print{body{background:white;font-size:10pt;line-height:1.6}.top,.side,.controls,.notes-actions,.sim,.hero,.footer,.flow{display:none!important}.shell{max-width:none;padding:0}.layout{display:block;padding:0}.paper{padding:0;border:0;box-shadow:none}.paper h2{break-before:auto;break-after:avoid;margin-top:24px;font-size:16pt}.paper h3{break-after:avoid}.tablewrap{overflow:visible;break-inside:auto}th,td{font-size:8pt;padding:6px}tr{break-inside:avoid}thead{display:table-header-group}a{color:inherit;text-decoration:none}textarea{border:1px solid #aaa!important}button{display:none}figure{break-inside:avoid}.panel[hidden]{display:none!important}@page{size:A4;margin:17mm 14mm}}
'''
notes_titles=['4주간 계속할 이유와 피하고 싶은 것','선택한 방향과 그 이유','첫 미션·성공조건·타임아웃','댓글0건일 때 기본 미션','이번에 검토할 가설과 반대 결과','실제 제작시간과 부담','고유 참여자·요청·반영 결과','네 편 뒤 계속·수정·보류할 것']
notes=''.join(f'<div class="note"><label for="note{i}">{html.escape(title)}</label><textarea id="note{i}" data-note="{html.escape(title,quote=True)}" placeholder="직접 검토한 내용을 적으세요."></textarea></div>' for i,title in enumerate(notes_titles))
page='''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>김실버 채널 · 심층 진단과 4주 실험</title><style>'''+css+'''</style></head><body>
<header class="top"><div class="shell"><div class="brand">김실버<br>CHANNEL REVIEW · 2026.10.26</div><nav class="topnav" aria-label="보고서 보기"><button data-tab="report" aria-selected="true">심층 진단</button><button data-tab="workbook" aria-selected="false">실험·결정 워크북</button><button data-tab="data" aria-selected="false">근거·영상 데이터</button><button id="print">현재 탭 인쇄</button></nav></div></header>
<div class="shell" id="top"><section class="hero"><div class="eyebrow">STUDIO EVIDENCE × CREATOR INTENT</div><h1>구독자가 줄어드는 이유를,<br>다음 영상을 정하는 근거로.</h1><p class="lead">구독 감소수는 과거보다 줄었습니다. 더 크게 줄어든 것은 신규 구독 유입입니다. 94일의 일반 영상 게시 간격 뒤, 원하는 새 방향으로 재출발하는 상황을 분리해서 봅니다.</p><div class="kpis"><div class="kpi"><b>593 → 18명</b><span>신규 구독 · 이전90일과 최근90일</span></div><div class="kpi"><b>144 → 21명</b><span>구독 감소 · 같은 두90일 비교</span></div><div class="kpi"><b>94일</b><span>7/4→10/6 공개 일반 영상 게시 간격</span></div></div><div class="notice"><strong>해석 변경:</strong> 2026-08-24부터 전체 조회 집계가 바뀌었습니다. 전체 조회·유효 조회·순 시청자·실제 시청시간을 나눠 읽습니다. 리니지 복귀는 기본안에서 제외하고, 주15~20시간의 새 참여형 포맷을 검토합니다.</div><p class="sub">관측일 2026-10-26 KST · 기간 집계 대체로10/24까지 · 실제 관측 / 계산 / 사용자 설명 / 가설 / 미검증을 구분 · 채널599명</p></section>
<div class="layout"><aside class="side"><strong>검토 순서</strong>'''+navhtml+'''<a href="#top" data-switch="workbook">→ 내 선택과 실험 기록</a><a href="#top" data-switch="data">→ 원자료와50개 영상</a></aside><main class="content">
<section class="panel" id="panel-report"><div class="flow" aria-label="순증 변화의 산술 분해"><div><small>이전90일 순증</small><b>+449명</b></div><span class="arrow">→</span><div><small>신규 유입 변화</small><b>−575명</b></div><span class="arrow">+</span><div><small>감소수 완화</small><b>+123명</b></div><span class="arrow">=</span><div><small>최근90일 순증</small><b>−3명</b></div></div><article class="paper">'''+report+'''<section class="sim" aria-labelledby="simtitle"><h3 id="simtitle">구독 순증 시나리오</h3><p>숫자를 바꿔 ‘증가 − 감소’를 확인하세요. 미래 예측이나 목표 달성 확률이 아닌 산술입니다. 시작값은 최근28일입니다.</p><div class="simgrid"><div><label for="gain">신규 증가 <output id="gainOut">10</output>명</label><input id="gain" type="range" min="0" max="50" value="10"></div><div><label for="loss">감소 <output id="lossOut">12</output>명</label><input id="loss" type="range" min="0" max="30" value="12"></div><div><small>순증감</small><div class="net" id="net">−2</div></div></div></section></article></section>
<section class="panel" id="panel-workbook" hidden><article class="paper"><h2>내가 검토한 선택을 남기기</h2><p>아래 메모는 <strong>현재 페이지에만</strong> 남습니다. 닫기 전에 ‘메모 저장’을 누르면 내 컴퓨터에JSON으로 내려받습니다. 계정이나 외부 서비스로 전송하지 않습니다. 텍스트 워크북의 빈 표는 원본 Markdown을 복사해 작성할 수도 있습니다.</p><div class="notes">'''+notes+'''</div><div class="notes-actions"><button id="downloadNotes">메모 저장</button> <span class="status" id="noteStatus" aria-live="polite"></span></div>'''+workbook+'''</article></section>
<section class="panel" id="panel-data" hidden><article class="paper"><h2>근거의 범위와 한계</h2><p>같은 원자료를 여러 번 해석한 것을 독립 검증으로 세지 않았습니다. 아래 표의 ‘출처’는 확인에 사용한 로컬 파일 또는 로그인된Studio입니다. 원자료 파일 링크는 같은 폴더를 유지해야 열립니다. 본문·워크북·아래50개 데이터·모집 화면은HTML 안에 포함되어 있습니다.</p><div class="controls"><button id="downloadData">근거 데이터JSON 저장</button><input id="evidenceSearch" type="search" placeholder="근거·한계에서 찾기" aria-label="근거 검색"></div><div class="tablewrap"><table class="evidence-table"><thead><tr><th>근거</th><th>관측·주장 / 기간</th><th>출처 / 한계</th></tr></thead><tbody id="evidenceRows">'''+evrows+'''</tbody></table></div><h2>최근28일 · 확인한 콘텐츠50개</h2><p>기간2026-09-27~10-24. 유효 조회순 표에서 확인한 상위50개이며 전체 영상 전수가 아닙니다. 조회·유효·순증은 횟수와사람의 다른 단위입니다. 영상 나이·형식·유입 조건을 맞추지 않은 표이므로 전환율 순위로 쓰지 마세요.</p><div class="controls"><input id="videoSearch" type="search" placeholder="영상 제목 검색" aria-label="영상 제목 검색"><span id="rowCount" class="status"></span></div><div class="tablewrap"><table class="sample"><thead><tr><th class="sortable" data-sort="title" tabindex="0">영상 ↕</th><th class="sortable" data-sort="duration" tabindex="0">길이 ↕</th><th class="sortable" data-sort="engaged_views" tabindex="0">유효조회 ↕</th><th class="sortable" data-sort="views" tabindex="0">전체조회 ↕</th><th class="sortable" data-sort="watch_hours" tabindex="0">시청시간h ↕</th><th class="sortable" data-sort="subscriber_net" tabindex="0">구독순증 ↕</th><th class="sortable" data-sort="impressions" tabindex="0">노출 ↕</th><th class="sortable" data-sort="ctr_pct" tabindex="0">CTR% ↕</th></tr></thead><tbody id="videoRows"></tbody></table></div><p class="tablecaption">이50개 표의 채널 총계는 전체45,578·유효12,186으로 표시됐습니다. 별도 상세 표45,540·12,181과 차이를 보존했습니다. 표의 개별 값은 관측 당시 값이며 실시간 동기화하지 않습니다.</p><h2>모집 영상 · 직접 확인한 화면</h2><figure><img src="data:image/png;base64,'''+png+'''" alt="게임을 대신 해드립니다 모집 영상의0분7초 인포그래픽 화면"><figcaption>E15 · 0:07 정지 화면과 제목. 전체 영상의 형식·음성을 검증한 자료가 아닙니다.</figcaption></figure><h2>공식 정의</h2><ul>'''+official+'''</ul><p class="sub">자료 작성과 계산 검토: Codex · 독립된 복수 분석가 검증 미실시 · 콘텐츠 제작·댓글 게시·일정 등록·채널 설정 변경 미실행</p></article></section>
</main></div><footer class="footer">김실버 · 비공개 검토용 로컬 자료 · 분석2026-10-26 · 자동 갱신되지 않음 · 가설의 효과는 실행 후 검증</footer></div>
<script type="application/json" id="auditData">'''+embedded+'''</script><script>
const data=JSON.parse(document.getElementById('auditData').textContent);let activeTab='report';
function switchTab(name){activeTab=name;document.querySelectorAll('.panel').forEach(el=>el.hidden=el.id!=='panel-'+name);document.querySelectorAll('[data-tab]').forEach(el=>el.setAttribute('aria-selected',String(el.dataset.tab===name)));}
document.querySelectorAll('[data-tab]').forEach(el=>el.addEventListener('click',()=>{switchTab(el.dataset.tab);window.scrollTo({top:document.querySelector('.layout').offsetTop-86,behavior:'smooth'});}));
document.querySelectorAll('[data-switch]').forEach(el=>el.addEventListener('click',e=>{e.preventDefault();switchTab(el.dataset.switch);window.scrollTo({top:document.querySelector('.layout').offsetTop-86,behavior:'smooth'});}));
document.querySelectorAll('[data-report-anchor]').forEach(el=>el.addEventListener('click',()=>switchTab('report')));
document.getElementById('print').addEventListener('click',()=>window.print());
function updateSim(){const g=+document.getElementById('gain').value,l=+document.getElementById('loss').value,n=g-l;document.getElementById('gainOut').textContent=g;document.getElementById('lossOut').textContent=l;document.getElementById('net').textContent=(n>0?'+':n<0?'−':'')+Math.abs(n);document.getElementById('net').style.color=n<0?'#a94a37':'#176c61';}document.getElementById('gain').addEventListener('input',updateSim);document.getElementById('loss').addEventListener('input',updateSim);updateSim();
function download(name,payload){const blob=new Blob(['\\ufeff'.replace('\\ufeff','\ufeff')+JSON.stringify(payload,null,2)],{type:'application/json;charset=utf-8'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),500);}
document.getElementById('downloadNotes').addEventListener('click',()=>{const notes={};document.querySelectorAll('[data-note]').forEach(el=>notes[el.dataset.note]=el.value);download('김실버-검토메모.json',{report_date:'2026-10-26',notes});document.getElementById('noteStatus').textContent='메모 파일 다운로드를 요청했습니다. 다운로드한 파일을 확인하세요.';});
document.getElementById('downloadData').addEventListener('click',()=>download('김실버-근거데이터.json',data));
document.getElementById('evidenceSearch').addEventListener('input',e=>{const q=e.target.value.trim().toLowerCase();document.querySelectorAll('#evidenceRows tr').forEach(tr=>tr.hidden=!tr.textContent.toLowerCase().includes(q));});
let sortKey='engaged_views',descending=true;const keys=['title','duration','engaged_views','views','watch_hours','subscriber_net','impressions','ctr_pct'];
function timeSeconds(v){return v.split(':').reverse().reduce((s,n,i)=>s+(+n)*60**i,0)}
function renderVideos(){const q=document.getElementById('videoSearch').value.trim().toLowerCase();const rows=data.content_sample_28d.filter(x=>x.title.toLowerCase().includes(q));rows.sort((a,b)=>{let x=a[sortKey],y=b[sortKey];let c;if(sortKey==='title')c=x.localeCompare(y,'ko');else{if(sortKey==='duration'){x=timeSeconds(x);y=timeSeconds(y);}c=(x??-Infinity)-(y??-Infinity);}return descending?-c:c;});const body=document.getElementById('videoRows');body.replaceChildren();for(const r of rows){const tr=document.createElement('tr');for(const k of keys){const td=document.createElement('td');td.textContent=r[k]===null?'미확인':typeof r[k]==='number'?r[k].toLocaleString('ko-KR',{maximumFractionDigits:1}):r[k];tr.appendChild(td);}body.appendChild(tr);}document.getElementById('rowCount').textContent=rows.length+' / 50개';}
document.querySelectorAll('[data-sort]').forEach(el=>{function apply(){const key=el.dataset.sort;descending=sortKey===key?!descending:true;sortKey=key;renderVideos()}el.addEventListener('click',apply);el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();apply()}})});document.getElementById('videoSearch').addEventListener('input',renderVideos);renderVideos();
</script></body></html>'''
(ROOT/'김실버-심층진단.html').write_text(page,encoding='utf-8')

class Check(HTMLParser):
    def __init__(self):super().__init__();self.ids=[];self.refs=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if 'href' in a:self.refs.append(a['href'])
c=Check();c.feed(page)
assert len(c.ids)==len(set(c.ids)), 'duplicate id'
for href in c.refs:
    if href.startswith('#'):
        if href!='#top':assert href[1:] in c.ids,href
    elif not href.startswith(('http:','https:','data:')):
        assert (ROOT/href).is_file(),href
assert '\ufffd' not in page
assert all(x in page for x in ['593','559,334','94일','18명','요청1건','12,181'])
assert len(D['content_sample_28d'])==50
print(json.dumps({'html':str(ROOT/'김실버-심층진단.html'),'bytes':len(page.encode('utf-8')),'anchors_checked':len(c.ids),'evidence_items':len(D['evidence']),'video_rows':50},ensure_ascii=False,indent=2))
