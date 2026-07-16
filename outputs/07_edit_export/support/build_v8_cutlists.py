#!/usr/bin/env python3
# Lifecycle: task-scoped
# Cleanup: keep through v8 review; remove after v8 decisions are accepted or promote only if the data-driven builder becomes cross-video
"""백룸·리미널 체험 중심 v8 스파인에서 새 컷리스트와 변경 결정표를 만든다."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


FIELDS = ["sequence", "order", "cut_id", "start", "end", "label", "role"]


def cut(cut_id: str, start: float, end: float, label: str, role: str) -> dict[str, str]:
    return {
        "sequence": "FULL_전체18비트_v8",
        "order": "",
        "cut_id": cut_id,
        "start": f"{start:.3f}",
        "end": f"{end:.3f}",
        "label": label,
        "role": role,
    }


CUTS = [
    cut("HOOK_01", 4233.740, 4248.940, "HOOK_방향을속이는소리", "백룸작동방식_약속"),
    cut("HOOK_02", 4364.040, 4369.940, "HOOK_심리와공포를건드림", "백룸작동방식_약속"),
    cut("HOOK_03", 4604.740, 4611.940, "HOOK_평범한방인데_불켜줘", "백룸작동방식_아이러니"),

    cut("B01_01", 42.535, 53.240, "B01_영화백룸_시청계기", "영화→게임_동기"),
    cut("B01_02", 53.389, 60.680, "B01_원작게임_궁금증", "영화→게임_동기"),

    cut("B02_01", 61.920, 73.600, "B02_유튜브시리즈_출발", "리미널_시청자약속"),
    cut("B02_02", 75.309, 88.240, "B02_리미널공간_궁금증", "리미널_시청자약속"),
    cut("B02_03", 92.720, 115.760, "B02_어두운방_혼자체험", "체험조건"),

    cut("B03_01", 314.940, 347.600, "B03_영화첫장면같은_게임진입", "영화비교_진입"),

    cut("B04_01", 408.840, 432.920, "B04_한복판에_내동댕이", "빈공간_공포"),
    cut("B04_02", 432.970, 448.320, "B04_커다란공간에_아무도없음", "빈공간_공포"),

    cut("B05_01", 900.801, 915.200, "B05_맵이전부_똑같음", "반복공간_방향상실"),
    cut("B05_02", 915.201, 921.280, "B05_여기서깨어나면", "반복공간_상상"),

    cut("B06_01", 1042.724, 1059.880, "B06_숨소리라도_있으면피할텐데", "소리공포_위치불명"),
    cut("B06_02", 1060.029, 1071.800, "B06_갑자기서있을까_계속방황", "소리공포_위치불명"),
    cut("B06_03", 1093.529, 1101.380, "B06_전자레인지같은_환경음", "소리공포_환경음"),

    cut("B07_01", 1102.679, 1135.160, "B07_실제비명_빈방질주", "영화거리_붕괴사건"),
    cut("B07_02", 1158.539, 1176.130, "B07_영화라서평온_세계안은불가", "영화거리_자각"),

    cut("B08_01", 1254.389, 1260.620, "B08_리미널별거아니네_허세", "체험증거_허세붕괴"),
    cut("B08_02", 1260.869, 1275.380, "B08_직접하니_무서운줄몰랐다", "체험증거_허세붕괴"),
    cut("B08_03", 1280.069, 1293.620, "B08_마우스와몸이바들바들", "체험증거_신체"),

    cut("B09_01", 1329.369, 1346.020, "B09_비슷한구조가_공간감각교란", "공간분석"),

    cut("B10_01", 2072.170, 2081.361, "B10_조우직전_지나갔나", "대표추격_인지"),
    cut("B10_02", 2082.000, 2115.740, "B10_발견_질주_도주", "대표추격_행동"),
    cut("B10_03", 2119.840, 2129.300, "B10_게임인걸알아도_무섭다", "대표추격_반응"),
    cut("B10_04", 2139.980, 2144.780, "B10_양팔벌린_엔티티", "대표추격_재조우"),
    cut("B10_05", 2182.380, 2193.067, "B10_멀리서_다시질주", "대표추격_재점화"),
    cut("B10_06", 2193.517, 2233.940, "B10_막다른길_착하게살게요", "대표추격_피크"),
    cut("B10_07", 2239.710, 2251.940, "B10_숨기_안전확인", "대표추격_결과"),

    cut("B11_01", 2294.060, 2302.940, "B11_문닫으면_못들어옴", "엔티티규칙_문"),
    cut("B11_02", 2589.290, 2595.940, "B11_빼꼼은_못봄", "엔티티규칙_관찰"),
    cut("B11_03", 2597.540, 2602.940, "B11_빼꼼관찰_성공", "엔티티규칙_관찰"),

    cut("B12_01", 2665.140, 2679.940, "B12_백룸을보고_내용이궁금", "중간회고_백룸관심"),
    cut("B12_02", 2680.240, 2685.940, "B12_모시계단_찾아봄", "중간회고_세계관"),
    cut("B12_03", 2686.840, 2689.940, "B12_엔티티요소_알게됨", "중간회고_세계관"),
    cut("B12_04", 2690.090, 2697.683, "B12_리미널스페이스_관심", "중간회고_리미널"),
    cut("B12_05", 2699.590, 2700.940, "B12_관심이커짐", "중간회고_리미널"),
    cut("B12_06", 2703.590, 2720.723, "B12_백룸안의느낌_게임까지", "중간회고_체험질문"),

    cut("B13_01", 3422.890, 3428.940, "B13_어두운공간이_무섭다", "광원작동_암흑"),
    cut("B13_02", 3502.090, 3507.940, "B13_전원키는곳_발견", "광원작동_UI"),
    cut("B13_03", 3510.340, 3524.770, "B13_전원켜고_혼자생쇼", "광원작동_전후결과"),

    cut("B14_01", 3527.090, 3532.940, "B14_에이싱크회사_건물추정", "세계관_관찰시설"),
    cut("B14_02", 3533.440, 3539.940, "B14_건물내부에서_백룸", "세계관_관찰시설"),
    cut("B14_03", 3540.840, 3549.940, "B14_백룸을_관찰한시설", "세계관_관찰시설"),

    cut("B15_01", 4271.015, 4275.940, "B15_반복할수록_무서움감소", "반복의한계_익숙함"),
    cut("B15_02", 4276.690, 4289.940, "B15_공포속에서_계속헤맴", "반복의한계_공간"),
    cut("B15_03", 4342.190, 4353.940, "B15_엔티티익숙_공포는잔존", "반복의한계_결론"),

    cut("B16_01", 4581.940, 4585.940, "B16_광원을_게임요소로잘씀", "구현비평_광원강점"),
    cut("B16_02", 4591.090, 4603.940, "B16_영화의기괴한공간감은_약함", "구현비평_공간반례"),

    cut("B17_01", 4694.190, 4695.940, "B17_이게열리는_소리였구나", "소리재해석_발견"),
    cut("B17_02", 4704.540, 4713.940, "B17_소리가_장소개방신호", "소리재해석_인과"),
    cut("B17_03", 4716.490, 4719.940, "B17_놀래키는요소로_오해", "소리재해석_오해"),
    cut("B17_04", 4720.640, 4725.940, "B17_귀에가까워_무서움으로인식", "소리재해석_오해"),
    cut("B17_05", 4727.840, 4735.940, "B17_진행을알리는_장치", "소리재해석_이해"),

    cut("B18_01", 4790.340, 4793.940, "B18_무서워서정리하는건아님", "체험종료_부정"),
    cut("B18_02", 4798.740, 4811.940, "B18_백룸시청기념_게임마무리", "체험종료_정리"),
    cut("B18_03", 4908.715, 4915.940, "B18_오늘방송_여기까지", "체험종료_종료"),
    cut("B18_04", 4920.380, 4923.940, "B18_너무긴장했다", "체험종료_잔여감정"),
]


DECISION_FIELDS = ["change_id", "target", "action", "before", "after", "reason", "evidence"]
DECISIONS = [
    ("V8_01", "전체", "기존 스파인 폐기·전면 재작성", "v7 공포→적응 중심 88컷", "v8 백룸·리미널 공간→빛·소리→구현 평가 중심", "사용자 지시에 따라 백룸 팬의 관심을 주축으로 변경", "v8 5단계 기획서·6단계 후보 지도"),
    ("V8_02", "HOOK", "콜드오픈 재설계", "인간형 엔티티 비명", "방향 없는 소리→심리 평가→평범한 방인데 불 요청", "영상의 새 질문을 첫 30초 안에 약속", "4233.74~4248.94, 4364.04~4369.94, 4604.74~4611.94"),
    ("V8_03", "B01~B04", "영화·리미널 기대와 공간 진입 강화", "인물 셋업·사운드 공포", "영화 시청→리미널 궁금증→영화 같은 진입→큰 빈 공간", "백룸 팬의 유입 이유와 첫 화면 보상 연결", "SRT 42.535~445.920, 신규 원본 프레임"),
    ("V8_04", "B05~B06", "반복 구조·소리 메커니즘 추가", "v7에서 대부분 미선정", "똑같은 맵·위치 불명 위협·환경음", "괴물 이전에 공간과 소리가 공포를 만드는 근거", "SRT 900.801~1101.380"),
    ("V8_05", "B07~B09", "체험과 분석 연결", "영화 거리 붕괴·신체 공포", "영화 거리 붕괴→신체 증거→공간감각 분석", "리액션을 백룸 작동 방식의 증거로 재배치", "SRT 1106.410~1346.020"),
    ("V8_06", "B10~B11", "대표 사건 1개와 규칙 학습만 유지", "다수 추격·공포 반복", "완결형 추격 1개→문·관찰 규칙", "재미와 게임 체험은 보존하되 중심을 빼앗지 않음", "C09~C11 원본 자산"),
    ("V8_07", "B12", "백룸·리미널 중간 회고 신설", "v7 미선정", "모시계단·엔티티·리미널 관심과 실제 느낌 질문", "시청자 관심축을 본문 중간에서 명시적으로 회수", "SRT 2665.140~2720.723"),
    ("V8_08", "B13~B14", "광원 전후·관찰시설 단서 신설", "v7 코미디 이완만 유지", "암흑→전원 UI→환한 관찰창→회사 세계관", "게임이 백룸을 구현하는 방법을 화면으로 보여줌", "SRT 3422.890~3549.940, 신규 원본 프레임"),
    ("V8_09", "B15", "적응을 반복의 한계로 강등", "v7 메시지 결론", "엔티티는 익숙해져도 헤맴과 공포는 남음", "적응을 주제가 아닌 체험 변화로 사용", "SRT 4271.015~4353.940"),
    ("V8_10", "B16", "공간 재현 반례 신설", "v7 미선정", "광원 강점과 영화식 기괴한 공간감의 약점", "긍정 일변도의 거짓 평가를 방지", "SRT 4581.940~4603.940"),
    ("V8_11", "B17", "소리 기능 재해석 신설", "v7 미선정", "공포음 오해→장소 개방 신호 이해", "소리 축에 발견과 결론을 부여", "SRT 4694.190~4735.940"),
    ("V8_12", "B18", "백룸 체험 종료로 재정의", "공포 부정·퇴장", "체험 정리→종료→긴장 자백", "캐릭터 아이러니를 보조 결말로 유지", "SRT 4790.340~4923.940"),
]


def beat_id(cut_id: str) -> str:
    return "HOOK" if cut_id.startswith("HOOK") else cut_id.split("_", 1)[0]


def build_content() -> list[dict[str, str]]:
    rows = [dict(row) for row in CUTS]
    for order, row in enumerate(rows, 1):
        row["order"] = str(order)
    validate_content(rows)
    return rows


def validate_content(rows: list[dict[str, str]]) -> None:
    ids = [row["cut_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("중복 cut_id")
    if [int(row["order"]) for row in rows] != list(range(1, len(rows) + 1)):
        raise ValueError("order가 연속적이지 않음")
    sections = {beat_id(cut_id) for cut_id in ids}
    expected = {"HOOK"} | {f"B{i:02d}" for i in range(1, 19)}
    if sections != expected:
        raise ValueError(f"비트 불일치: missing={sorted(expected-sections)}, extra={sorted(sections-expected)}")
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
        sequence = "00_HOOK_백룸작동방식_v8" if section == "HOOK" else f"{int(section[1:]):02d}_{section}_v8"
        parts.append({
            **row,
            "sequence": sequence,
            "order": str(counts[section]),
            "cut_id": f"PART_{row['cut_id']}",
        })
    full = [
        {**row, "sequence": "FULL_전체18비트_v8", "cut_id": f"FULL_{row['cut_id']}"}
        for row in rows
    ]
    combined = parts + full
    if len({row["cut_id"] for row in combined}) != len(combined):
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
    parser.add_argument("content_output", type=Path)
    parser.add_argument("multisequence_output", type=Path)
    parser.add_argument("decision_output", type=Path)
    args = parser.parse_args()

    content = build_content()
    multi = build_multisequence(content)
    decisions = [dict(zip(DECISION_FIELDS, row)) for row in DECISIONS]
    write_csv(args.content_output, content, FIELDS)
    write_csv(args.multisequence_output, multi, FIELDS)
    write_csv(args.decision_output, decisions, DECISION_FIELDS)
    duration = sum(float(row["end"]) - float(row["start"]) for row in content)
    print(f"[v8-cutlists] content={len(content)} cuts, duration={duration:.2f}s")
    print(f"[v8-cutlists] multisequence={len(multi)} rows, decisions={len(decisions)}")


if __name__ == "__main__":
    main()
