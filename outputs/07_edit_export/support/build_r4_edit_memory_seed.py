#!/usr/bin/env python3
"""Build the reproducible r4 edit-memory migration batch.

Lifecycle: task-scoped output reproducibility support.
Cleanup: remove only after the r4 seed and its migrated memory are superseded.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


SCHEMA_VERSION = 1
REVISION_ID = "integrated-calibration-v1-r4"
OCCURRED_AT = "2026-07-15T09:20:00+00:00"


def event(event_id, event_type, aggregate_type, aggregate_id, payload, revision_id=None):
    value = {
        "event_id": event_id,
        "event_type": event_type,
        "aggregate_type": aggregate_type,
        "aggregate_id": aggregate_id,
        "occurred_at": OCCURRED_AT,
        "payload": payload,
    }
    if revision_id is not None:
        value["revision_id"] = revision_id
    return value


def continuity_risk(source_gap):
    gap = abs(source_gap)
    if gap >= 120:
        return 0.95
    if gap >= 30:
        return 0.8
    if gap >= 5:
        return 0.45
    return 0.15


def build(cutlist_path):
    with cutlist_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    events = [
        event(
            "r4-atom-hook-taunt-cue",
            "source_atom.registered",
            "source_atom",
            "utterance-2336.323-2341.940",
            {
                "source_id": "backrooms_20260630",
                "source_in": 2336.323,
                "source_out": 2341.940,
                "sentence_complete_at": 2341.940,
                "speaker": "김실버",
                "scene_id": "entity-door-taunt",
                "story_function": "threat_rule_taunt",
                "emotion": "bravado",
                "transcript": "범벼 범벼 너 못들어오잖아 뭐 범벼봐 인식도 못하죠?",
                "safe_cut_points": [2336.323, 2341.940],
            },
        ),
        event(
            "r3-revision-historical",
            "revision.created",
            "revision",
            "integrated-calibration-v1-r3",
            {
                "source_id": "backrooms_20260630",
                "parent_revision_id": None,
                "hypothesis": "훅 디테일을 동일 사건 화면과 반응 분해로 강화한다",
                "status": "superseded",
            },
            revision_id="integrated-calibration-v1-r3",
        ),
        event(
            "r4-revision-created",
            "revision.created",
            "revision",
            REVISION_ID,
            {
                "source_id": "backrooms_20260630",
                "parent_revision_id": "integrated-calibration-v1-r3",
                "hypothesis": "위협의 접근과 재등장을 압축하고 세 대표 장면으로 영상 방향을 검증한다",
                "status": "rejected",
            },
            revision_id=REVISION_ID,
        ),
    ]

    beat_specs = [
        (
            "r4-beat-a",
            1,
            "위협 등장부터 허세 붕괴까지 훅에서 한 번의 사건으로 전달",
            "문 앞 위협, 허세, 공포 인정, 도주",
            "통제감을 과시함",
            "위협 앞에서 통제감이 무너짐",
        ),
        (
            "r4-beat-b",
            2,
            "어둠 문제를 발견하고 전원을 조작해 코미디 결과까지 연결",
            "문제 발견, 행동, 밝아진 결과",
            "환경을 두려워함",
            "규칙을 직접 조작함",
        ),
        (
            "r4-beat-c",
            3,
            "반복 적응 뒤에도 공포가 남는다는 결론과 자백",
            "학습, 부인, 종료, 자백",
            "적응했다고 주장함",
            "무서웠다고 인정함",
        ),
    ]
    for beat_id, position, purpose, viewer_information, before, after in beat_specs:
        events.append(
            event(
                f"{beat_id}-defined",
                "story_beat.defined",
                "story_beat",
                beat_id,
                {
                    "source_id": "backrooms_20260630",
                    "position": position,
                    "purpose": purpose,
                    "viewer_information": viewer_information,
                    "character_state_before": before,
                    "character_state_after": after,
                    "status": "rejected_revision_intent",
                },
            )
        )

    by_sequence = defaultdict(list)
    for row in rows:
        sequence = row["sequence"]
        cut_id = row["cut_id"]
        payload = {
            "sequence_name": sequence,
            "position": int(row["order"]),
            "source_in": float(row["start"]),
            "source_out": float(row["end"]),
            "label": row["label"],
            "role": row["role"],
            "video_track": int(row["video_track"]),
            "audio_mode": row["audio_mode"] or None,
            "timeline_start": float(row["timeline_start"]) if row["timeline_start"] else None,
        }
        if cut_id == "A_HOOK_TAUNT":
            payload["atom_id"] = "utterance-2336.323-2341.940"
        events.append(
            event(
                f"r4-node-{cut_id.lower()}",
                "timeline.node_added",
                "timeline_node",
                cut_id,
                payload,
                revision_id=REVISION_ID,
            )
        )
        if int(row["video_track"]) == 1:
            by_sequence[sequence].append(row)

    for sequence, primary_rows in by_sequence.items():
        primary_rows.sort(key=lambda row: int(row["order"]))
        for left, right in zip(primary_rows, primary_rows[1:]):
            edge_id = f"{left['cut_id']}_to_{right['cut_id']}"
            gap = float(right["start"]) - float(left["end"])
            events.append(
                event(
                    f"r4-edge-{edge_id.lower()}",
                    "timeline.edge_added",
                    "timeline_edge",
                    edge_id,
                    {
                        "from_node_id": left["cut_id"],
                        "to_node_id": right["cut_id"],
                        "semantic_relation": "unverified_hard_cut_adjacency",
                        "audio_transition": "hard_cut_linked_audio",
                        "continuity_risk": continuity_risk(gap),
                        "evidence": f"sequence={sequence}; source_gap_seconds={gap:.3f}; continuous A/V not agent-observed",
                    },
                    revision_id=REVISION_ID,
                )
            )

    events.extend(
        [
            event(
                "r4-eval-structure-92",
                "evaluation.recorded",
                "evaluation",
                "r4-structure-preflight",
                {
                    "evaluator": "agent",
                    "method": "structure_and_screen_preflight",
                    "scope": "structure_and_screen_only_without_continuous_av_or_premiere",
                    "verdict": "scoped_pass_not_video_quality",
                    "dimensions": {"structure_visual_preflight_score": 92},
                    "evidence": "CURRENT.json pending_calibration.validation; semantic and actual A/V gates were false",
                    "actual_av_observed": False,
                },
                revision_id=REVISION_ID,
            ),
            event(
                "r4-eval-user-rejection",
                "evaluation.recorded",
                "evaluation",
                "r4-user-playback-rejection",
                {
                    "evaluator": "user",
                    "method": "actual_av_playback",
                    "scope": "integrated_calibration_r4_full_review",
                    "verdict": "rejected",
                    "dimensions": {
                        "speech_continuity": "failed",
                        "semantic_clarity": "failed",
                        "production_intent_alignment": "failed",
                    },
                    "evidence": "User reported abrupt cuts, clipped speech, poor line selection, and unclear video intent",
                    "actual_av_observed": True,
                },
                revision_id=REVISION_ID,
            ),
        ]
    )

    feedback_specs = [
        (
            "r4-feedback-overall-rejected",
            "revision",
            REVISION_ID,
            "production_intent_alignment",
            "critical",
            "전체 캘리브레이션",
            "영상 제작 의도와 전달하려는 내용이 영상 자체에서 보이지 않고 단순 컷 모음처럼 느껴짐",
            "사용자 실제 재생 검토",
        ),
        (
            "r4-feedback-speech-hard-cuts",
            "revision",
            REVISION_ID,
            "speech_continuity",
            "critical",
            "전체 캘리브레이션",
            "컷 사이가 뚝뚝 끊기고 말하던 내용이 잘려 사용자가 첫 A/V 결함 탐지자가 됨",
            "연속 A/V에 대한 agent 평가 이벤트 부재",
        ),
        (
            "r4-feedback-hook-mid-cue-cut",
            "timeline_node",
            "A_HOOK_TAUNT",
            "utterance_completeness",
            "critical",
            "CAL_A 훅",
            "2336.323–2341.940 발화 중 2338.837에서 절단해 뒤 문장을 제거함",
            "SRT cue 243과 r4 audit의 cue-internal silence boundary",
        ),
        (
            "r4-feedback-b-semantic-stitch",
            "sequence",
            "CAL_B_빛과스위치코미디",
            "semantic_continuity",
            "high",
            "CAL_B 전체",
            "3422→3506→3510→3513→3520초의 떨어진 발화를 하드컷으로 연결해 행동 인과가 약함",
            "r4 cutlist source ranges",
        ),
        (
            "r4-feedback-c-semantic-stitch",
            "sequence",
            "CAL_C_적응과공포재조명",
            "semantic_continuity",
            "critical",
            "CAL_C 전체",
            "4342→4790→4914→4920초 발화를 조립해 회고와 최종 자백의 맥락이 영상에서 자립하지 못함",
            "r4 cutlist source ranges",
        ),
        (
            "r4-feedback-score-scope",
            "evaluation",
            "r4-structure-preflight",
            "evaluation_scope_integrity",
            "critical",
            "품질 판정",
            "실제 연속 A/V 검토가 없는 92점을 영상 성공 점수처럼 사용함",
            "structure score 92; agent actual A/V observation false; user rejected",
        ),
    ]
    for event_id, target_type, target_id, dimension, severity, scope, observation, evidence in feedback_specs:
        events.append(
            event(
                event_id,
                "feedback.recorded",
                "feedback",
                event_id,
                {
                    "target_type": target_type,
                    "target_id": target_id,
                    "verdict": "reject",
                    "dimension": dimension,
                    "severity": severity,
                    "scope": scope,
                    "observation": observation,
                    "evidence": evidence,
                    "persists_until": "superseded_by_verified_fix_on_descendant_revision",
                },
                revision_id=REVISION_ID,
            )
        )

    for name, note in [
        ("working", "r4 rejected; a new working baseline has not been selected"),
        ("preferred", "no preferred candidate after r4 rejection"),
        ("approved", "no user-approved edit baseline exists"),
    ]:
        events.append(
            event(
                f"r4-baseline-{name}-cleared",
                "baseline.set",
                "baseline",
                name,
                {"name": name, "revision_id": None, "note": note},
            )
        )
    return {"schema_version": SCHEMA_VERSION, "events": events}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cutlist", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    batch = build(args.cutlist)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(batch, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(args.output), "events": len(batch["events"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
