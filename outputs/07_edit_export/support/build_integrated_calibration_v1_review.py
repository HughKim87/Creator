#!/usr/bin/env python3
# Lifecycle: task-scoped
# Cleanup: keep through user direction review; remove after integrated-calibration-v1 is approved or rejected.
"""Build the local blind-playback review page for integrated-calibration-v1."""

from __future__ import annotations

import argparse
import csv
import html
import json
import subprocess
from collections import OrderedDict
from fractions import Fraction
from pathlib import Path


SEQUENCE_PURPOSES = {
    "CAL_A_훅과첫진입": "E08의 위협 등장·허세·즉시 붕괴를 한 번의 진행 화면으로 약속한 뒤 E01→E02로 리셋",
    "CAL_B_빛변화와코미디": "E10의 암흑→전원→밝아짐→혼자 생쇼로 중간 사건의 긴장과 이완을 검증",
    "CAL_C_적응과공포잔존": "E11의 적응·공포 잔존을 E14의 부인·중단·최종 자백으로 회수",
}


def load_rows(path: Path) -> list[dict[str, object]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        source = list(csv.DictReader(handle))
    if not source:
        raise ValueError("empty calibration cutlist")
    rows = []
    for item in source:
        rows.append(
            {
                "sequence": item["sequence"],
                "order": int(item["order"]),
                "cut_id": item["cut_id"],
                "start": float(item["start"]),
                "end": float(item["end"]),
                "label": item["label"],
                "role": item["role"],
                "timeline_start_raw": item["timeline_start"],
                "video_track": int(item["video_track"]),
                "audio_mode": item["audio_mode"],
            }
        )
    return rows


def load_decisions(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        decisions = list(csv.DictReader(handle))
    if not decisions:
        raise ValueError("empty microbeat decisions")
    return decisions


def probe_fps(source: Path, ffprobe: Path) -> Fraction:
    result = subprocess.run(
        [
            str(ffprobe),
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=avg_frame_rate",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(source),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    fps = Fraction(result.stdout.strip())
    if fps <= 0:
        raise ValueError(f"invalid fps: {fps}")
    return fps


def add_timeline(rows: list[dict[str, object]], fps: Fraction) -> list[dict[str, object]]:
    grouped: OrderedDict[str, list[dict[str, object]]] = OrderedDict()
    for item in rows:
        grouped.setdefault(str(item["sequence"]), []).append(dict(item))
    result = []
    fps_float = float(fps)
    for sequence_rows in grouped.values():
        cursor = 0
        for item in sorted(sequence_rows, key=lambda row: int(row["order"])):
            start = float(item["start"])
            end = float(item["end"])
            duration_frames = round(end * fps_float) - round(start * fps_float)
            raw = str(item["timeline_start_raw"])
            timeline_start = round(float(raw) * fps_float) if raw else cursor
            timeline_end = timeline_start + duration_frames
            cursor = max(cursor, timeline_end)
            item["timeline_start"] = timeline_start / fps_float
            item["timeline_end"] = timeline_end / fps_float
            item.pop("timeline_start_raw", None)
            result.append(item)
    return result


def sequence_cards(rows: list[dict[str, object]]) -> str:
    grouped: OrderedDict[str, list[dict[str, object]]] = OrderedDict()
    for item in rows:
        grouped.setdefault(str(item["sequence"]), []).append(item)
    cards = []
    for name, items in grouped.items():
        duration = max(float(item["timeline_end"]) for item in items)
        linked = sum(item["audio_mode"] == "linked" for item in items)
        overlays = sum(item["audio_mode"] == "none" for item in items)
        cards.append(
            f'<button class="sequence-card" data-sequence="{html.escape(name, quote=True)}">'
            f'<b>{html.escape(name)}</b><span>{duration:.1f}초 · 기본 {linked}컷 · V2 {overlays}컷</span>'
            f'<small>{html.escape(SEQUENCE_PURPOSES[name])}</small></button>'
        )
    return "\n".join(cards)


def cut_tables(rows: list[dict[str, object]]) -> str:
    grouped: OrderedDict[str, list[dict[str, object]]] = OrderedDict()
    for item in rows:
        grouped.setdefault(str(item["sequence"]), []).append(item)
    sections = []
    for name, items in grouped.items():
        body = []
        for item in sorted(items, key=lambda row: (float(row["timeline_start"]), int(row["video_track"]))):
            track = "V2 무음 화면" if item["audio_mode"] == "none" else "V1+A1/A2"
            body.append(
                "<tr>"
                f'<td>{html.escape(str(item["cut_id"]))}</td>'
                f'<td>{float(item["timeline_start"]):.3f}–{float(item["timeline_end"]):.3f}</td>'
                f'<td>{float(item["start"]):.3f}–{float(item["end"]):.3f}</td>'
                f'<td>{track}</td><td>{html.escape(str(item["role"]))}</td>'
                "</tr>"
            )
        sections.append(
            f'<section class="cut-section explain" data-table="{html.escape(name, quote=True)}">'
            f'<h2>{html.escape(name)}</h2><div class="table-wrap"><table><thead><tr>'
            '<th>컷</th><th>편집본</th><th>원본</th><th>트랙</th><th>이야기 기능</th>'
            f'</tr></thead><tbody>{"".join(body)}</tbody></table></div></section>'
        )
    return "\n".join(sections)


def decision_table(decisions: list[dict[str, str]]) -> str:
    action_labels = {
        "redesign": "재설계",
        "compress": "개선·압축",
        "radio": "유지·개선",
        "improve": "개선",
        "keep": "유지",
    }
    body = []
    for item in decisions:
        body.append(
            "<tr>"
            f'<td>{html.escape(item["beat_id"])}</td>'
            f'<td><b>{action_labels.get(item["action"], item["action"])}</b></td>'
            f'<td>{html.escape(item["story_function"])}</td>'
            f'<td>{html.escape(item["reason"])}</td>'
            f'<td>{html.escape(item["removed_ranges"] or "-")}</td>'
            "</tr>"
        )
    return "".join(body)


def build_document(
    rows: list[dict[str, object]],
    decisions: list[dict[str, str]],
    media_src: str,
    fps: Fraction,
) -> str:
    timeline_rows = add_timeline(rows, fps)
    data = json.dumps(timeline_rows, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    cards = sequence_cards(timeline_rows)
    tables = cut_tables(timeline_rows)
    actions = decision_table(decisions)
    media = html.escape(media_src, quote=True)
    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>백룸 통합 대표 캘리브레이션 v1</title>
<style>
:root{{--bg:#07111f;--card:#101d31;--line:#2a405f;--txt:#e8f0fb;--muted:#9db0ca;--accent:#38bdf8;--ok:#86efac;--warn:#fde68a}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--txt);font-family:system-ui,"Malgun Gothic",sans-serif;line-height:1.55}}
main{{max-width:1180px;margin:auto;padding:28px 18px 70px}}h1{{font-size:28px;margin:0 0 8px}}h2{{font-size:20px}}.lede{{color:var(--muted);margin:0 0 20px}}
.notice,.thesis,.panel{{border:1px solid var(--line);background:var(--card);padding:14px 16px;border-radius:11px;margin:14px 0}}.notice{{border-color:#7c3aed;background:#2e1065}}.thesis{{border-color:#0ea5e9}}.thesis p{{font-size:18px;margin:5px 0}}
.sequence-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:16px}}.sequence-card{{text-align:left;border:1px solid var(--line);background:var(--card);color:var(--txt);border-radius:10px;padding:13px;cursor:pointer}}
.sequence-card.active{{border-color:var(--accent);box-shadow:0 0 0 2px #38bdf833}}.sequence-card b,.sequence-card span,.sequence-card small{{display:block}}.sequence-card span{{color:#bae6fd;margin:5px 0}}.sequence-card small{{color:var(--muted)}}
.player-card{{position:static;border:1px solid var(--line);background:var(--card);border-radius:12px;padding:14px;margin-bottom:18px}}.stage{{position:relative;aspect-ratio:16/9;background:#020617;border-radius:9px;overflow:hidden}}.stage video{{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;background:#020617}}#overlayVideo{{display:none;z-index:2}}
.controls{{display:flex;gap:8px;flex-wrap:wrap;margin-top:11px}}button.control{{border:1px solid #496482;background:#203552;color:var(--txt);padding:8px 12px;border-radius:7px;cursor:pointer}}button.primary{{background:#0369a1;border-color:#0ea5e9}}button.blind{{background:#4c1d95;border-color:#8b5cf6}}
.meta{{font-family:ui-monospace,Consolas,monospace;color:#bae6fd;margin-top:9px}}.status{{color:var(--muted);font-size:13px;margin-top:4px}}.blind-active .explain{{display:none!important}}.blind-label{{display:none;color:var(--warn);font-weight:700;margin:10px 0}}.blind-active .blind-label{{display:block}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}}.grid section{{background:#0b1728;border:1px solid var(--line);border-radius:9px;padding:12px}}.grid h3{{margin:0 0 7px;font-size:15px;color:#bae6fd}}.grid ul{{margin:0;padding-left:20px}}
.cut-section{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;margin-top:12px;display:none}}.cut-section.active{{display:block}}.table-wrap{{overflow:auto}}table{{border-collapse:collapse;width:100%;font-size:13px}}th,td{{padding:8px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}th{{color:#bae6fd}}.recommend{{border-color:#22c55e}}.recommend b{{color:var(--ok)}}
@media(max-width:820px){{.sequence-grid,.grid{{grid-template-columns:1fr}}}}
</style></head><body><main>
<h1>백룸 통합 대표 캘리브레이션 v1</h1>
<p class="lede">전체 편집이 아니라 초반·중간·후반의 최소 대표 표본입니다. AI 선검증 뒤 방향 한 번만 판단하기 위한 패키지입니다.</p>
<div class="notice"><b>승격 잠금:</b> 사용자 방향 승인 전에는 전체 편집·approved_baseline·current_deliverable로 확장하지 않습니다. MP4도 생성하지 않았습니다.</div>
<section class="thesis explain"><h2>기획 의도</h2><p>영화로 보던 백룸은, 직접 헤매고 규칙을 배우며 익숙해질수록 무서움은 줄어도 끝내 긴장이 남는 체험이었다.</p><ul><li>대상: 백룸·리미널 스페이스와 영화형 백룸 묘사에 관심 있는 시청자</li><li>인물 변화: 호기심·허세 → 실제 공간에서 붕괴 → 규칙 학습·코미디 → 적응했지만 공포 잔존</li><li>제외: 분석 체크리스트, 관련 없는 화면 위 장문 설명, 단순 공포 극복담, 미확정 소리 인과</li></ul></section>
<div class="sequence-grid">{cards}</div>
<section class="player-card" id="reviewPlayer"><div class="blind-label">블라인드 모드: 기획 설명을 숨긴 채 영상·음성만으로 메시지와 인물 변화를 확인합니다.</div><div class="stage"><video id="baseVideo" preload="metadata" playsinline src="{media}"></video><video id="overlayVideo" preload="metadata" muted playsinline src="{media}"></video></div>
<div class="controls"><button class="control primary" id="playSequence">선택 시퀀스 재생</button><button class="control" id="prevCut">이전 기본 컷</button><button class="control" id="nextCut">다음 기본 컷</button><button class="control" id="stop">정지</button><button class="control blind" id="blindMode">블라인드 설명 숨기기</button></div><div class="meta" id="meta"></div><div class="status" id="status">원본 메타데이터를 불러오는 중입니다.</div></section>
<section class="panel explain"><h2>편집 의도와 통과 기준</h2><div class="grid"><section><h3>A 초반</h3><ul><li>훅은 문맥→허세 피크→즉시 붕괴</li><li>훅 뒤 E01→E02 시간 리셋</li><li>첫 공간까지 미래 화면 없음</li></ul></section><section><h3>B 중간</h3><ul><li>E08 중복 없이 E10 사용</li><li>암흑→전원→밝아짐이 화면으로 성립</li><li>공포 직후 코미디 보존</li></ul></section><section><h3>C 후반</h3><ul><li>적응과 공포 잔존이 함께 들림</li><li>허세가 긴장 자백으로 뒤집힘</li><li>검은 종료 화면만 같은 사건의 이전 화면으로 덮음</li></ul></section></div></section>
<section class="panel explain"><h2>AI 비트별 조치</h2><div class="table-wrap"><table><thead><tr><th>비트</th><th>판정</th><th>기능</th><th>이유</th><th>제거·축소</th></tr></thead><tbody>{actions}</tbody></table></div></section>
<section class="panel recommend explain"><h2>한 가지 권고</h2><p><b>이 편집 문법을 유지:</b> 공포 장면을 길게 쌓는 대신 `위협 또는 문제 → 행동·규칙 발견 → 김실버의 허세/코미디 → 남는 불안`을 한 사건 단위로 압축하고, 설명보다 실제 공간 상태 변화를 먼저 보여줍니다.</p></section>
{tables}
<script>
const CUTS={data};const base=document.getElementById('baseVideo'),overlay=document.getElementById('overlayVideo');const meta=document.getElementById('meta'),status=document.getElementById('status');
const sequences=[...new Set(CUTS.map(c=>c.sequence))];let selected=sequences[0],baseIndex=0,playing=false,tailing=false,activeOverlay='',blind=false;
function rows(){{return CUTS.filter(c=>c.sequence===selected)}}function bases(){{return rows().filter(c=>c.audio_mode==='linked').sort((a,b)=>a.timeline_start-b.timeline_start)}}function overlays(){{return rows().filter(c=>c.audio_mode==='none')}}
function fmt(v){{const m=Math.floor(v/60),s=(v-m*60).toFixed(2).padStart(5,'0');return m+':'+s}}function setActive(){{document.querySelectorAll('.sequence-card').forEach(b=>b.classList.toggle('active',b.dataset.sequence===selected));document.querySelectorAll('.cut-section').forEach(s=>s.classList.toggle('active',s.dataset.table===selected));const c=bases()[baseIndex];meta.textContent=selected+' · '+(baseIndex+1)+'/'+bases().length+' · '+c.cut_id+' · 원본 '+fmt(c.start)+'–'+fmt(c.end)}}
function hideOverlay(){{overlay.pause();overlay.style.display='none';activeOverlay=''}}function syncOverlay(timeline){{const c=overlays().find(x=>timeline>=x.timeline_start&&timeline<x.timeline_end);if(!c){{hideOverlay();return}}const target=c.start+(timeline-c.timeline_start);if(activeOverlay!==c.cut_id){{activeOverlay=c.cut_id;overlay.currentTime=target;overlay.style.display='block';overlay.play().catch(()=>{{}})}}else if(Math.abs(overlay.currentTime-target)>.18){{overlay.currentTime=target}}}}
function playCurrent(){{const c=bases()[baseIndex];base.muted=false;base.currentTime=c.start;base.play().then(()=>{{playing=true;tailing=false;status.textContent='음성 포함 재생 중 · '+selected}}).catch(e=>status.textContent='재생 실패: '+e.message);setActive()}}function stopAll(){{playing=false;tailing=false;base.pause();hideOverlay();status.textContent='정지됨'}}
function startVisualTail(timeline){{const c=overlays().find(x=>timeline>=x.timeline_start&&timeline<x.timeline_end);if(!c){{stopAll();status.textContent='선택 시퀀스 재생 완료';return}}base.pause();playing=false;tailing=true;const target=c.start+(timeline-c.timeline_start);activeOverlay=c.cut_id;overlay.currentTime=target;overlay.style.display='block';overlay.play().then(()=>status.textContent='무음 엔딩 여운 재생 중 · '+selected).catch(()=>{{stopAll();status.textContent='무음 엔딩 여운 재생 실패'}})}}
base.addEventListener('timeupdate',()=>{{const c=bases()[baseIndex];const timeline=c.timeline_start+Math.max(0,base.currentTime-c.start);syncOverlay(timeline);if(base.currentTime<c.end-.025)return;if(playing&&baseIndex<bases().length-1){{baseIndex++;playCurrent()}}else if(playing&&Math.max(...rows().map(x=>x.timeline_end))>c.timeline_end+.025){{startVisualTail(c.timeline_end)}}else if(playing){{stopAll();status.textContent='선택 시퀀스 재생 완료'}}}});overlay.addEventListener('timeupdate',()=>{{if(!tailing)return;const c=overlays().find(x=>x.cut_id===activeOverlay);if(c&&overlay.currentTime>=c.end-.025){{stopAll();status.textContent='선택 시퀀스 재생 완료'}}}});base.addEventListener('loadedmetadata',()=>status.textContent='원본 로드 완료 · '+fmt(base.duration)+' · {html.escape(str(fps))}fps · 오디오 활성');base.addEventListener('error',()=>status.textContent='원본을 불러오지 못했습니다. 상대 경로를 확인하세요.');
document.querySelectorAll('.sequence-card').forEach(button=>button.onclick=()=>{{stopAll();selected=button.dataset.sequence;baseIndex=0;setActive()}});document.getElementById('playSequence').onclick=()=>{{stopAll();baseIndex=0;playCurrent()}};document.getElementById('stop').onclick=stopAll;document.getElementById('prevCut').onclick=()=>{{stopAll();baseIndex=Math.max(0,baseIndex-1);base.currentTime=bases()[baseIndex].start;setActive()}};document.getElementById('nextCut').onclick=()=>{{stopAll();baseIndex=Math.min(bases().length-1,baseIndex+1);base.currentTime=bases()[baseIndex].start;setActive()}};
document.getElementById('blindMode').onclick=()=>{{blind=!blind;document.body.classList.toggle('blind-active',blind);document.getElementById('blindMode').textContent=blind?'블라인드 해제':'블라인드 설명 숨기기';status.textContent=blind?'블라인드 재생 준비됨':'설명 표시됨'}};setActive();
</script></main></body></html>"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("cutlist", type=Path)
    parser.add_argument("decisions", type=Path)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--media-src", required=True)
    parser.add_argument("--ffprobe", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"output already exists: {args.output}")
    fps = probe_fps(args.source, args.ffprobe)
    rows = load_rows(args.cutlist)
    decisions = load_decisions(args.decisions)
    document = build_document(rows, decisions, args.media_src, fps)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(document, encoding="utf-8", newline="\n")
    print(f"[integrated-review] fps={fps}, cuts={len(rows)}, decisions={len(decisions)}, output={args.output}")


if __name__ == "__main__":
    main()
