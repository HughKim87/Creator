import html, re
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, Image
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parent
pdfmetrics.registerFont(TTFont('Malgun','C:/Windows/Fonts/malgun.ttf'))
pdfmetrics.registerFont(TTFont('Malgun-Bold','C:/Windows/Fonts/malgunbd.ttf'))
pdfmetrics.registerFontFamily('Malgun',normal='Malgun',bold='Malgun-Bold',italic='Malgun',boldItalic='Malgun-Bold')
INK=colors.HexColor('#182c32');TEAL=colors.HexColor('#176c61');LINE=colors.HexColor('#d8dfdb')
PAGEW,PAGEH=A4;WIDTH=PAGEW-32*mm
styles={
 'body':ParagraphStyle('body',fontName='Malgun',fontSize=9.2,leading=15.1,textColor=INK,spaceAfter=8,wordWrap='CJK',allowWidows=0,allowOrphans=0),
 'h2':ParagraphStyle('h2',fontName='Malgun-Bold',fontSize=15,leading=21,textColor=INK,spaceBefore=18,spaceAfter=11,keepWithNext=True,wordWrap='CJK'),
 'h3':ParagraphStyle('h3',fontName='Malgun-Bold',fontSize=11.2,leading=17,textColor=TEAL,spaceBefore=11,spaceAfter=7,keepWithNext=True,wordWrap='CJK'),
 'cell':ParagraphStyle('cell',fontName='Malgun',fontSize=7.4,leading=11.6,textColor=INK,wordWrap='CJK'),
 'head':ParagraphStyle('head',fontName='Malgun-Bold',fontSize=7.6,leading=11.8,textColor=TEAL,wordWrap='CJK'),
 'cover':ParagraphStyle('cover',fontName='Malgun-Bold',fontSize=29,leading=42,textColor=INK,wordWrap='CJK'),
 'subtitle':ParagraphStyle('subtitle',fontName='Malgun',fontSize=12,leading=21,textColor=TEAL,wordWrap='CJK',spaceAfter=16),
 'small':ParagraphStyle('small',fontName='Malgun',fontSize=8,leading=12.8,textColor=colors.HexColor('#59696b'),wordWrap='CJK',spaceAfter=8),
}

def clean(s):
    return s.replace('−','-').replace('–','-').replace('—','-').replace('\u2011','-').replace('😎','')

def rich(s):
    s=html.escape(clean(s))
    def link(m):
        label,url=m[1],html.unescape(m[2])
        if url.startswith('https://'):
            return f'<link href="{html.escape(url,quote=True)}" color="#176c61">{label}</link>'
        return label
    s=re.sub(r'\[([^\]]+)\]\(([^\s)]+)\)',link,s)
    return re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',s)

def P(s,style='body'):return Paragraph(rich(s),styles[style])

