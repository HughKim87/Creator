#!/usr/bin/env python3
# Lifecycle: task-scoped
# Cleanup: keep through user review; remove after the v9 grammar is accepted or rejected.
"""v9 캘리브레이션 XML의 V1 오디오와 V2 무음 컷어웨이를 브라우저에서 검토하는 페이지를 만든다."""

from __future__ import annotations

import argparse
import csv
import html
import json
import subprocess
from collections import OrderedDict
from fractions import Fraction
from pathlib import Path


def load_rows(path: Path) -> list[dict[str, object]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("캘리브레이션 컷리스트가 비어 있음")
    parsed = []
    for item in rows:
        parsed.append(
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
    return parsed


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
    value = result.stdout.strip()
    fps = Fraction(value)
    if fps <= 0:
        raise ValueError(f"잘못된 FPS: {value}")
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
    purposes = {
        "CAL_A_훅과빠른진입": "12.9초 미니 사건 뒤 설명을 압축하고 31.5초에 실제 백룸으로 진입하는지 확인",
        "CAL_B_추격과코미디": "발견→도주→막힘→탄원→생존→코미디가 반복 없이 이어지는지 확인",
        "CAL_C_주제회수와아이러니": "백룸 공간 기대와 빛의 공포 한 논지가 화면 근거·캐릭터 아이러니와 연결되는지 확인",
    }
    cards = []
    for index, (name, items) in enumerate(grouped.items()):
        duration = max(float(item["timeline_end"]) for item in items)
        linked = sum(item["audio_mode"] == "linked" for item in items)
        overlays = sum(item["audio_mode"] == "none" for item in items)
        cards.append(
            f'<button class="sequence-card" data-sequence="{html.escape(name, quote=True)}">'
            f'<b>{html.escape(name)}</b><span>{duration:.1f}초 · 발화/사건 {linked}컷 · V2 {overlays}컷</span>'
            f'<small>{html.escape(purposes[name])}</small></button>'
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
            kind = "V2 무음 화면" if item["audio_mode"] == "none" else "V1+A1/A2"
            body.append(
                '<tr>'
                f'<td>{html.escape(str(item["cut_id"]))}</td>'
                f'<td>{float(item["timeline_start"]):.3f}–{float(item["timeline_end"]):.3f}</td>'
                f'<td>{float(item["start"]):.3f}–{float(item["end"]):.3f}</td>'
                f'<td>{kind}</td><td>{html.escape(str(item["role"]))}</td>'
                '</tr>'
            )
        sections.append(
            f'<section class="cut-section" data-table="{html.escape(name, quote=True)}">'
            f'<h2>{html.escape(name)}</h2><div class="table-wrap"><table><thead><tr>'
            '<th>컷</th><th>편집본</th><th>원본</th><th>트랙</th><th>기능</th>'
            f'</tr></thead><tbody>{"".join(body)}</tbody></table></div></section>'
        )
    return "\n".join(sections)


def build_document(rows: list[dict[str, object]], media_src: str, fps: Fraction) -> str:
    timeline_rows = add_timeline(rows, fps)
    data = json.dumps(timeline_rows, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    cards = sequence_cards(timeline_rows)
    tables = cut_tables(timeline_rows)
    media = html.escape(media_src, quote=True)
    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>백룸 v9 편집문법 캘리브레이션</title>
<style>
:root{{--bg:#07111f;--card:#101d31;--line:#2a405f;--txt:#e8f0fb;--muted:#9db0ca;--accent:#38bdf8;--ok:#86efac}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--txt);font-family:system-ui,"Malgun Gothic",sans-serif;line-height:1.55}}
main{{max-width:1180px;margin:auto;padding:28px 18px 70px}}h1{{font-size:28px;margin:0 0 8px}}.lede{{color:var(--muted);margin:0 0 20px}}
.notice{{border:1px solid #7c3aed;background:#2e1065;padding:13px 15px;border-radius:10px;margin-bottom:16px}}
.sequence-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:16px}}.sequence-card{{text-align:left;border:1px solid var(--line);background:var(--card);color:var(--txt);border-radius:10px;padding:13px;cursor:pointer}}
.sequence-card.active{{border-color:var(--accent);box-shadow:0 0 0 2px #38bdf833}}.sequence-card b,.sequence-card span,.sequence-card small{{display:block}}.sequence-card span{{color:#bae6fd;margin:5px 0}}.sequence-card small{{color:var(--muted)}}
.player-card{{position:static;border:1px solid var(--line);background:var(--card);border-radius:12px;padding:14px;margin-bottom:18px}}
.stage{{position:relative;aspect-ratio:16/9;background:#020617;border-radius:9px;overflow:hidden}}.stage video{{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;background:#020617}}#overlayVideo{{display:none;z-index:2}}
.controls{{display:flex;gap:8px;flex-wrap:wrap;margin-top:11px}}button.control{{border:1px solid #496482;background:#203552;color:var(--txt);padding:8px 12px;border-radius:7px;cursor:pointer}}button.primary{{background:#0369a1;border-color:#0ea5e9}}
.meta{{font-family:ui-monospace,Consolas,monospace;color:#bae6fd;margin-top:9px}}.status{{color:var(--muted);font-size:13px;margin-top:4px}}
.approval{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:16px 0}}.approval section{{background:var(--card);border:1px solid var(--line);border-radius:9px;padding:12px}}.approval h3{{margin:0 0 7px;font-size:15px;color:#bae6fd}}.approval ul{{margin:0;padding-left:20px}}
.cut-section{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;margin-top:12px;display:none}}.cut-section.active{{display:block}}.cut-section h2{{margin:0 0 10px;font-size:18px}}
.table-wrap{{overflow:auto}}table{{border-collapse:collapse;width:100%;font-size:13px}}th,td{{padding:8px;border-bottom:1px solid var(--line);text-align:left;white-space:nowrap}}th{{color:#bae6fd}}td:last-child{{white-space:normal}}
@media(max-width:820px){{.sequence-grid,.approval{{grid-template-columns:1fr}}}}
</style></head><body><main>
<h1>백룸 v9 편집문법 캘리브레이션</h1>
<p class="lede">전체본이 아닙니다. 초반·중간·후반의 대표 리듬 세 개만 먼저 승인받기 위한 7C 검증 페이지입니다.</p>
<div class="notice"><b>검증 대기:</b> Premiere 가져오기와 사용자 리듬 승인이 끝나기 전에는 v9 전체 편집으로 확장하지 않습니다. 새 MP4도 생성하지 않았습니다.</div>
<div class="sequence-grid">{cards}</div>
<section class="player-card" id="reviewPlayer"><div class="stage"><video id="baseVideo" preload="metadata" playsinline src="{media}"></video><video id="overlayVideo" preload="metadata" muted playsinline src="{media}"></video></div>
<div class="controls"><button class="control primary" id="playSequence">선택 시퀀스 재생</button><button class="control" id="prevCut">이전 기본 컷</button><button class="control" id="nextCut">다음 기본 컷</button><button class="control" id="stop">정지</button></div>
<div class="meta" id="meta"></div><div class="status" id="status">원본 메타데이터를 불러오는 중입니다.</div></section>
<div class="approval"><section><h3>A 승인 기준</h3><ul><li>훅이 하나의 사건으로 이해되는가</li><li>설명보다 공간 진입이 충분히 빠른가</li></ul></section><section><h3>B 승인 기준</h3><ul><li>추격 원인·막힘·결과가 빠지지 않았는가</li><li>공포 직후 김실버의 코미디가 살아 있는가</li></ul></section><section><h3>C 승인 기준</h3><ul><li>백룸 관심을 화면이 실제로 받쳐주는가</li><li>논지가 빛의 강점과 공간 재현의 한계로 모이는가</li></ul></section></div>
{tables}
<script>
const CUTS={data};
const base=document.getElementById('baseVideo'),overlay=document.getElementById('overlayVideo');
const meta=document.getElementById('meta'),status=document.getElementById('status');
const sequences=[...new Set(CUTS.map(c=>c.sequence))];let selected=sequences[0],baseIndex=0,playing=false,activeOverlay='';
function rows(){{return CUTS.filter(c=>c.sequence===selected)}}function bases(){{return rows().filter(c=>c.audio_mode==='linked').sort((a,b)=>a.timeline_start-b.timeline_start)}}
function overlays(){{return rows().filter(c=>c.audio_mode==='none')}}function fmt(v){{const m=Math.floor(v/60),s=(v-m*60).toFixed(2).padStart(5,'0');return m+':'+s}}
function setActive(){{document.querySelectorAll('.sequence-card').forEach(b=>b.classList.toggle('active',b.dataset.sequence===selected));document.querySelectorAll('.cut-section').forEach(s=>s.classList.toggle('active',s.dataset.table===selected));const c=bases()[baseIndex];meta.textContent=selected+' · '+(baseIndex+1)+'/'+bases().length+' · '+c.cut_id+' · 원본 '+fmt(c.start)+'–'+fmt(c.end)}}
function hideOverlay(){{overlay.pause();overlay.style.display='none';activeOverlay=''}}
function syncOverlay(timeline){{const c=overlays().find(x=>timeline>=x.timeline_start&&timeline<x.timeline_end);if(!c){{hideOverlay();return}}const target=c.start+(timeline-c.timeline_start);if(activeOverlay!==c.cut_id){{activeOverlay=c.cut_id;overlay.currentTime=target;overlay.style.display='block';overlay.play().catch(()=>{{}})}}else if(Math.abs(overlay.currentTime-target)>.18){{overlay.currentTime=target}}}}
function playCurrent(){{const c=bases()[baseIndex];base.currentTime=c.start;base.play().then(()=>{{playing=true;status.textContent='재생 중 · '+selected}}).catch(e=>status.textContent='재생 실패: '+e.message);setActive()}}
function stopAll(){{playing=false;base.pause();hideOverlay();status.textContent='정지됨'}}
base.addEventListener('timeupdate',()=>{{const c=bases()[baseIndex];const timeline=c.timeline_start+Math.max(0,base.currentTime-c.start);syncOverlay(timeline);if(base.currentTime<c.end-.025)return;if(playing&&baseIndex<bases().length-1){{baseIndex++;playCurrent()}}else{{stopAll();status.textContent='선택 시퀀스 재생 완료'}}}});
base.addEventListener('loadedmetadata',()=>status.textContent='원본 로드 완료 · '+fmt(base.duration)+' · {html.escape(str(fps))}fps');base.addEventListener('error',()=>status.textContent='원본을 불러오지 못했습니다. 상대 경로를 확인하세요.');
document.querySelectorAll('.sequence-card').forEach(button=>button.onclick=()=>{{stopAll();selected=button.dataset.sequence;baseIndex=0;setActive()}});
document.getElementById('playSequence').onclick=()=>{{stopAll();baseIndex=0;playCurrent()}};document.getElementById('stop').onclick=stopAll;
document.getElementById('prevCut').onclick=()=>{{stopAll();baseIndex=Math.max(0,baseIndex-1);base.currentTime=bases()[baseIndex].start;setActive()}};
document.getElementById('nextCut').onclick=()=>{{stopAll();baseIndex=Math.min(bases().length-1,baseIndex+1);base.currentTime=bases()[baseIndex].start;setActive()}};setActive();
</script></main></body></html>"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("cutlist", type=Path)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--media-src", required=True)
    parser.add_argument("--ffprobe", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"출력 파일이 이미 존재함: {args.output}")
    fps = probe_fps(args.source, args.ffprobe)
    document = build_document(load_rows(args.cutlist), args.media_src, fps)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(document, encoding="utf-8", newline="\n")
    print(f"[v9-review] fps={fps}, cuts={len(load_rows(args.cutlist))}, output={args.output}")


if __name__ == "__main__":
    main()
