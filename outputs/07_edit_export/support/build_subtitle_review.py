#!/usr/bin/env python3
# Lifecycle: task-scoped
# Cleanup: remove or promote only after the review-page contract is generalized beyond this run
"""기존 자막 검증 HTML을 전체 컷리스트 기준으로 재생성한다.

템플릿의 화면과 731개 자막/비트 분류는 유지하고, CSV 컷과 겹치는 원본
구간·클립 이름·채택 상태만 다시 계산한다. 같은 원본 구간이 콜드 오픈과
본편에 반복 사용되어도 자막별 사용 시간은 합집합으로 계산해 중복 집계하지
않는다.
"""

from __future__ import annotations

import argparse
import csv
import html as html_lib
import json
import re
from pathlib import Path


def extract_const(html: str, name: str) -> list[dict]:
    match = re.search(rf"^const {re.escape(name)}=(.*);$", html, re.MULTILINE)
    if not match:
        raise ValueError(f"템플릿에서 const {name}을 찾지 못함")
    return json.loads(match.group(1))


def load_cuts(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    cuts = []
    seen_ids: set[str] = set()
    for index, row in enumerate(rows, 1):
        cut_id = row.get("cut_id", "").strip()
        start = float(row["start"])
        end = float(row["end"])
        if not cut_id or cut_id in seen_ids:
            raise ValueError(f"비어 있거나 중복된 cut_id: {cut_id!r}")
        if end <= start:
            raise ValueError(f"0 이하 길이 컷: {cut_id}")
        seen_ids.add(cut_id)
        cuts.append(
            {
                "order": int(row.get("order") or index),
                "cut_id": cut_id,
                "start": start,
                "end": end,
                "label": (row.get("label") or cut_id).strip(),
                "role": (row.get("role") or "").strip(),
            }
        )
    cuts.sort(key=lambda cut: cut["order"])
    if [cut["order"] for cut in cuts] != list(range(1, len(cuts) + 1)):
        raise ValueError("order는 1부터 끊김 없이 이어져야 함")
    missing = [
        f"B{i:02d}"
        for i in range(1, 19)
        if not any(c["cut_id"].startswith(f"B{i:02d}") for c in cuts)
    ]
    if missing:
        raise ValueError(f"전체 편집 컷리스트에 빠진 비트: {', '.join(missing)}")
    return cuts


def merge_intervals(intervals: list[tuple[float, float]]) -> list[tuple[float, float]]:
    merged: list[list[float]] = []
    for start, end in sorted(intervals):
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return [(round(start, 2), round(end, 2)) for start, end in merged]


def apply_cuts(data: list[dict], cuts: list[dict]) -> list[dict]:
    for row in data:
        start = float(row["s"])
        end = float(row["e"])
        overlaps = []
        labels = []
        if end > start:
            for cut in cuts:
                left = max(start, cut["start"])
                right = min(end, cut["end"])
                if right > left:
                    overlaps.append((left, right))
                    if cut["label"] not in labels:
                        labels.append(cut["label"])
        merged = merge_intervals(overlaps)
        row["ov"] = [{"a": left, "b": right} for left, right in merged]
        row["used"] = round(sum(right - left for left, right in merged), 2)
        row["clip"] = " · ".join(labels)
        if merged:
            row["st"] = "sel"
        elif str(row.get("sec", "")).startswith("B"):
            row["st"] = "zone"
        else:
            row["st"] = "out"
    return data


def replace_const(html: str, name: str, value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    updated, count = re.subn(
        rf"^const {re.escape(name)}=.*;$",
        f"const {name}={encoded};",
        html,
        count=1,
        flags=re.MULTILINE,
    )
    if count != 1:
        raise ValueError(f"const {name} 교체 횟수 오류: {count}")
    return updated


def replace_paragraph_body(
    document: str,
    marker: str,
    replacement: str,
) -> str:
    pattern = re.compile(r"<p(?P<attrs>[^>]*)>(?P<body>.*?)</p>", re.DOTALL)
    for match in pattern.finditer(document):
        if marker not in match.group("body"):
            continue
        updated = f"<p{match.group('attrs')}>{replacement}</p>"
        return document[: match.start()] + updated + document[match.end() :]
    raise ValueError(f"교체할 문단을 찾지 못함: {marker}")


def find_paragraph_body(document: str, marker: str) -> str:
    pattern = re.compile(r"<p(?P<attrs>[^>]*)>(?P<body>.*?)</p>", re.DOTALL)
    for match in pattern.finditer(document):
        if marker in match.group("body"):
            return match.group("body")
    raise ValueError(f"찾을 문단이 없음: {marker}")


def replace_one(
    document: str,
    pattern: str,
    replacement: str,
    *,
    flags: int = 0,
    label: str,
) -> str:
    updated, count = re.subn(pattern, replacement, document, count=1, flags=flags)
    if count != 1:
        raise ValueError(f"{label} 교체 횟수 오류: {count}")
    return updated


def validate_assessment(assessment: dict) -> dict:
    required = {
        "overall_score",
        "overall_judgment",
        "thesis",
        "planning_intent",
        "editing_intent",
        "rubric",
        "priorities",
        "beats",
    }
    missing = sorted(required - set(assessment))
    if missing:
        raise ValueError(f"AI 스파인 평가 필수 필드 누락: {', '.join(missing)}")
    expected_ids = [f"B{index:02d}" for index in range(1, 19)]
    beat_ids = [str(beat.get("id", "")) for beat in assessment["beats"]]
    if beat_ids != expected_ids:
        raise ValueError("AI 스파인 평가는 B01~B18을 순서대로 한 번씩 포함해야 함")
    allowed_verdicts = {"유지", "개선", "재설계"}
    for beat in assessment["beats"]:
        if beat.get("verdict") not in allowed_verdicts:
            raise ValueError(f"허용되지 않은 AI 판정: {beat.get('id')} {beat.get('verdict')}")
        score = beat.get("score")
        if not isinstance(score, (int, float)) or not 0 <= score <= 100:
            raise ValueError(f"AI 점수 범위 오류: {beat.get('id')} {score}")
        for field in ("summary", "strengths", "add", "improve", "remove", "decision"):
            if field not in beat:
                raise ValueError(f"AI 비트 평가 필드 누락: {beat.get('id')} {field}")
    return assessment


def html_list(items: list[str], *, ordered: bool = False) -> str:
    tag = "ol" if ordered else "ul"
    rows = "".join(f"<li>{html_lib.escape(str(item))}</li>" for item in items)
    return f"<{tag}>{rows}</{tag}>"


def inject_assessment(
    document: str,
    assessment: dict,
    *,
    version_label: str,
    source_duration_label: str,
    cut_count: int,
    duration_label: str,
) -> str:
    assessment = validate_assessment(assessment)
    planning = assessment["planning_intent"]
    editing = assessment["editing_intent"]
    thesis = html_lib.escape(str(assessment["thesis"]))
    overall = int(round(float(assessment["overall_score"])))
    judgment = html_lib.escape(str(assessment["overall_judgment"]))
    counts = {
        verdict: sum(beat["verdict"] == verdict for beat in assessment["beats"])
        for verdict in ("유지", "개선", "재설계")
    }
    ui = assessment.get("ui", {})
    review_title = html_lib.escape(str(ui.get("review_title", "AI 스파인 재분석")))
    score_label = html_lib.escape(str(ui.get("score_label", "현재 18비트 기획 적합도")))
    note = html_lib.escape(
        str(
            ui.get(
                "note",
                "이 평가는 AI의 선제 제안이며 사용자 승인본이 아닙니다. "
                "점수보다 낮은 점수의 원인과 추가·개선·제거 제안을 먼저 확인합니다.",
            )
        )
    )
    priority_heading = html_lib.escape(str(ui.get("priority_heading", "우선 개선 순서")))
    detail_heading = html_lib.escape(str(ui.get("detail_heading", "비트별 추가·개선·제거 제안")))
    intent_card = f"""
<div class="card intent-card" id="intentReview">
<h2 style="margin-top:0">기획 의도 · 편집 의도</h2>
<div class="intent-thesis"><span>한 줄 기획 의도</span><strong>{thesis}</strong></div>
<div class="intent-grid">
<section><h3>시청자에게 약속하는 것</h3><p>{html_lib.escape(str(planning['viewer_promise']))}</p></section>
<section><h3>영상이 끝까지 답할 질문</h3><p>{html_lib.escape(str(planning['story_question']))}</p></section>
</div>
<h3>인물 변화</h3>
{html_list(planning['character_arc'], ordered=True)}
<div class="intent-grid">
<section><h3>반드시 증명할 것</h3>{html_list(planning['must_prove'])}</section>
<section><h3>이 영상이 아닌 것</h3>{html_list(planning['not_this'])}</section>
</div>
<h3>편집 선택 우선순위</h3>
{html_list(editing['selection_priority'], ordered=True)}
<div class="intent-grid">
<section><h3>리듬 설계</h3>{html_list(editing['rhythm'])}</section>
<section><h3>화면·오디오 원칙</h3>{html_list(editing['audio_visual'])}</section>
</div>
<h3>기본 제거 대상</h3>
{html_list(editing['remove_default'])}
<p class="intent-facts">현재 {version_label}: 원본 {html_lib.escape(source_duration_label)} → <b>{cut_count}컷·{duration_label}</b> · 18비트. 콜드 오픈은 후반 사건을 먼저 약속하고 본문에서는 같은 원본을 반복하지 않습니다.</p>
</div>
""".strip()
    document = replace_one(
        document,
        r'<div class="card">\s*<h2 style="margin-top:0">기획·편집 의도</h2>.*?</div>',
        intent_card,
        flags=re.DOTALL,
        label="상세 기획·편집 의도 카드",
    )

    assessment_card = f"""
<div class="card assessment-card" id="aiSpineReview">
<h2 style="margin-top:0">{review_title}</h2>
<div class="score-summary">
<div class="score-number"><b>{overall}</b><span>/100</span></div>
<div><strong>{score_label}</strong><p>{judgment}</p>
<div class="verdict-counts"><span class="keep">유지 {counts['유지']}</span><span class="improve">개선 {counts['개선']}</span><span class="rebuild">재설계 {counts['재설계']}</span></div></div>
</div>
<p class="note">{note}</p>
<h3>평가 기준</h3><div id="assessmentRubric" class="rubric-grid"></div>
<h3>{priority_heading}</h3><div id="assessmentPriorities"></div>
<h3>18비트 한눈에 보기</h3>
<div class="audit-table-wrap"><table id="assessmentTable"><tr><th>비트</th><th>점수</th><th>판정</th><th>AI 결론</th></tr></table></div>
<h3>{detail_heading}</h3><div id="assessmentDetails"></div>
</div>
""".strip()
    spine_marker = '<div class="card">\n<h2 style="margin-top:0">승인된 이야기 스파인 18비트</h2>'
    if spine_marker not in document:
        raise ValueError("AI 평가 카드 삽입 위치를 찾지 못함")
    document = document.replace(spine_marker, f"{assessment_card}\n\n{spine_marker}", 1)

    assessment_css = """
.intent-thesis{padding:14px;border:1px solid #0ea5e9;border-radius:8px;background:#082f49;margin-bottom:12px}
.intent-thesis span{display:block;color:#7dd3fc;font-size:12px;margin-bottom:4px}.intent-thesis strong{font-size:17px;line-height:1.6}
.intent-card h3,.assessment-card h3{font-size:13px;color:#bae6fd;margin:14px 0 6px}.intent-card ul,.intent-card ol{margin:5px 0 5px 21px;padding:0}
.intent-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}.intent-grid section{background:#172554;border-radius:7px;padding:9px 11px}
.intent-grid section h3{margin-top:0}.intent-grid p{margin:0}.intent-facts{border-top:1px solid #334155;padding-top:10px;color:#cbd5e1}
.score-summary{display:grid;grid-template-columns:120px 1fr;gap:14px;align-items:center}.score-summary p{margin:5px 0}
.score-number{height:100px;border-radius:50%;background:#0c4a6e;display:flex;align-items:center;justify-content:center;flex-direction:column;border:4px solid #38bdf8}
.score-number b{font-size:34px}.score-number span{font-size:12px;color:#bae6fd}.verdict-counts{display:flex;gap:7px;flex-wrap:wrap}
.verdict-counts span,.verdict{border-radius:999px;padding:3px 8px;font-size:11px;font-weight:bold}.keep{background:#14532d;color:#86efac}.improve{background:#713f12;color:#fde68a}.rebuild{background:#7f1d1d;color:#fecaca}
.rubric-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:7px}.rubric-item{background:#172554;border-radius:7px;padding:8px}.rubric-item b{display:block;color:#bae6fd}.rubric-item small{color:#94a3b8}
.priority-item{display:grid;grid-template-columns:28px 90px 1fr;gap:8px;padding:8px;border-bottom:1px solid #334155}.priority-item b{color:#7dd3fc}.priority-item code{color:#f0abfc}
.audit-table-wrap{overflow-x:auto}#assessmentTable td:nth-child(2){font-weight:bold;color:#7dd3fc}#assessmentTable tr[data-target]{cursor:pointer}
.audit-detail{border:1px solid #334155;border-radius:8px;margin:8px 0;background:#111c31}.audit-detail summary{cursor:pointer;padding:10px 12px;font-weight:bold}
.audit-body{padding:0 12px 12px}.audit-body>p{color:#cbd5e1}.audit-cols{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.audit-cols section{border-radius:6px;padding:8px;background:#172554}.audit-cols h4{margin:0 0 5px;color:#bae6fd}.audit-cols ul{margin:0 0 0 18px;padding:0}
.audit-decision{border-top:1px solid #334155;margin-top:9px;padding-top:9px;color:#f0abfc}
@media(max-width:760px){.intent-grid,.audit-cols,.score-summary{grid-template-columns:1fr}.rubric-grid{grid-template-columns:1fr 1fr}.score-number{width:100px}.priority-item{grid-template-columns:28px 70px 1fr}}
""".strip()
    if "</style>" not in document:
        raise ValueError("AI 평가 CSS 삽입 위치를 찾지 못함")
    document = document.replace("</style>", f"{assessment_css}\n</style>", 1)

    client_assessment = {
        "overall_score": assessment["overall_score"],
        "rubric": assessment["rubric"],
        "priorities": assessment["priorities"],
        "beats": assessment["beats"],
        "ui": {
            "add_label": str(ui.get("add_label", "추가")),
            "improve_label": str(ui.get("improve_label", "개선")),
            "remove_label": str(ui.get("remove_label", "제거·축소")),
            "decision_label": str(ui.get("decision_label", "AI 제안")),
        },
    }
    encoded = json.dumps(client_assessment, ensure_ascii=False, separators=(",", ":"))
    assessment_script = r"""
const ASSESSMENT=__ASSESSMENT__;
const assessmentById=Object.fromEntries(ASSESSMENT.beats.map(beat=>[beat.id,beat]));
function esc(value){return String(value).replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]))}
function verdictClass(value){return value==='유지'?'keep':value==='개선'?'improve':'rebuild'}
function listItems(items){return '<ul>'+items.map(item=>'<li>'+esc(item)+'</li>').join('')+'</ul>'}
function buildAssessment(){
 document.getElementById('assessmentRubric').innerHTML=ASSESSMENT.rubric.map(item=>'<div class="rubric-item"><b>'+esc(item.name)+' · '+esc(item.weight)+'점</b><small>'+esc(item.description)+'</small></div>').join('');
 document.getElementById('assessmentPriorities').innerHTML=ASSESSMENT.priorities.map(item=>'<div class="priority-item"><b>'+esc(item.rank)+'</b><code>'+esc(item.beats.join('·'))+'</code><span>'+esc(item.action)+'</span></div>').join('');
 const table=document.getElementById('assessmentTable');
 ASSESSMENT.beats.forEach(beat=>{
  const row=document.createElement('tr');row.dataset.target='audit_'+beat.id;
  row.innerHTML='<td>'+esc(beat.id)+'</td><td>'+esc(beat.score)+'</td><td><span class="verdict '+verdictClass(beat.verdict)+'">'+esc(beat.verdict)+'</span></td><td>'+esc(beat.summary)+'</td>';
  row.onclick=()=>document.getElementById(row.dataset.target).scrollIntoView({behavior:'smooth',block:'center'});table.appendChild(row);
 });
 document.getElementById('assessmentDetails').innerHTML=ASSESSMENT.beats.map(beat=>'<details class="audit-detail" id="audit_'+esc(beat.id)+'" '+(beat.verdict==='재설계'?'open':'')+'><summary>'+esc(beat.id)+' · '+esc(beat.score)+'점 · <span class="verdict '+verdictClass(beat.verdict)+'">'+esc(beat.verdict)+'</span> — '+esc(beat.summary)+'</summary><div class="audit-body"><p><b>강점</b>'+listItems(beat.strengths)+'</p><div class="audit-cols"><section><h4>'+esc(ASSESSMENT.ui.add_label)+'</h4>'+listItems(beat.add)+'</section><section><h4>'+esc(ASSESSMENT.ui.improve_label)+'</h4>'+listItems(beat.improve)+'</section><section><h4>'+esc(ASSESSMENT.ui.remove_label)+'</h4>'+listItems(beat.remove)+'</section></div><div class="audit-decision"><b>'+esc(ASSESSMENT.ui.decision_label)+':</b> '+esc(beat.decision)+'</div></div></details>').join('');
}
function decorateSpine(){
 const header=document.querySelector('#spine tr');
 ['AI 점수','AI 판정'].forEach(label=>{const th=document.createElement('th');th.textContent=label;header.appendChild(th)});
 document.querySelectorAll('#spine tr.spn').forEach(row=>{const beat=assessmentById[row.cells[0].textContent];if(!beat)return;const score=document.createElement('td');score.textContent=beat.score;const verdict=document.createElement('td');verdict.innerHTML='<span class="verdict '+verdictClass(beat.verdict)+'">'+esc(beat.verdict)+'</span>';row.append(score,verdict)});
}
""".strip().replace("__ASSESSMENT__", encoded)
    init_marker = "buildSpine();render();"
    if init_marker not in document:
        raise ValueError("AI 평가 스크립트 삽입 위치를 찾지 못함")
    return document.replace(
        init_marker,
        f"{assessment_script}\nbuildAssessment();buildSpine();decorateSpine();render();",
        1,
    )


def inject_player(document: str, media_src: str) -> str:
    media_src_escaped = html_lib.escape(media_src, quote=True)
    player_css = """
.player-card{position:static;border:1px solid #334155;box-shadow:0 8px 24px #020617aa}
.player-card video{display:block;width:100%;max-height:56vh;background:#020617;border-radius:8px}
.player-controls{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-top:10px}
.player-controls button,.player-controls select{background:#334155;color:var(--txt);border:1px solid #475569;border-radius:6px;padding:7px 10px}
.player-controls button{cursor:pointer}.player-controls button.primary{background:#0284c7;border-color:#0284c7}
.player-controls select{flex:1;min-width:300px}.player-meta{margin-top:8px;color:#bae6fd;font-family:monospace}
.player-status{margin-top:4px;color:#94a3b8;font-size:12px}.row[data-seek]{cursor:pointer}
""".strip()
    if "</style>" not in document:
        raise ValueError("플레이어 CSS 삽입 위치를 찾지 못함")
    document = document.replace("</style>", f"{player_css}\n</style>", 1)

    player_html = f"""
<div class="card player-card" id="reviewPlayer">
<h2 style="margin-top:0">원본 재생 · 컷 순서 검토</h2>
<video id="sourceVideo" controls preload="metadata" playsinline src="{media_src_escaped}"></video>
<div class="player-controls">
<button id="prevCut" type="button">이전 컷</button>
<select id="cutSelect" aria-label="검토할 컷"></select>
<button id="nextCut" type="button">다음 컷</button>
<button id="playCut" type="button" class="primary">선택 컷 재생</button>
<button id="playSequence" type="button">전체 순서 재생</button>
<button id="stopPlayback" type="button">정지</button>
</div>
<div class="player-meta" id="cutMeta"></div>
<div class="player-status" id="playerStatus" aria-live="polite">원본 메타데이터를 불러오는 중입니다.</div>
<p class="note">각 컷은 원본 시각을 직접 참조합니다. 전체 순서 재생은 컷 끝에서 다음 컷의 원본 시각으로 이동합니다. 자막 행을 누르면 해당 원본 시각으로 이동합니다.</p>
</div>
""".strip()
    bar_marker = '<div class="bar">'
    if bar_marker not in document:
        raise ValueError("플레이어 HTML 삽입 위치를 찾지 못함")
    document = document.replace(bar_marker, f"{player_html}\n\n{bar_marker}", 1)

    old_row = "return '<div class=\"row '+cls+'\" id=\"r'+r.i+'\">"
    new_row = "return '<div class=\"row '+cls+'\" id=\"r'+r.i+'\" data-seek=\"'+r.s+'\">"
    if old_row not in document:
        raise ValueError("자막 행 재생 위치 삽입점을 찾지 못함")
    document = document.replace(old_row, new_row, 1)

    player_script = r"""
const sourceVideo=document.getElementById('sourceVideo');
const cutSelect=document.getElementById('cutSelect');
const cutMeta=document.getElementById('cutMeta');
const playerStatus=document.getElementById('playerStatus');
const sequenceButton=document.getElementById('playSequence');
let currentCutIndex=0,sequencePlaying=false;
function cutText(c){return c.order+'/'+CUTS.length+' · '+c.cut_id+' · '+fmt(c.start)+'–'+fmt(c.end)+' · '+c.label}
function updateCutUi(){
 const c=CUTS[currentCutIndex];
 cutSelect.value=String(currentCutIndex);
 cutMeta.textContent=cutText(c);
 sequenceButton.classList.toggle('primary',sequencePlaying);
 sequenceButton.textContent=sequencePlaying?'전체 순서 재생 중':'전체 순서 재생';
}
function playVideo(){
 const result=sourceVideo.play();
 if(result&&result.catch)result.catch(err=>{playerStatus.textContent='재생 실패: '+err.message});
}
function selectCut(index,autoplay=false){
 currentCutIndex=Math.max(0,Math.min(CUTS.length-1,index));
 const c=CUTS[currentCutIndex];
 sourceVideo.currentTime=c.start;
 playerStatus.textContent='선택: '+cutText(c);
 updateCutUi();
 if(autoplay)playVideo();
}
function seekSource(seconds){
 sequencePlaying=false;
 sourceVideo.pause();
 sourceVideo.currentTime=seconds;
 playerStatus.textContent='원본 '+fmt(seconds)+'로 이동했습니다.';
 updateCutUi();
}
CUTS.forEach((c,index)=>{
 const option=document.createElement('option');
 option.value=String(index);option.textContent=cutText(c);cutSelect.appendChild(option);
});
cutSelect.onchange=()=>{sequencePlaying=false;sourceVideo.pause();selectCut(Number(cutSelect.value))};
document.getElementById('prevCut').onclick=()=>{sequencePlaying=false;sourceVideo.pause();selectCut(currentCutIndex-1)};
document.getElementById('nextCut').onclick=()=>{sequencePlaying=false;sourceVideo.pause();selectCut(currentCutIndex+1)};
document.getElementById('playCut').onclick=()=>{sequencePlaying=false;selectCut(currentCutIndex,true)};
sequenceButton.onclick=()=>{sequencePlaying=true;selectCut(currentCutIndex,true)};
document.getElementById('stopPlayback').onclick=()=>{sequencePlaying=false;sourceVideo.pause();selectCut(currentCutIndex)};
sourceVideo.addEventListener('loadedmetadata',()=>{playerStatus.textContent='원본 로드 완료 · '+fmt(sourceVideo.duration);updateCutUi()});
sourceVideo.addEventListener('error',()=>{playerStatus.textContent='원본을 불러오지 못했습니다. 페이지와 원본의 상대 경로를 확인하세요.'});
sourceVideo.addEventListener('timeupdate',()=>{
 const c=CUTS[currentCutIndex];
 if(sourceVideo.currentTime<c.end-0.03)return;
 if(sequencePlaying&&currentCutIndex<CUTS.length-1){selectCut(currentCutIndex+1,true);return}
 sourceVideo.pause();sequencePlaying=false;updateCutUi();
 playerStatus.textContent='컷 끝: '+cutText(c);
});
list.addEventListener('click',event=>{
 if(event.target.tagName==='INPUT'||event.target.tagName==='BUTTON')return;
 const row=event.target.closest('.row[data-seek]');
 if(row)seekSource(Number(row.dataset.seek));
});
selectCut(0);
""".strip()
    init_marker = "buildSpine();render();"
    if init_marker not in document:
        raise ValueError("플레이어 스크립트 삽입 위치를 찾지 못함")
    return document.replace(init_marker, f"{player_script}\n{init_marker}", 1)


def build(
    template: Path,
    cutlist: Path,
    output: Path,
    *,
    page_name: str = "전체 편집",
    version_label: str = "v1",
    source_duration_label: str = "원본 전체",
    media_src: str | None = None,
    assessment: dict | None = None,
) -> dict:
    if output.exists():
        raise FileExistsError(f"출력 파일이 이미 존재함(덮어쓰기 금지): {output}")
    html = template.read_text(encoding="utf-8")
    cuts = load_cuts(cutlist)
    data = apply_cuts(extract_const(html, "DATA"), cuts)
    beats = extract_const(html, "BEATS")
    for beat in beats:
        beat["repr"] = (
            f"FULL {version_label} ✅"
            if str(beat.get("id", "")).startswith("B")
            else ""
        )
        if beat.get("id") == "B10":
            beat["sum"] = "시청자개입 — 살아있는 공략이에요? (실제 녹음 발화만 사용)"

    raw_duration = round(sum(cut["end"] - cut["start"] for cut in cuts), 2)
    selected_rows = sum(row["st"] == "sel" for row in data)
    selected_beats = sorted(
        {
            row["sec"]
            for row in data
            if row["st"] == "sel" and str(row["sec"]).startswith("B")
        }
    )

    duration_minutes = int(raw_duration // 60)
    duration_seconds = raw_duration - duration_minutes * 60
    duration_label = f"{duration_minutes}분 {duration_seconds:05.2f}초"
    version_slug = re.sub(r"[^0-9A-Za-z_-]+", "_", version_label).strip("_") or "current"

    html = replace_one(
        html,
        r"<title>.*?</title>",
        f"<title>{page_name} 검증 {version_label} — 페이퍼 에디트</title>",
        label="title",
    )
    html = replace_one(
        html,
        r"<h1>.*?</h1>",
        f"<h1>{page_name} 검증 {version_label} — 자막 × 18비트 페이퍼 에디트</h1>",
        label="h1",
    )
    intent_source = find_paragraph_body(html, "3막 ")
    intent_prefix = intent_source.split("전체 ", 1)[0].rstrip()
    intent_body = (
        f"{intent_prefix}\n전체 {version_label}: 원본 {source_duration_label}를 "
        f"<b>{len(cuts)}컷·{duration_label}</b>로 구성했고 18비트를 모두 포함했습니다.<br>"
        "미선택 자막은 전체 편집에서 제외된 원본 구간입니다. "
        "콜드 오픈은 후반 원본 일부를 본편보다 먼저 사용합니다."
    )
    html = replace_paragraph_body(html, "3막 ", intent_body)
    html = replace_paragraph_body(
        html,
        "✅ =",
        f"행을 클릭하면 아래 해당 구간으로 이동합니다. ✅ = 전체 편집 {version_label}에 포함됨.",
    )
    html = html.replace(
        "블록 끝은 다음 자막 시작으로 근사한 점선)",
        "블록 끝은 다음 자막 시작으로 근사한 점선 · 반복 사용 구간의 초록 바는 합집합으로 표시)",
    )
    html = replace_const(html, "DATA", data)
    html = replace_const(html, "BEATS", beats)
    cuts_json = json.dumps(cuts, ensure_ascii=False, separators=(",", ":"))
    if re.search(r"^const CUTS=", html, flags=re.MULTILINE):
        html = replace_const(html, "CUTS", cuts)
    else:
        html = html.replace(
            "DATA.forEach(r=>r.cur=(r.st==='sel'));",
            f"const CUTS={cuts_json};\nDATA.forEach(r=>r.cur=(r.st==='sel'));",
        )
    html = replace_one(
        html,
        r"return \{base:'[^']*'(?:,cuts:CUTS)?",
        f"return {{base:'full_18beat_{version_slug}',cuts:CUTS",
        label="검토 결과 기준 버전",
    )
    html = replace_one(
        html,
        r"## 자막 검토 결과 \([^\n']*기준\)",
        f"## 자막 검토 결과 (전체 {version_label} 기준)",
        label="검토 결과 제목",
    )
    html = replace_one(
        html,
        r"subtitle_review_result_full_[^']+\.json|subtitle_review_result_v\d+\.json",
        f"subtitle_review_result_full_{version_slug}.json",
        label="검토 결과 파일명",
    )
    if media_src:
        html = inject_player(html, media_src)
    if assessment:
        html = inject_assessment(
            html,
            assessment,
            version_label=version_label,
            source_duration_label=source_duration_label,
            cut_count=len(cuts),
            duration_label=duration_label,
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8", newline="\n")
    return {
        "cues": len(data),
        "cuts": len(cuts),
        "selected_rows": selected_rows,
        "selected_beats": len(selected_beats),
        "duration": raw_duration,
        "assessment_beats": len(assessment["beats"]) if assessment else 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("template", type=Path)
    parser.add_argument("cutlist", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--page-name", default="전체 편집")
    parser.add_argument("--version-label", default="v1")
    parser.add_argument("--source-duration-label", default="원본 전체")
    parser.add_argument("--media-src", help="출력 HTML에서 원본 영상을 가리키는 상대 또는 절대 URL")
    parser.add_argument("--assessment", type=Path, help="AI 스파인 평가 JSON")
    args = parser.parse_args()
    assessment = None
    if args.assessment:
        assessment = json.loads(args.assessment.read_text(encoding="utf-8"))
    stats = build(
        args.template,
        args.cutlist,
        args.output,
        page_name=args.page_name,
        version_label=args.version_label,
        source_duration_label=args.source_duration_label,
        media_src=args.media_src,
        assessment=assessment,
    )
    print(
        "[subtitle-review] "
        f"자막 {stats['cues']}개, 컷 {stats['cuts']}개, "
        f"선택 자막 {stats['selected_rows']}개, 비트 {stats['selected_beats']}개, "
        f"재생 길이 {stats['duration']:.2f}초"
    )
    print(f"[subtitle-review] 완료: {args.output}")


if __name__ == "__main__":
    main()
