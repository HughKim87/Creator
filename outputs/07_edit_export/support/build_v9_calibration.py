#!/usr/bin/env python3
# Lifecycle: task-scoped
# Cleanup: keep until the user approves or rejects the v9 calibration; then record the grammar and remove this builder.
"""v9 편집문법 승인을 위한 훅·추격·주제 회수 3개 캘리브레이션 시퀀스를 만든다."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


CUT_FIELDS = [
    "sequence",
    "order",
    "cut_id",
    "start",
    "end",
    "label",
    "role",
    "timeline_start",
    "video_track",
    "audio_mode",
    "audio_start",
    "audio_end",
]
DECISION_FIELDS = [
    "decision_id",
    "sequence",
    "target",
    "action",
    "before",
    "after",
    "reason",
    "evidence",
]


def row(
    sequence: str,
    cut_id: str,
    start: float,
    end: float,
    label: str,
    role: str,
    timeline_start: float | None,
    *,
    video_track: int = 1,
    audio_mode: str = "linked",
) -> dict[str, str]:
    return {
        "sequence": sequence,
        "order": "",
        "cut_id": cut_id,
        "start": f"{start:.3f}",
        "end": f"{end:.3f}",
        "label": label,
        "role": role,
        "timeline_start": "" if timeline_start is None else f"{timeline_start:.6f}",
        "video_track": str(video_track),
        "audio_mode": audio_mode,
        "audio_start": "",
        "audio_end": "",
    }


def append_linked(
    rows: list[dict[str, str]],
    sequence: str,
    cursor: float,
    cut_id: str,
    start: float,
    end: float,
    label: str,
    role: str,
) -> float:
    # 연결 V1/A1/A2는 타임라인 시작점을 비워 둔다. XML 생성기가 원본 메타데이터의
    # 실제 FPS와 각 절대 in/out 프레임 차이로 다음 시작점을 계산해야 반올림 누적이 없다.
    rows.append(row(sequence, cut_id, start, end, label, role, None))
    return cursor + end - start


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    # A: 12.9초짜리 미니 사건 뒤에 동기 두 문장만 남기고 31.5초에 실제 백룸에 진입한다.
    seq = "CAL_A_훅과빠른진입"
    cursor = 0.0
    cursor = append_linked(rows, seq, cursor, "A_HOOK", 3022.900, 3035.800, "조우_비명_사망", "훅_완결미니사건")
    cursor = append_linked(rows, seq, cursor, "A_MOTIVE", 42.535, 53.240, "영화백룸을보고게임궁금", "동기_새정보")
    cursor = append_linked(rows, seq, cursor, "A_CONDITION", 117.419, 125.320, "어두운방에서혼자체험", "체험조건_새정보")
    cursor = append_linked(rows, seq, cursor, "A_ENTRY", 314.940, 347.600, "영화첫장면같은백룸진입", "기대보상_실제공간")

    # 훅은 명시적인 콜드오픈이지만, 훅이 끝난 뒤 본편 셋업에는 미래 플레이 B-roll을 섞지 않는다.
    # A_MOTIVE·A_CONDITION의 동시대 원본 화면을 그대로 보여 주고 A_ENTRY에서 처음 게임에 진입한다.

    # B: 추격을 발견→도주→막힘→탄원→생존→코미디의 2~8초 마이크로비트로 재구성한다.
    seq = "CAL_B_추격과코미디"
    cursor = 0.0
    chase = [
        ("B_LISTEN", 2082.861, 2084.500, "지나갔나", "발견전_정적"),
        ("B_SPOTTED", 2084.739, 2087.699, "발견했다", "발견"),
        ("B_RUN", 2096.630, 2102.185, "추격시작", "도주"),
        ("B_REENCOUNTER", 2119.840, 2126.569, "게임인걸알아도무서운재조우", "재조우"),
        ("B_ENTITY", 2140.150, 2144.780, "양팔벌리고달리는엔티티", "위협시각화"),
        ("B_DEAD_END", 2193.517, 2196.887, "막다른길", "막힘"),
        ("B_DOOMED", 2196.937, 2198.900, "조졌어", "막힘_감정피크"),
        ("B_STAMINA", 2205.100, 2212.700, "스태미나고갈과추격", "압박"),
        ("B_PLEA_SETUP", 2213.800, 2216.940, "탄원시작", "탄원_설정"),
        ("B_PLEA_PEAK", 2217.040, 2225.940, "착하게살게요", "탄원_피크"),
        ("B_LAUGH", 2239.739, 2243.940, "웃음과왜안가", "공포직후코미디"),
        ("B_HIDE", 2244.040, 2249.978, "숨어서안전확인", "회피"),
        ("B_DOOR", 2253.990, 2260.940, "문으로생존", "결과"),
        ("B_WATER", 2264.590, 2268.940, "아몬드워터", "긴장이완_코미디"),
        ("B_RECOVER", 2269.890, 2275.940, "자기격려하고회복", "캐릭터회복"),
    ]
    for values in chase:
        cursor = append_linked(rows, seq, cursor, *values)

    # C: 백룸 공간 기대와 빛의 공포라는 한 논지만 남기고, 주차장 발화는 관련 화면으로 덮는다.
    seq = "CAL_C_주제회수와아이러니"
    cursor = 0.0
    cursor = append_linked(rows, seq, cursor, "C_CURIOSITY", 2673.540, 2679.940, "백룸내용이궁금했다", "관심_질문")
    cursor = append_linked(rows, seq, cursor, "C_PLAY", 2710.440, 2720.723, "궁금증이게임체험으로이어짐", "관심_행동")
    for cut_id, start, end, timeline, label in [
        ("C_V2_EMPTY", 408.840, 412.840, 0.000, "빈백룸_관심시각화"),
        ("C_V2_REPEAT", 900.801, 904.801, 4.000, "반복공간_관심시각화"),
        ("C_V2_SOUND", 1042.724, 1046.724, 8.000, "위치불명복도_관심시각화"),
        ("C_V2_SPACE", 1329.369, 1334.052, 12.000, "반복복도_공간감시각화"),
    ]:
        rows.append(
            row(
                seq,
                cut_id,
                start,
                end,
                label,
                "무음V2_주차장화면교체",
                timeline,
                video_track=2,
                audio_mode="none",
            )
        )

    theme = [
        ("C_DARK", 3422.890, 3425.940, "어두운공간이무섭다", "빛_문제"),
        ("C_DARK_REACT", 3427.540, 3428.940, "어둠리액션", "인물_공포"),
        ("C_POWER", 3502.090, 3505.990, "전원발견", "빛_해결행동"),
        ("C_SWITCH", 3506.540, 3507.940, "전원작동", "빛_전환"),
        ("C_SHOW", 3510.340, 3513.940, "불켜지고혼자생쇼", "공포직후코미디"),
        ("C_RELIEF", 3520.540, 3522.940, "긴장이완", "인물_회복"),
        ("C_EVAL_LIGHT", 4581.940, 4583.940, "광원을잘활용", "평가_강점"),
        ("C_EVAL_GAME", 4584.790, 4585.940, "게임요소로작동", "평가_근거"),
        ("C_EVAL_MOVIE", 4591.090, 4599.940, "영화의공간기대", "평가_비교"),
        ("C_EVAL_WEIRD", 4599.990, 4601.940, "기괴한공간감", "평가_기대"),
        ("C_EVAL_MISS", 4601.941, 4603.940, "그느낌은약했다", "평가_한계"),
        ("C_ORDINARY", 4604.740, 4607.940, "평범한방", "평가_반례"),
        ("C_ORDINARY_FEEL", 4608.690, 4609.940, "평범하게느껴짐", "평가_반례"),
        ("C_LIGHT_PLEASE", 4610.640, 4611.940, "그래도불켜줘", "평가직후캐릭터아이러니"),
        ("C_NOT_SCARED", 4790.340, 4793.940, "무서워서끝내는건아님", "엔딩_허세"),
        ("C_WAIT", 4920.340, 4921.940, "잠깐만", "엔딩_균열"),
        ("C_TENSE", 4922.490, 4923.940, "너무긴장했다", "엔딩_자백"),
    ]
    for values in theme:
        cursor = append_linked(rows, seq, cursor, *values)

    counts: Counter[str] = Counter()
    for item in rows:
        counts[item["sequence"]] += 1
        item["order"] = str(counts[item["sequence"]])
    validate_rows(rows)
    return rows


DECISIONS = [
    ("V9_01", "CAL_A", "v8 훅", "remove", "28.3초 소리·심리·빛 설명 세 문장", "전부 제외", "논지 나열보다 사건의 감정 피크를 먼저 준다", "v8 HOOK_01~03"),
    ("V9_02", "CAL_A", "v7 조우", "keep", "12.9초 조우·비명·사망", "하나의 훅 미니 사건", "발견부터 결과까지 즉시 이해된다", "3022.900~3035.800"),
    ("V9_03", "CAL_A", "초반 설명", "compress", "동기·리미널 설명·환경 설정 약 74초", "동기와 체험 조건 18.606초", "중복 설명을 버리고 실제 진입을 31.506초로 당긴다", "42.535~53.240; 117.419~125.320"),
    ("V9_04", "CAL_A", "초반 미래 플레이 삽입", "remove", "본편 진입 전 408~3513초의 미래 플레이 V2 6컷", "전부 제외하고 동시대 셋업 원본 화면 유지", "콜드오픈 뒤에는 처음으로 돌아왔다는 시간 흐름을 깨지 않는다", "사용자 피드백·A_V2_* 6컷"),
    ("V9_05", "CAL_B", "v8 B10", "compress", "120.531초 장기 추격", "발견·도주·막힘·탄원·결과 약 74초", "반복 달리기와 반복 탄원을 문장 단위로 제거한다", "2082.861~2275.940 선별"),
    ("V9_06", "CAL_B", "공포 직후 리액션", "keep", "분석 논지 우선으로 코미디 약화", "웃음·아몬드워터·자기격려 보존", "김실버의 공포→붕괴→회복 캐릭터를 되살린다", "2239.739~2275.940 선별"),
    ("V9_07", "CAL_B", "반복 달리기", "remove", "2102.485~2115.740 재확인", "전부 제외", "같은 상태를 반복하고 새 사건이 없다", "SRT·v8 B10"),
    ("V9_08", "CAL_B", "반복 거리 설명", "remove", "2182.380~2193.067", "전부 제외", "막다른길 사건을 늦춘다", "SRT·v8 B10"),
    ("V9_09", "CAL_B", "반복 탄원", "remove", "2225.941~2233.940", "전부 제외", "탄원 피크 이후 같은 감정이 반복된다", "SRT·v8 B10"),
    ("V9_10", "CAL_C", "v8 B12", "compress", "주차장 화면의 백룸·리미널 설명 49.676초", "관심→게임 체험 16.683초", "백룸 팬과 관련된 정보는 남기되 강의처럼 늘어놓지 않는다", "2673.540~2720.723 선별"),
    ("V9_11", "CAL_C", "B12 주차장 화면", "cutaway", "관련 없는 주차장 화면", "회고 시점보다 앞선 빈 공간·반복 복도 V2", "주제를 화면으로 증명하되 미래 플레이를 선공개하지 않는다", "408.840~1334.052의 C_V2_* 4컷"),
    ("V9_12", "CAL_C", "v8 B14 관찰시설 논지", "remove", "회사·관찰시설 추정", "음성 논지 제외", "근거가 약한 별도 세계관 논지를 제거한다", "3527.090~3549.940; 관찰창은 무음 화면만 사용"),
    ("V9_13", "CAL_C", "v8 B17 소리장치 논지", "remove", "진행 신호 재해석", "전체 제외", "공간 기대와 빛의 공포라는 중심 논지에 집중한다", "4694.190~4735.940"),
    ("V9_14", "CAL_C", "평가와 엔딩", "keep", "분석과 리액션이 분리", "광원 강점→공간 한계→불켜줘→긴장 자백", "평가 직후 캐릭터 아이러니로 메시지를 감정에 붙인다", "4581.940~4923.940 선별"),
]


def validate_rows(rows: list[dict[str, str]]) -> None:
    expected_sequences = {
        "CAL_A_훅과빠른진입",
        "CAL_B_추격과코미디",
        "CAL_C_주제회수와아이러니",
    }
    if {item["sequence"] for item in rows} != expected_sequences:
        raise ValueError("캘리브레이션 시퀀스 구성이 다름")
    ids = [item["cut_id"] for item in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("중복 cut_id")
    for item in rows:
        if float(item["end"]) <= float(item["start"]):
            raise ValueError(f"0 이하 길이: {item['cut_id']}")
        if item["audio_mode"] == "none" and item["video_track"] != "2":
            raise ValueError(f"무음 컷어웨이는 V2여야 함: {item['cut_id']}")


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
    parser.add_argument("cutlist_output", type=Path)
    parser.add_argument("decision_output", type=Path)
    args = parser.parse_args()
    rows = build_rows()
    decisions = [dict(zip(DECISION_FIELDS, values)) for values in DECISIONS]
    write_csv(args.cutlist_output, rows, CUT_FIELDS)
    write_csv(args.decision_output, decisions, DECISION_FIELDS)
    print(f"[v9-calibration] cuts={len(rows)}, decisions={len(decisions)}, sequences=3")


if __name__ == "__main__":
    main()
