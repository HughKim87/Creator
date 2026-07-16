#!/usr/bin/env python3
# Lifecycle: task-scoped
# Cleanup: keep through v7 review; remove after the v7 decisions are accepted or promoted to a generic revision tool
"""v6 컷리스트에 승인된 스파인 개선 결정을 적용해 v7 CSV 두 종류를 만든다."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


FIELDS = ["sequence", "order", "cut_id", "start", "end", "label", "role"]

REMOVE_IDS = {
    "B02_04", "B02_05", "B02_06", "B02_07",
    "B03_02", "B03_03",
    "B04_02", "B04_03", "B04_05",
    "B05_03", "B05_04",
    "B07_08", "B07_10", "B07_11", "B07_12", "B07_14", "B07_15", "B07_16", "B07_17", "B07_18",
    "B09_02", "B09_03",
    "B10_04",
    "B15_04", "B15_05",
    "B17_04",
}

OVERRIDES = {
    "B02_01": {"label": "B02_진입전_문구와사운드에쫄림", "role": "게임진입·소리공포"},
    "B02_02": {"label": "B02_사운드만으로_공포확인", "role": "게임진입·소리공포"},
    "B02_03": {"label": "B02_게임진입_영화같은추격", "role": "게임진입·소리공포"},
    "B02_08": {"label": "B02_못하겠다_소리에반응", "role": "게임진입·소리공포"},
    "B03_01": {"label": "B03_현실침범_노크_살려줘", "role": "현실침범"},
    "B03_04": {"label": "B03_현실침범_그림자오인", "role": "현실침범"},
    "B03_05": {"label": "B03_현실침범_휴대폰점등", "role": "현실침범"},
    "B04_01": {"label": "B04_첫피격_비명_방어허세", "role": "첫붕괴·방어허세"},
    "B04_04": {"label": "B04_허세뒤_소름자백", "role": "첫붕괴·방어허세"},
    "B05_01": {"role": "핵심전환_공포사건→자각"},
    "B05_02": {"role": "핵심전환_공포사건→자각"},
    "B06_01": {"role": "핵심전환_신체증거"},
    "B06_02": {"role": "핵심전환_신체증거"},
    "B06_03": {"role": "핵심전환_신체증거"},
    "B06_04": {"role": "핵심전환_신체증거"},
    "B07_01": {"role": "자기설득실패"},
    "B07_02": {"role": "자기설득실패"},
    "B07_03": {"role": "자기설득실패"},
    "B07_04": {"role": "자기설득실패"},
    "B07_05": {"role": "진행브리지"},
    "B07_06": {"role": "진행브리지"},
    "B07_07": {"role": "진행브리지"},
    "B07_09": {"role": "진행브리지"},
    "B07_13": {"role": "진행브리지"},
    "B09_01": {"role": "규칙적응_대표실험"},
    "B09_04": {"role": "규칙적응_대표실험"},
    "B09_05": {"role": "규칙적응_대표실험"},
    "B10_01": {"role": "시청자의존_씨앗"},
    "B10_02": {"start": "2917.19", "label": "B10_도움받아_레버성공", "role": "시청자의존_씨앗"},
    "B10_03": {"label": "B10_공략감사", "role": "시청자의존_씨앗"},
    "B11_01": {"label": "B11_훅사건직전_또괴물불안", "role": "훅사건_콜백"},
    "B11_02": {"label": "B11_훅사건직전_미치겠네", "role": "훅사건_콜백"},
    "B11_03": {"label": "B11_훅사건사후_인간형해석", "role": "훅사건_콜백"},
    "B11_04": {"label": "B11_훅사건사후_공포재확인", "role": "훅사건_콜백"},
    "B15_01": {"role": "긴장이완_대표도전"},
    "B15_02": {"role": "긴장이완_대표도전"},
    "B15_03": {"end": "4125.94", "label": "B15_대표도전_도착성공", "role": "긴장이완_대표도전"},
    "B17_01": {"role": "시청자의존_회수"},
    "B17_02": {"end": "4513.94", "label": "B17_시청자없었으면_진작종료", "role": "시청자의존_회수"},
    "B17_03": {"role": "솔직한퇴장"},
    "B17_05": {"role": "솔직한퇴장"},
    "B17_06": {"role": "솔직한퇴장"},
}

ADDED_AFTER_B14 = {
    "sequence": "FULL_전체18비트_v7",
    "order": "",
    "cut_id": "B14_05",
    "start": "3993.97",
    "end": "4002.94",
    "label": "B14_규칙활용_달리기성공",
    "role": "적응행동증거",
}

DECISIONS = [
    ("V7_01", "B02", "압축·역할 재정의", "8컷 63.29초", "4컷 33.77초", "목표·UI·환경음 반복을 빼고 진입 전 사운드 공포→게임 진입→소리 반응만 남김", "SRT 192.40~204.56, 314.94~347.60, 544.30~552.44; C02·intro·early_fear 화면 근거"),
    ("V7_02", "B03", "설명 제거", "5컷 66.57초", "3컷 59.56초", "엔티티 정의를 제거해 노크·그림자·휴대폰 점등의 현실 침범 기능에 집중", "SRT 612.27~646.80, 707.35~713.96, 736.42~754.48"),
    ("V7_03", "B04", "사건 집중", "5컷 54.34초", "2컷 33.81초", "첫 피격→비명→방어 허세와 뒤이은 소름 자백만 남김", "SRT 846.23~871.88, 1084.52~1092.52"),
    ("V7_04", "B05+B06", "핵심 전환 연결", "8컷 86.56초", "6컷 72.18초", "B01에서 이미 밝힌 어두운 방 설명을 반복하지 않고 비명→영화와 현실 차이→떨림 증거를 연속 배치", "SRT 1102.68~1175.30, 1254.39~1293.62"),
    ("V7_05", "B07", "최우선 재설계", "18컷 122.82초", "9컷 59.42초", "자기설득 실패를 스파인으로 두고 추락·맵 전환만 진행 브리지로 남김", "C08·fall·transition 화면 근거; 규칙 읽기·환경음 반복·추가 추격 제거"),
    ("V7_06", "B09", "대표 실험만 유지", "5컷 26.34초", "3컷 16.62초", "문 닫기와 빼꼼 관찰 두 규칙만 남겨 적응 증거를 선명하게 함", "SRT 2294.65~2302.94, 2589.29~2602.94"),
    ("V7_07", "B10", "시청자 의존 씨앗 압축", "4컷 18.73초", "3컷 13.50초", "실제 발화의 도움 요청→레버 성공→감사만 남겨 B17 회수 준비", "SRT 2840.94~2848.94, 2917.19~2927.94"),
    ("V7_08", "B11", "훅 콜백으로 재정의", "조우·사망처럼 보이는 표기", "훅 직전 불안→훅 사건 사후 인간형 해석", "본문에 없는 사건을 다시 넣지 않고 오프닝 사건의 전후 반응이라는 실제 구성에 맞춤", "원본 2995.81~2999.85와 3046.18~3057.27; 훅 3022.90~3035.80"),
    ("V7_09", "B14", "행동 증거 추가", "선언 4컷 22.71초", "선언+달리기 성공 5컷 31.69초", "근성게임 선언 직후 실제로 규칙을 활용해 달려 성공하는 행동을 붙임", "SRT 3993.97~4002.94; C17 화면 근거"),
    ("V7_10", "B15", "기능 축소", "5컷 26.07초", "3컷 15.74초", "마피아 농담과 대표 도전만 남기고 허세·익숙함 반복은 B14·B16에 양보", "SRT 4101.19~4110.94, 4118.94~4125.94; C18 화면 근거"),
    ("V7_11", "B17", "엔딩 진입 압축", "6컷 23.62초", "5컷 18.63초", "시청자 의존→끄고 싶음→온몸 긴장→편한 게임 희망의 감정 하강만 유지", "SRT 4504.24~4513.94, 4678.49~4693.94"),
]


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("기준 컷리스트가 비어 있음")
    return rows


def transform(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    seen = {row["cut_id"] for row in rows}
    unknown = (REMOVE_IDS | set(OVERRIDES)) - seen
    if unknown:
        raise ValueError(f"기준본에서 찾지 못한 컷: {sorted(unknown)}")

    for source_row in rows:
        cut_id = source_row["cut_id"]
        if cut_id in REMOVE_IDS:
            continue
        row = {field: source_row.get(field, "") for field in FIELDS}
        row.update(OVERRIDES.get(cut_id, {}))
        row["sequence"] = "FULL_전체18비트_v7"
        output.append(row)
        if cut_id == "B14_04":
            output.append(dict(ADDED_AFTER_B14))

    for order, row in enumerate(output, 1):
        row["order"] = str(order)

    validate_content(output)
    return output


def beat_id(cut_id: str) -> str:
    return "HOOK" if cut_id.startswith("HOOK") else cut_id.split("_", 1)[0]


def validate_content(rows: list[dict[str, str]]) -> None:
    ids = [row["cut_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("중복 cut_id")
    if [int(row["order"]) for row in rows] != list(range(1, len(rows) + 1)):
        raise ValueError("order가 연속적이지 않음")
    missing = [f"B{i:02d}" for i in range(1, 19) if f"B{i:02d}" not in {beat_id(i) for i in ids}]
    if missing:
        raise ValueError(f"누락 비트: {missing}")
    intervals = sorted((float(row["start"]), float(row["end"]), row["cut_id"]) for row in rows)
    for start, end, cut_id in intervals:
        if end <= start:
            raise ValueError(f"0 이하 길이 컷: {cut_id}")
    for previous, current in zip(intervals, intervals[1:]):
        if current[0] < previous[1]:
            raise ValueError(f"원본 시간 중복: {previous[2]} / {current[2]}")


def build_multisequence(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    parts: list[dict[str, str]] = []
    counts: Counter[str] = Counter()
    for row in rows:
        section = beat_id(row["cut_id"])
        counts[section] += 1
        if section == "HOOK":
            sequence = "00_HOOK_C09_v7"
        else:
            sequence = f"{int(section[1:]):02d}_{section}_v7"
        parts.append({
            **row,
            "sequence": sequence,
            "order": str(counts[section]),
            "cut_id": f"PART_{row['cut_id']}",
        })

    full = [
        {**row, "sequence": "FULL_전체18비트_v7", "cut_id": f"FULL_{row['cut_id']}"}
        for row in rows
    ]
    combined = parts + full
    ids = [row["cut_id"] for row in combined]
    if len(ids) != len(set(ids)):
        raise ValueError("다중 시퀀스 cut_id 중복")
    return combined


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    if path.exists():
        raise FileExistsError(f"출력 파일이 이미 존재함: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, quoting=csv.QUOTE_ALL, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline", type=Path)
    parser.add_argument("content_output", type=Path)
    parser.add_argument("multisequence_output", type=Path)
    parser.add_argument("decision_output", type=Path)
    args = parser.parse_args()

    content = transform(read_rows(args.baseline))
    multi = build_multisequence(content)
    decision_fields = ["change_id", "target", "action", "before", "after", "reason", "evidence"]
    decisions = [dict(zip(decision_fields, row)) for row in DECISIONS]
    write_csv(args.content_output, content, FIELDS)
    write_csv(args.multisequence_output, multi, FIELDS)
    write_csv(args.decision_output, decisions, decision_fields)
    duration = sum(float(row["end"]) - float(row["start"]) for row in content)
    print(f"[v7-cutlists] content={len(content)} cuts, duration={duration:.2f}s")
    print(f"[v7-cutlists] multisequence={len(multi)} rows, decisions={len(decisions)}")


if __name__ == "__main__":
    main()