def render_md(source):
    result=[];para=[];lines=source.splitlines();i=0
    def flush():
        if para:result.append(P(' '.join(para)));para.clear()
    while i<len(lines):
        line=lines[i].strip()
        if line.startswith('|'):
            flush();rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                cells=[c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?',c) for c in cells):rows.append(cells)
                i+=1
            n=len(rows[0]);assert all(len(r)==n for r in rows)
            if n==3:ratios=[.27,.32,.41]
            elif n==4:ratios=[.21,.22,.22,.35]
            elif n==5:ratios=[.17,.22,.24,.24,.13]
            elif n==6:ratios=[.24,.15,.15,.15,.15,.16]
            elif n==7:ratios=[.10,.20,.16,.17,.14,.13,.10]
            else:ratios=[1/n]*n
            cells=[[P(c,'head' if r==0 else 'cell') for c in row] for r,row in enumerate(rows)]
            t=Table(cells,colWidths=[WIDTH*x for x in ratios],repeatRows=1,hAlign='LEFT')
            t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#edf1ed')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#fafbf8')]),('LINEBELOW',(0,0),(-1,-1),.4,LINE),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
            result.extend([Spacer(1,5),t,Spacer(1,10)]);continue
        m=re.match(r'^(#{1,3}) (.*)',line)
        if m:
            flush()
            if len(m[1])>1:result.append(P(m[2],'h2' if len(m[1])==2 else 'h3'))
        elif line.startswith('- '):
            flush();result.append(P('• '+line[2:]))
        elif line:
            para.append(line)
        else:flush()
        i+=1
    flush();return result

def draw_page(c,doc):
    c.saveState();c.setStrokeColor(LINE);c.line(16*mm,17*mm,PAGEW-16*mm,17*mm)
    c.setFont('Malgun',7);c.setFillColor(colors.HexColor('#59696b'))
    c.drawString(16*mm,12*mm,'김실버 | 비공개 검토 자료 | 2026-10-26')
    c.drawRightString(PAGEW-16*mm,12*mm,str(doc.page))
    if doc.page>1:c.drawString(16*mm,PAGEH-12*mm,doc.title)
    c.restoreState()

def make_pdf(mdfile,outfile,title,subtitle,summary):
    doc=SimpleDocTemplate(str(ROOT/outfile),pagesize=A4,rightMargin=16*mm,leftMargin=16*mm,topMargin=21*mm,bottomMargin=23*mm,title=title,author='Codex - Kim Silver channel review')
    story=[Spacer(1,23*mm),P('KIM SILVER / CHANNEL REVIEW','subtitle'),P(title,'cover'),Spacer(1,10*mm),P(subtitle,'subtitle'),Spacer(1,7*mm),P(summary),Spacer(1,8*mm)]
    coverrows=[[P('593 → 18명','h3'),P('144 → 21명','h3'),P('94일','h3')],[P('신규 구독 획득','small'),P('구독 감소','small'),P('일반 영상 게시 간격','small')]]
    cover=Table(coverrows,colWidths=[WIDTH/3]*3)
    cover.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#edf1ed')),('LEFTPADDING',(0,0),(-1,-1),12),('TOPPADDING',(0,0),(-1,-1),10),('VALIGN',(0,0),(-1,-1),'TOP')]))
    story.extend([cover,Spacer(1,12*mm),P('두90일: 2026-04-28~07-26 / 2026-07-27~10-24. 기간·분모·집계차이와 미검증 항목은 본문에 구분했다. 숫자는 관측 당시 값이며 자동 갱신되지 않는다.','small'),P('HTML판에는 검색 가능한 영상50개, 근거 목록, 검토 메모, 순증 시나리오가 포함된다. 이PDF는 읽기·인쇄용이다.','small'),PageBreak()])
    story.extend(render_md((ROOT/mdfile).read_text(encoding='utf-8')))
    if '보고서' in mdfile:
        story.extend([P('직접 확인한 모집 화면','h2'),P('모집 영상0분7초의 정지 화면. 제목·설명과 함께 검토했으며, 전체 음성·영상 형식의 검증을 대신하지 않는다.','small'),Image(str(ROOT/'request-intro-00m07s.png'),width=WIDTH,height=WIDTH*340/760)])
    doc.build(story,onFirstPage=draw_page,onLaterPages=draw_page)
    r=PdfReader(str(ROOT/outfile));contents='\n'.join(p.extract_text() or '' for p in r.pages)
    assert '김실버' in contents and '593' in contents and '94일' in contents
    assert all((p.extract_text() or '').strip() for p in r.pages)
    return dict(file=outfile,pages=len(r.pages),text_characters=len(contents))

results=[]
results.append(make_pdf('진단보고서.md','김실버-채널심층진단.pdf','김실버 채널 심층 진단','구독 감소의 구조와, 원하는 새 방향으로 이어갈 방법','신규 구독 유입의 감소,94일 일반 영상 게시 간격,집계 정의 변경을 분리한다. 리니지 복귀를 전제로 삼지 않고 참여형 게임 시리즈의 다음 선택을 검토한다.'))
results.append(make_pdf('실험·결정워크북.md','김실버-4주실험워크북.pdf','4주 실험·결정 워크북','댓글이 없어도 다음 편을 정하고, 실제 결과로 판단하기','주15~20시간 안에서 한 가지 약속을 정한다. 미션·타임아웃·참여 기본값·작업시간·게시후7일 지표를 기록하고,네 편 뒤 계속·수정·보류를 결정한다.'))
import json
(ROOT/'pdf-checks.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(results,ensure_ascii=False,indent=2))
