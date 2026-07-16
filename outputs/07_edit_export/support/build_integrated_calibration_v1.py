#!/usr/bin/env python3
# Lifecycle: task-scoped
# Cleanup: keep until integrated-calibration-v1 is approved or rejected; then retain the decision CSV and remove this builder.
"""Build the approved-plan opening, middle, and ending calibration package."""

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
    "beat_id",
    "story_function",
    "action",
    "candidate_range",
    "selected_ranges",
    "removed_ranges",
    "cut_count",
    "selected_duration",
    "longest_cut_id",
    "longest_cut_seconds",
    "longest_reason",
    "screen_boundary",
    "audio_boundary",
    "rule_ids",
    "reason",
    "evidence",
]
PROFILE_FIELDS = ["section", "mode", "waive", "justification"]

SEQ_A = "CAL_A_훅과첫진입"
SEQ_B = "CAL_B_빛변화와코미디"
SEQ_C = "CAL_C_적응과공포잔존"
SOURCE_FPS = 60


def row(
    sequence: str,
    cut_id: str,
    start: float,
    end: float,
    label: str,
    role: str,
    timeline_start: float | None = None,
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


def source_duration_frames(item: dict[str, str]) -> int:
    return round(float(item["end"]) * SOURCE_FPS) - round(float(item["start"]) * SOURCE_FPS)


def linked_timeline_start(rows: list[dict[str, str]], sequence: str, cut_id: str) -> float:
    cursor = 0
    for item in rows:
        if item["sequence"] != sequence or item["audio_mode"] != "linked":
            continue
        if item["cut_id"] == cut_id:
            return cursor / SOURCE_FPS
        cursor += source_duration_frames(item)
    raise ValueError(f"linked cut not found: {sequence}/{cut_id}")


def linked_timeline_end(rows: list[dict[str, str]], sequence: str) -> float:
    frames = sum(
        source_duration_frames(item)
        for item in rows
        if item["sequence"] == sequence and item["audio_mode"] == "linked"
    )
    return frames / SOURCE_FPS


def apply_order_and_validate(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    counts: Counter[str] = Counter()
    for item in rows:
        counts[item["sequence"]] += 1
        item["order"] = str(counts[item["sequence"]])
    validate_rows(rows)
    return rows


def build_rows_r2() -> list[dict[str, str]]:
    rows = [
        # A opening: E08 is used once as a 12.567 second cold open. The story then
        # resets to E01 and advances to E02 without future-playback cutaways.
        row(SEQ_A, "A_HOOK_CONTEXT", 2336.323, 2341.940, "엔티티를두고도발", "훅_문맥_위협확인"),
        row(SEQ_A, "A_HOOK_BOAST", 2342.740, 2344.940, "NPC수준허세", "훅_피크_허세"),
        row(SEQ_A, "A_HOOK_TURN", 2346.190, 2350.940, "근데무서워빨리가", "훅_결과_즉시붕괴"),
        row(SEQ_A, "A_MOTIVE_MOVIE", 43.616, 46.860, "영화백룸을보고옴", "본편리셋_E01_동기"),
        row(SEQ_A, "A_MOTIVE_GAME", 47.824, 52.095, "원래게임이먼저있었음", "E01_매체전환"),
        row(SEQ_A, "A_ENTRY_REVEAL", 322.421, 326.250, "로비에서백룸화면으로", "E02_진입문턱"),
        row(SEQ_A, "A_ENTRY_EXPERIENCE", 337.434, 343.438, "영화첫장면같은실제공간", "E02_첫공간보상"),

        # B middle: E08 is not repeated. E10 alone supplies problem, action,
        # visible state change, and comedy payoff.
        row(SEQ_B, "B_DARK_PROBLEM", 3422.890, 3426.000, "어두운공간이무섭다", "E10_문제_암흑"),
        row(SEQ_B, "B_POWER_ACTION", 3502.090, 3507.953, "전원위치발견과작동", "E10_행동_규칙발견"),
        row(SEQ_B, "B_COMEDY_SETUP", 3510.340, 3513.940, "나혼자공포게임", "E10_결과_밝아짐"),
        row(SEQ_B, "B_COMEDY_PAYOFF", 3520.540, 3522.940, "혼자생쇼했네", "E10_이완_코미디"),

        # C ending: E11 states the adaptation paradox, then E14 pays it off as
        # a denial, bodily tension, sign-off, and confession.
        row(SEQ_C, "C_ADAPT", 4270.832, 4275.780, "반복할수록무서움감소", "E11_적응"),
        row(SEQ_C, "C_REPEAT", 4342.274, 4347.935, "반복할수록익숙해짐", "E11_학습회수"),
        row(SEQ_C, "C_FIRST_SITUATION", 4348.729, 4351.259, "처음상황이되면", "E11_반전설정"),
        row(SEQ_C, "C_FEAR_REMAINS", 4352.059, 4354.669, "여전히공포감이남음", "E11_메시지회수"),
        row(SEQ_C, "C_NOT_SCARED", 4790.368, 4793.921, "무서워서끝내는건아님", "E14_허세_부인"),
        row(SEQ_C, "C_TENSE_BODY", 4864.420, 4866.190, "몸이너무긴장됨", "E14_허세붕괴"),
        row(SEQ_C, "C_SIGNOFF", 4914.041, 4915.292, "오늘방송여기까지", "E14_중단"),
        row(SEQ_C, "C_CONFESSION", 4920.340, 4924.050, "잠깐만너무긴장했어", "E14_최종자백"),
        # The source is black during the last linked audio. A prior, unused shot
        # from the same ending room covers it without inventing a new event.
        row(
            SEQ_C,
            "C_V2_ENDING_ROOM",
            4873.940,
            4878.917,
            "종료공간연속화면",
            "무음V2_동일사건_J컷",
            21.072,
            video_track=2,
            audio_mode="none",
        ),
    ]

    return apply_order_and_validate(rows)


def build_rows_r3() -> list[dict[str, str]]:
    rows = [
        # A: keep the approved E08 event, but expose the creature during the
        # boast and split fear from escape at complete SRT cue boundaries.
        row(SEQ_A, "A_HOOK_CONTEXT", 2336.323, 2341.940, "엔티티를두고도발", "훅_문맥_위협확인"),
        row(SEQ_A, "A_HOOK_BOAST", 2342.740, 2344.940, "NPC수준허세", "훅_피크_허세"),
        row(SEQ_A, "A_HOOK_FEAR", 2346.190, 2347.940, "근데무서워", "훅_반전_공포인정"),
        row(SEQ_A, "A_HOOK_ESCAPE", 2348.115, 2350.940, "빨리가", "훅_결과_도주"),
        row(SEQ_A, "A_MOTIVE_MOVIE", 43.616, 46.860, "영화백룸을보고옴", "본편리셋_E01_동기"),
        row(SEQ_A, "A_MOTIVE_GAME", 47.824, 52.095, "원래게임이먼저있었음", "E01_매체전환"),
        row(SEQ_A, "A_ENTRY_REVEAL", 322.421, 326.250, "로비에서백룸화면으로", "E02_진입문턱"),
        row(SEQ_A, "A_ENTRY_EXPERIENCE", 337.434, 343.438, "영화첫장면같은실제공간", "E02_첫공간보상"),

        # B: restore the omitted switch action and hold the bright result
        # before the next spoken cue begins.
        row(SEQ_B, "B_DARK_PROBLEM", 3422.890, 3426.000, "어두운공간이무섭다", "E10_문제_암흑"),
        row(SEQ_B, "B_POWER_DISCOVERY", 3502.090, 3507.953, "전원위치발견", "E10_행동_규칙발견"),
        row(SEQ_B, "B_COMEDY_SETUP", 3510.340, 3513.940, "나혼자공포게임", "E10_코미디_설정"),
        row(SEQ_B, "B_POWER_SWITCH", 3513.940, 3516.340, "전원스위치실행", "E10_행동_실제조작"),
        row(SEQ_B, "B_COMEDY_PAYOFF", 3520.540, 3523.740, "혼자생쇼와밝은결과", "E10_결과_코미디_밝아짐"),

        # C: snap two risky speech boundaries to their complete SRT cues and
        # add 0.4 seconds of same-room visual breathing room after confession.
        row(SEQ_C, "C_ADAPT", 4270.832, 4275.780, "반복할수록무서움감소", "E11_적응"),
        row(SEQ_C, "C_REPEAT", 4342.274, 4347.935, "반복할수록익숙해짐", "E11_학습회수"),
        row(SEQ_C, "C_FIRST_SITUATION", 4348.729, 4351.259, "처음상황이되면", "E11_반전설정"),
        row(SEQ_C, "C_FEAR_REMAINS", 4352.059, 4354.669, "여전히공포감이남음", "E11_메시지회수"),
        row(SEQ_C, "C_NOT_SCARED", 4790.368, 4793.921, "무서워서끝내는건아님", "E14_허세_부인"),
        row(SEQ_C, "C_TENSE_BODY", 4864.365, 4865.940, "지금너무긴장됨", "E14_허세붕괴"),
        row(SEQ_C, "C_SIGNOFF", 4914.090, 4915.940, "오늘방송여기까지", "E14_중단"),
        row(SEQ_C, "C_CONFESSION", 4920.340, 4924.050, "잠깐만너무긴장했어", "E14_최종자백"),
    ]

    rows.extend(
        [
            row(
                SEQ_A,
                "A_V2_HOOK_BOAST_ENTITY",
                2336.500,
                2338.700,
                "NPC허세중엔티티근접화면",
                "무음V2_동일사건_위협강조",
                linked_timeline_start(rows, SEQ_A, "A_HOOK_BOAST"),
                video_track=2,
                audio_mode="none",
            ),
            row(
                SEQ_C,
                "C_V2_ENDING_ROOM",
                4873.940,
                4879.907,
                "종료공간연속화면과여운",
                "무음V2_동일사건_J컷_엔딩홀드",
                linked_timeline_start(rows, SEQ_C, "C_SIGNOFF"),
                video_track=2,
                audio_mode="none",
            ),
        ]
    )
    return apply_order_and_validate(rows)


def build_rows_r4() -> list[dict[str, str]]:
    rows = [
        # A: begin on the complete "뭐? 뭐?" reveal cue, keep only the first
        # complete taunt phrase at a measured silence boundary, and let the
        # source action progress without replaying the creature on V2.
        row(SEQ_A, "A_HOOK_REVEAL", 2333.865, 2336.223, "문앞엔티티접근", "훅_문맥_위협등장"),
        row(SEQ_A, "A_HOOK_TAUNT", 2336.323, 2338.837, "못들어오잖아도발", "훅_행동_규칙확인"),
        row(SEQ_A, "A_HOOK_BOAST", 2342.740, 2344.940, "NPC수준허세", "훅_피크_허세"),
        row(SEQ_A, "A_HOOK_FEAR", 2346.190, 2347.940, "근데무서워", "훅_반전_공포인정"),
        row(SEQ_A, "A_HOOK_ESCAPE", 2348.115, 2351.207, "빨리가와짧은잔향", "훅_결과_도주"),
        row(SEQ_A, "A_MOTIVE_MOVIE", 43.616, 46.860, "영화백룸을보고옴", "본편리셋_E01_동기"),
        row(SEQ_A, "A_MOTIVE_GAME", 47.824, 52.095, "원래게임이먼저있었음", "E01_매체전환"),
        row(SEQ_A, "A_ENTRY_REVEAL", 322.421, 326.250, "로비에서백룸화면으로", "E02_진입문턱"),
        row(SEQ_A, "A_ENTRY_EXPERIENCE", 337.434, 343.438, "영화첫장면같은실제공간", "E02_첫공간보상"),

        # B: remove the repeated viewer direction and begin on the creator's
        # discovery reaction. Preserve the actual switch and bright-room hold.
        row(SEQ_B, "B_DARK_PROBLEM", 3422.890, 3426.000, "어두운공간이무섭다", "E10_문제_암흑"),
        row(SEQ_B, "B_POWER_DISCOVERY", 3506.540, 3507.940, "전원위치발견반응", "E10_행동_규칙발견"),
        row(SEQ_B, "B_COMEDY_SETUP", 3510.340, 3513.940, "나혼자공포게임", "E10_코미디_설정"),
        row(SEQ_B, "B_POWER_SWITCH", 3513.940, 3516.340, "전원스위치실행", "E10_행동_실제조작"),
        row(SEQ_B, "B_COMEDY_PAYOFF", 3520.540, 3523.740, "혼자생쇼와밝은결과", "E10_결과_코미디_밝아짐"),

        # C: remove the redundant near-black adaptation sentence and the
        # context-dependent "해주고 싶어요" cue. The remaining spine states
        # familiarity, surviving fear, denial, sign-off, and final confession.
        row(SEQ_C, "C_REPEAT", 4342.274, 4347.935, "반복할수록익숙해짐", "E11_학습회수"),
        row(SEQ_C, "C_FIRST_SITUATION", 4348.729, 4351.259, "처음상황이되면", "E11_반전설정"),
        row(SEQ_C, "C_FEAR_REMAINS", 4352.059, 4354.669, "여전히공포감이남음", "E11_메시지회수"),
        row(SEQ_C, "C_NOT_SCARED", 4790.368, 4793.921, "무서워서끝내는건아님", "E14_허세_부인"),
        row(SEQ_C, "C_SIGNOFF", 4914.090, 4915.940, "오늘방송여기까지", "E14_중단"),
        row(SEQ_C, "C_CONFESSION", 4920.340, 4924.050, "잠깐만너무긴장했어", "E14_최종자백"),
    ]

    rows.extend(
        [
            # An already-past E11 corridor replaces the first two seconds of
            # another similar corridor, turning repetition into visible recall.
            row(
                SEQ_C,
                "C_V2_REPEAT_FLASHBACK",
                4272.000,
                4274.000,
                "이전통로회고화면",
                "무음V2_과거화면_반복시각화",
                linked_timeline_start(rows, SEQ_C, "C_REPEAT"),
                video_track=2,
                audio_mode="none",
            ),
            # Split the black ending cover at the semantic cut from sign-off to
            # confession. Both shots are earlier views of the same ending room.
            row(
                SEQ_C,
                "C_V2_SIGNOFF_ROOM",
                4864.365,
                4866.215,
                "종료선언이전방화면",
                "무음V2_동일공간_종료선언",
                linked_timeline_start(rows, SEQ_C, "C_SIGNOFF"),
                video_track=2,
                audio_mode="none",
            ),
            row(
                SEQ_C,
                "C_V2_CONFESSION_ROOM",
                4873.940,
                4878.050,
                "자백이전방화면과여운",
                "무음V2_동일공간_자백_엔딩홀드",
                linked_timeline_start(rows, SEQ_C, "C_CONFESSION"),
                video_track=2,
                audio_mode="none",
            ),
        ]
    )
    return apply_order_and_validate(rows)


def build_rows(revision: str = "r2") -> list[dict[str, str]]:
    if revision == "r2":
        return build_rows_r2()
    if revision == "r3":
        return build_rows_r3()
    if revision == "r4":
        return build_rows_r4()
    raise ValueError(f"unsupported revision: {revision}")


def linked_duration(rows: list[dict[str, str]], sequence: str) -> float:
    return sum(
        float(item["end"]) - float(item["start"])
        for item in rows
        if item["sequence"] == sequence and item["audio_mode"] == "linked"
    )


def build_decisions(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    durations = {sequence: linked_duration(rows, sequence) for sequence in (SEQ_A, SEQ_B, SEQ_C)}
    values = [
        (
            "ICV1_01", SEQ_A, "A_HOOK", "백룸 규칙·캐릭터·코미디를 즉시 약속", "redesign",
            "E08 00:38:18.118~00:39:14.940", "2336.323~2341.940|2342.740~2344.940|2346.190~2350.940",
            "문 규칙 설명 반복·39:11 이후 공략 설명", "3", "12.567", "A_HOOK_CONTEXT", "5.617",
            "엔티티가 창 너머에 보이는 문맥을 잃지 않아 최장 유지",
            "2336.5 엔티티 가시→2342.8 방 이탈→2350.8 창 너머 재등장",
            "SRT 정렬 -0.05초; 각 끝은 원본 무음 또는 문장 종결 구간",
            "EDIT-001|EDIT-003|EDIT-004", "훅과 중간 사건 중복 없이 10~16초 미니 사건을 만든다",
            "source frames 2336.5/2342.8/2350.8; original audio decode; E08",
        ),
        (
            "ICV1_02", SEQ_A, "A_RESET", "콜드오픈 뒤 E01로 시간 리셋", "compress",
            "E01 00:00:42.535~00:01:28.240", "43.616~46.860|47.824~52.095",
            "원작 설명·리미널 정의·체험 조건 반복", "2", "7.515", "A_MOTIVE_GAME", "4.271",
            "영화에서 게임으로 관심이 이동하는 완결 문장",
            "영화 화면과 같은 시점의 원본 화면만 사용; 미래 V2 0개",
            "-35dB 0.18초 무음 경계 43.616/46.860/47.824/52.095",
            "EDIT-002|EDIT-003|EDIT-004", "설명보다 실제 진입을 앞당기되 동기를 잃지 않는다",
            "E01; original audio silence scan",
        ),
        (
            "ICV1_03", SEQ_A, "A_ENTRY", "영화에서 보던 공간을 직접 체험", "compress",
            "E02 00:05:14.940~00:05:47.600", "322.421~326.250|337.434~343.438",
            "로비 대기·긴 무음·반복 감탄", "2", "9.833", "A_ENTRY_EXPERIENCE", "6.004",
            "VHS 공간 이동과 영화 첫 장면 비교가 한 호흡으로 이어짐",
            "322.5 로비→324.1 백룸 화면→337.5 실제 공간",
            "SRT 단일 장문 cue를 원본 무음 5.66/3.63초 구간에서 분해",
            "EDIT-002|EDIT-003", "후보범위 전체 보존 대신 화면 상태 변화와 반응만 남긴다",
            "E02; source frames 322.5/324.1/337.5/343.4; original audio silence scan",
        ),
        (
            "ICV1_04", SEQ_B, "B_LIGHT", "공간 규칙 발견이 공포를 코미디로 전환", "compress",
            "E10 00:57:02.890~00:58:42.940", "3422.890~3426.000|3502.090~3507.953|3510.340~3513.940|3520.540~3522.940",
            "암흑 배회·스크린샷 문제·관찰시설 추정", "4", f"{durations[SEQ_B]:.3f}", "B_POWER_ACTION", "5.863",
            "전원 위치 발견부터 UI 작동까지 실제 상태 변화가 지속됨",
            "3502.2 암흑→3506.6 전원 UI→3510.4 밝아진 공간",
            "SRT 정렬 0.00초; cue 경계와 원본 무음 경계를 함께 사용",
            "EDIT-003|EDIT-005|STORY-003", "훅에 쓴 E08을 반복하지 않고 E10으로 중간 리듬을 대표한다",
            "E10; source frames 3423/3502.2/3506.6/3510.4/3522.9",
        ),
        (
            "ICV1_05", SEQ_C, "C_PARADOX", "익숙해져도 공포가 남는 중심 메시지 회수", "radio",
            "E11 01:11:11.015~01:12:33.940", "4270.832~4275.780|4342.274~4347.935|4348.729~4351.259|4352.059~4354.669",
            "목표 없는 배회·반복 놀람·별도 심리 분석", "4", "15.749", "C_REPEAT", "5.661",
            "적응과 공포 잔존을 연결하는 완결 문장",
            "같은 어두운 통로 사건 안에서 화면 시간이 증가",
            "SRT 정렬 0.00초; 원본 무음 경계로 문장 사이를 분리",
            "EDIT-003|STORY-004", "메시지를 검증 설명이 아니라 실제 발화와 화면으로 읽히게 한다",
            "E11; source frames 4271.1/4275.9/4342.3/4354.0",
        ),
        (
            "ICV1_06", SEQ_C, "C_EXIT", "허세가 몸의 긴장과 중단으로 붕괴", "compress",
            "E14 01:19:50.340~01:22:04.067", "4790.368~4793.921|4864.420~4866.190|4914.041~4915.292|4920.340~4924.050",
            "합방·진행 운영 설명·장시간 정지 화면", "4", "10.284", "C_CONFESSION", "3.710",
            "녹화 종료까지 남은 마지막 긴장 자백을 보존",
            "최종 검은 화면은 같은 종료 공간의 미사용 4873.940~4878.917 V2로만 덮음",
            "원본 끝 4924.067 전 0.017초 여유; SRT보다 실제 파일 길이를 우선",
            "EDIT-003|EDIT-004|STORY-004", "무서워서 끝내는 것이 아니라는 부인을 행동 결과로 반박한다",
            "E14; source frames 4790.4/4864.4/4878.8; original audio decode",
        ),
    ]
    return [dict(zip(DECISION_FIELDS, item)) for item in values]


def build_decisions_r3(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    durations = {sequence: linked_duration(rows, sequence) for sequence in (SEQ_A, SEQ_B, SEQ_C)}
    values = [
        (
            "ICV1R3_01", SEQ_A, "A_HOOK", "백룸 규칙·캐릭터·코미디를 시각적으로 즉시 약속", "redesign",
            "E08 00:38:18.118~00:39:14.940", "2336.323~2341.940|2342.740~2344.940|2346.190~2347.940|2348.115~2350.940|V2 2336.500~2338.700@5.617",
            "2347.940~2348.115 무음 호흡·문 규칙 설명 반복·39:11 이후 공략 설명", "5", f"{durations[SEQ_A] - 17.348:.3f}", "A_HOOK_CONTEXT", "5.617",
            "철창 앞 엔티티와 도발 문장을 함께 보여주는 완결 문맥이므로 유지",
            "2336.5 엔티티 근접→허세 때 동일사건 V2 근접 화면→2346.2 공포 인정→2350.8 창 너머 재등장",
            "SRT 완결 cue 2336.323~2341.940/2342.740~2344.940/2346.190~2347.940/2348.115~2350.940",
            "EDIT-001|EDIT-003|EDIT-004", "사용자 피드백의 훅 디테일 부족을 사건 교체 없이 화면-대사 정렬과 반응 분해로 해결",
            "user feedback 2026-07-15; source frames 2336.5/2338.7/2342.8/2350.8; original audio decode; E08",
        ),
        (
            "ICV1R3_02", SEQ_A, "A_RESET", "콜드오픈 뒤 E01로 시간 리셋", "keep",
            "E01 00:00:42.535~00:01:28.240", "43.616~46.860|47.824~52.095",
            "원작 설명·리미널 정의·체험 조건 반복", "2", "7.515", "A_MOTIVE_GAME", "4.271",
            "영화에서 게임으로 관심이 이동하는 완결 문장",
            "콜드오픈 뒤 영화 화면과 같은 시점의 원본만 사용; 훅 V2는 E08 동일사건 내부에만 제한",
            "-35dB 0.18초 무음 경계 43.616/46.860/47.824/52.095",
            "EDIT-002|EDIT-003|EDIT-004", "전체 느낌이 좋아졌다는 사용자 평가를 반영해 승인된 리셋 구조는 유지",
            "E01; r2 regression; original audio silence scan",
        ),
        (
            "ICV1R3_03", SEQ_A, "A_ENTRY", "영화에서 보던 공간을 직접 체험", "keep",
            "E02 00:05:14.940~00:05:47.600", "322.421~326.250|337.434~343.438",
            "로비 대기·긴 무음·반복 감탄", "2", "9.833", "A_ENTRY_EXPERIENCE", "6.004",
            "VHS 공간 이동과 영화 첫 장면 비교가 한 호흡으로 이어짐",
            "322.5 로비→324.1 백룸 화면→337.5 실제 공간",
            "SRT 단일 장문 cue를 원본 무음 5.66/3.63초 구간에서 분해",
            "EDIT-002|EDIT-003", "전체 구조를 건드리지 않고 훅·중간·엔딩 국소 결함만 수정",
            "E02; source frames 322.5/324.1/337.5/343.4; r2 regression",
        ),
        (
            "ICV1R3_04", SEQ_B, "B_LIGHT", "공간 규칙 발견과 실제 조작이 공포를 코미디로 전환", "improve",
            "E10 00:57:02.890~00:58:42.940", "3422.890~3426.000|3502.090~3507.953|3510.340~3513.940|3513.940~3516.340|3520.540~3523.740",
            "암흑 배회·스크린샷 문제·관찰시설 추정·반복 스위치 조작", "5", f"{durations[SEQ_B]:.3f}", "B_POWER_DISCOVERY", "5.863",
            "전원 위치 발견과 접근이라는 독립 행동을 완결하므로 유지",
            "3423 암흑→3502 발견→3513.94 전원 UI→3516 실제 스위치 변화→3522.9 밝아짐→3523.7 밝은 방 홀드",
            "3513.940~3516.340은 SRT 없는 실제 조작음; 3523.740은 다음 cue 3524.940보다 1.2초 앞",
            "EDIT-003|EDIT-005|STORY-003", "r2에서 누락된 행동→결과 연결을 복구해 갑작스러운 해결 인상을 제거",
            "source frames 3423/3502.2/3513.94/3516.0/3522.9/3523.7; original AV decode",
        ),
        (
            "ICV1R3_05", SEQ_C, "C_PARADOX", "익숙해져도 공포가 남는 중심 메시지 회수", "keep",
            "E11 01:11:11.015~01:12:33.940", "4270.832~4275.780|4342.274~4347.935|4348.729~4351.259|4352.059~4354.669",
            "목표 없는 배회·반복 놀람·별도 심리 분석", "4", "15.749", "C_REPEAT", "5.661",
            "적응과 공포 잔존을 연결하는 완결 문장",
            "같은 어두운 통로 사건 안에서 화면 시간이 증가",
            "SRT 정렬 0.00초; 원본 무음 경계로 문장 사이를 분리",
            "EDIT-003|STORY-004", "사용자 평가상 전체 메시지 흐름은 개선됐으므로 중심 회수 구조를 유지",
            "E11; source frames 4271.1/4275.9/4342.3/4354.0; r2 regression",
        ),
        (
            "ICV1R3_06", SEQ_C, "C_EXIT", "허세가 몸의 긴장과 중단으로 붕괴하고 여운을 남김", "improve",
            "E14 01:19:50.340~01:22:04.067", "4790.368~4793.921|4864.365~4865.940|4914.090~4915.940|4920.340~4924.050|V2 4873.940~4879.907",
            "합방·진행 운영 설명·장시간 정지 화면", "5", f"{durations[SEQ_C] - 15.749:.3f}", "C_CONFESSION", "3.710",
            "마지막 긴장 자백의 반복과 숨이 캐릭터 붕괴를 완결",
            "검은 원본 화면은 동일 종료 공간 V2로 덮고 자백 뒤 0.4초까지 연속 화면 유지",
            "C_TENSE_BODY와 C_SIGNOFF를 SRT cue 경계에 스냅; 원본 끝 4924.067 전 종료",
            "EDIT-003|EDIT-004|STORY-004", "문장 경계 위험과 엔딩의 즉시 종료를 국소 보정",
            "E14; source frames 4790.4/4864.4/4879.25; original audio decode",
        ),
    ]
    return [dict(zip(DECISION_FIELDS, item)) for item in values]


def build_decisions_r4(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    durations = {sequence: linked_duration(rows, sequence) for sequence in (SEQ_A, SEQ_B, SEQ_C)}
    hook_duration = sum(
        float(item["end"]) - float(item["start"])
        for item in rows
        if item["cut_id"].startswith("A_HOOK_")
    )
    c_paradox_duration = sum(
        float(item["end"]) - float(item["start"])
        for item in rows
        if item["cut_id"] in {"C_REPEAT", "C_FIRST_SITUATION", "C_FEAR_REMAINS"}
    )
    c_exit_duration = durations[SEQ_C] - c_paradox_duration
    values = [
        (
            "ICV1R4_01", SEQ_A, "A_HOOK", "위협 등장부터 허세 붕괴까지 한 번의 진행 화면으로 약속", "redesign",
            "E08 00:38:52.000~00:39:11.207", "2333.865~2336.223|2336.323~2338.837|2342.740~2344.940|2346.190~2347.940|2348.115~2351.207",
            "2336.323~2341.940 cue 중 2338.837 이후 반복 도발|r3 동일 엔티티 V2 재사용", "5", f"{hook_duration:.3f}", "A_HOOK_ESCAPE", "3.092",
            "도주 대사 뒤 0.267초 원본 공간음과 창가 엔티티 결과를 보존",
            "2333.9 문앞 반응→2335.5 엔티티 접근→허세로 시선 이탈→2348.2 창가 재등장→2351.2 도주 완료",
            "2333.865~2336.223 완결 cue; 2338.644~2338.837 -35dB 무음에서 도발 문구 종료; 나머지는 완결 cue와 0.267초 결과 잔향",
            "EDIT-001|EDIT-003|EDIT-004", "같은 화면을 반복해 디테일을 가장하지 않고 위협의 접근과 재등장을 시간 순서대로 보여준다",
            "user 90+ target 2026-07-15; source frames 2332.0~2336.5/2342.8/2348.2/2350.8; ffmpeg silencedetect",
        ),
        (
            "ICV1R4_02", SEQ_A, "A_RESET", "콜드오픈 뒤 E01로 시간 리셋", "compress",
            "E01 00:00:42.535~00:01:28.240", "43.616~46.860|47.824~52.095",
            "원작 설명·리미널 정의·체험 조건 반복", "2", "7.515", "A_MOTIVE_GAME", "4.271",
            "영화에서 게임으로 관심이 이동하는 완결 문장",
            "콜드오픈 뒤 영화 화면과 같은 시점의 원본만 사용; 훅 V2 제거",
            "-35dB 0.18초 무음 경계 43.616/46.860/47.824/52.095",
            "EDIT-002|EDIT-003|EDIT-004", "훅 개선이 본편의 시간 리셋 구조를 손상하지 않게 유지한다",
            "E01; r3 regression; original audio silence scan",
        ),
        (
            "ICV1R4_03", SEQ_A, "A_ENTRY", "영화에서 보던 공간을 직접 체험", "radio",
            "E02 00:05:14.940~00:05:47.600", "322.421~326.250|337.434~343.438",
            "로비 대기·긴 무음·반복 감탄", "2", "9.833", "A_ENTRY_EXPERIENCE", "6.004",
            "VHS 공간 이동과 영화 첫 장면 비교가 한 호흡으로 이어짐",
            "322.5 로비→324.1 백룸 화면→337.5 실제 공간",
            "SRT 단일 장문 cue를 원본 무음 5.66/3.63초 구간에서 분해",
            "EDIT-002|EDIT-003", "첫 공간 보상은 실제 화면 변화가 계속되므로 유지한다",
            "E02; source frames 322.5/324.1/337.5/343.4; r3 regression",
        ),
        (
            "ICV1R4_04", SEQ_B, "B_LIGHT", "규칙 발견과 실제 조작이 공포를 코미디로 전환", "compress",
            "E10 00:57:02.890~00:58:42.940", "3422.890~3426.000|3506.540~3507.940|3510.340~3513.940|3513.940~3516.340|3520.540~3523.740",
            "3502.090~3505.990 시청자 위치 설명|암흑 배회|반복 스위치 조작", "5", f"{durations[SEQ_B]:.3f}", "B_COMEDY_SETUP", "3.600",
            "발견 반응을 실제 코미디 질문으로 뒤집는 완결 설정 문장",
            "3423 암흑→3506.6 전원 발견→3513.94 UI→3516 스위치 변화→3522.9 밝아짐",
            "3506.540~3507.940 완결 cue; 3513.940~3516.340 SRT 없는 실제 조작음; 다음 cue 전 1.2초 여유",
            "EDIT-003|EDIT-005|STORY-003", "위치 설명을 제거해 문제→발견→행동→결과를 13.7초로 압축한다",
            "SRT cues 466~469; source frames 3423/3506.6/3513.94/3516.0/3522.9/3523.7; original AV decode",
        ),
        (
            "ICV1R4_05", SEQ_C, "C_PARADOX", "익숙해져도 공포가 남는 중심 메시지 회수", "compress",
            "E11 01:11:11.015~01:12:33.940", "4342.274~4347.935|4348.729~4351.259|4352.059~4354.669|V2 4272.000~4274.000@0.000",
            "4270.832~4275.780 같은 뜻 반복과 첫 1.2초 암전|목표 없는 배회", "4", f"{c_paradox_duration:.3f}", "C_REPEAT", "5.661",
            "익숙함과 공포 잔존을 연결하는 중심 문장이므로 온전히 유지",
            "4272 과거 통로 회고 2초→4344 현재 반복 통로→처음 상황의 어둠으로 진행",
            "세 연결 오디오는 완결 SRT cue; V2는 이미 지나온 E11 화면이며 원본 오디오 비활성",
            "EDIT-003|EDIT-004|STORY-004", "중복 설명을 제거하고 과거 통로 회고로 반복 학습을 화면에서 읽히게 한다",
            "E11 SRT 4342.190~4353.940; source frames 4272/4275.9/4342.3~4353.9; chronology regression",
        ),
        (
            "ICV1R4_06", SEQ_C, "C_EXIT", "부인이 중단과 최종 자백으로 직접 붕괴", "redesign",
            "E14 01:19:50.340~01:22:04.067", "4790.368~4793.921|4914.090~4915.940|4920.340~4924.050|V2 4864.365~4866.215@14.350|V2 4873.940~4878.050@16.200",
            "4864.365~4865.940 앞 문맥 의존 cue|합방·운영 설명|장시간 검은 화면", "5", f"{c_exit_duration:.3f}", "C_CONFESSION", "3.710",
            "반복되는 잠깐만과 긴장 자백이 캐릭터 붕괴를 완결",
            "부인 원본→이전 종료방 앵글 1에서 sign-off→앵글 2에서 자백과 24프레임 여운",
            "연결 오디오는 세 완결 cue; 두 V2는 원본 오디오 비활성; 자백 뒤 정확히 24프레임 유지",
            "EDIT-003|EDIT-004|STORY-004", "문맥이 잘린 중간 문장을 제거해 부인과 최종 자백의 대비를 더 직접적으로 만든다",
            "E14 SRT cues 706/728~730; source frames 4790.4/4864.4~4867.3/4873.9~4878.8; XML frame math",
        ),
    ]
    return [dict(zip(DECISION_FIELDS, item)) for item in values]


AUDIT_SECTION = {
    "A_HOOK_CONTEXT": "HOOK_01",
    "A_HOOK_BOAST": "HOOK_02",
    "A_HOOK_TURN": "HOOK_03",
    "A_MOTIVE_MOVIE": "B01_01",
    "A_MOTIVE_GAME": "B01_02",
    "A_ENTRY_REVEAL": "B01_03",
    "A_ENTRY_EXPERIENCE": "B01_04",
    "B_DARK_PROBLEM": "B02_01",
    "B_POWER_ACTION": "B02_02",
    "B_COMEDY_SETUP": "B02_03",
    "B_COMEDY_PAYOFF": "B02_04",
    "C_ADAPT": "B03_01",
    "C_REPEAT": "B03_02",
    "C_FIRST_SITUATION": "B03_03",
    "C_FEAR_REMAINS": "B03_04",
    "C_NOT_SCARED": "B03_05",
    "C_TENSE_BODY": "B03_06",
    "C_SIGNOFF": "B03_07",
    "C_CONFESSION": "B03_08",
}


def build_audit_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    audit_rows = []
    section_counts: Counter[str] = Counter()
    for item in rows:
        if item["audio_mode"] != "linked":
            continue
        if item["sequence"] == SEQ_A and item["cut_id"].startswith("A_HOOK_"):
            section = "HOOK"
        elif item["sequence"] == SEQ_A:
            section = "B01"
        elif item["sequence"] == SEQ_B:
            section = "B02"
        else:
            section = "B03"
        section_counts[section] += 1
        mapped = dict(item)
        mapped["sequence"] = "INTEGRATED_CALIBRATION_V1"
        mapped["cut_id"] = f"{section}_{section_counts[section]:02d}"
        mapped["order"] = str(len(audit_rows) + 1)
        mapped["timeline_start"] = ""
        audit_rows.append(mapped)
    return audit_rows


def build_profiles() -> list[dict[str, str]]:
    return [
        {"section": "HOOK", "mode": "hook", "waive": "", "justification": ""},
        {"section": "B01", "mode": "compress", "waive": "", "justification": ""},
        {"section": "B02", "mode": "compress", "waive": "", "justification": ""},
        {"section": "B03", "mode": "radio", "waive": "", "justification": ""},
        {"section": "GLOBAL", "mode": "", "waive": "", "justification": ""},
    ]


def validate_rows(rows: list[dict[str, str]]) -> None:
    if {item["sequence"] for item in rows} != {SEQ_A, SEQ_B, SEQ_C}:
        raise ValueError("expected exactly three calibration sequences")
    ids = [item["cut_id"] for item in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate cut_id")
    for item in rows:
        if float(item["end"]) <= float(item["start"]):
            raise ValueError(f"non-positive duration: {item['cut_id']}")
        if item["audio_mode"] == "none" and item["video_track"] != "2":
            raise ValueError(f"silent cutaway must use V2: {item['cut_id']}")

    hook_duration = sum(
        float(item["end"]) - float(item["start"])
        for item in rows
        if item["cut_id"].startswith("A_HOOK_")
    )
    if not 10.0 <= hook_duration <= 16.0:
        raise ValueError(f"hook duration outside 10-16 seconds: {hook_duration:.3f}")

    a_story = [
        float(item["start"])
        for item in rows
        if item["sequence"] == SEQ_A
        and item["audio_mode"] == "linked"
        and not item["cut_id"].startswith("A_HOOK_")
    ]
    if a_story != sorted(a_story):
        raise ValueError("A story does not reset to chronological E01→E02 order")
    for item in rows:
        if item["sequence"] != SEQ_A or item["video_track"] != "2":
            continue
        if item["cut_id"] != "A_V2_HOOK_BOAST_ENTITY":
            raise ValueError(f"A contains an unapproved V2 cutaway: {item['cut_id']}")
        if not 2336.323 <= float(item["start"]) < float(item["end"]) <= 2350.940:
            raise ValueError("A hook V2 must stay inside the same E08 cold-open event")


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    if path.exists():
        raise FileExistsError(f"output already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, quoting=csv.QUOTE_ALL, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("cutlist_output", type=Path)
    parser.add_argument("decision_output", type=Path)
    parser.add_argument("audit_cutlist_output", type=Path)
    parser.add_argument("quality_profile_output", type=Path)
    parser.add_argument("--revision", choices=("r2", "r3", "r4"), default="r2")
    args = parser.parse_args()

    rows = build_rows(args.revision)
    write_csv(args.cutlist_output, rows, CUT_FIELDS)
    if args.revision == "r4":
        decisions = build_decisions_r4(rows)
    elif args.revision == "r3":
        decisions = build_decisions_r3(rows)
    else:
        decisions = build_decisions(rows)
    write_csv(args.decision_output, decisions, DECISION_FIELDS)
    write_csv(args.audit_cutlist_output, build_audit_rows(rows), CUT_FIELDS)
    write_csv(args.quality_profile_output, build_profiles(), PROFILE_FIELDS)
    print(
        f"[integrated-calibration-v1 {args.revision}] "
        f"cuts={len(rows)} linked={sum(item['audio_mode'] == 'linked' for item in rows)} "
        f"overlays={sum(item['audio_mode'] == 'none' for item in rows)} decisions={len(decisions)}"
    )


if __name__ == "__main__":
    main()
