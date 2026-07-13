#!/usr/bin/env python3
"""Audit cut-density consistency without deciding creative quality.

The tool reads a canonical, single-sequence content cutlist and a per-section
quality profile. It reports long-cut and density-review triggers. Thresholds are
review lines, not target cut lengths.
"""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path


MODE_THRESHOLDS = {
    "compress": (6.0, 12.0),
    "radio": (10.0, 18.0),
    "breath": (18.0, 45.0),
    "hook": (15.0, 30.0),
}
KNOWN_CODES = {
    "AVG_LONG",
    "MAX_LONG",
    "SINGLE_BLOCK",
    "LATE_DENSITY_CLIFF",
    "MISSING_PROFILE",
    "MISSING_CUTS",
}


@dataclass(frozen=True)
class Cut:
    cut_id: str
    section: str
    start: float
    end: float
    label: str

    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass(frozen=True)
class Profile:
    section: str
    mode: str
    waive: frozenset[str]
    justification: str


@dataclass(frozen=True)
class Finding:
    section: str
    code: str
    status: str
    detail: str
    justification: str = ""


def parse_seconds(value: str) -> float:
    parts = [float(part) for part in value.strip().split(":")]
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    raise ValueError(f"시각 형식 오류: {value}")


def section_from_cut_id(cut_id: str) -> str:
    if cut_id.startswith(("PART_", "FULL_")):
        raise ValueError("멀티시퀀스 cut_id는 감사 입력으로 사용할 수 없음")
    if cut_id.startswith("HOOK"):
        return "HOOK"
    match = re.match(r"^(B\d{2})(?:_|$)", cut_id)
    if not match:
        raise ValueError(f"구간을 판독할 수 없는 cut_id: {cut_id}")
    return match.group(1)


def load_cuts(path: Path) -> list[Cut]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("컷리스트가 비어 있음")
    sequences = {row.get("sequence", "").strip() for row in rows}
    if len(sequences) > 1:
        raise ValueError("여러 시퀀스가 있는 CSV는 감사 입력으로 사용할 수 없음")
    cuts = []
    seen = set()
    for index, row in enumerate(rows, 1):
        cut_id = (row.get("cut_id") or "").strip()
        if not cut_id or cut_id in seen:
            raise ValueError(f"비어 있거나 중복된 cut_id: {cut_id!r}")
        start = parse_seconds(row["start"])
        end = parse_seconds(row["end"])
        if end <= start:
            raise ValueError(f"0 이하 길이 컷 {index}: {cut_id}")
        seen.add(cut_id)
        cuts.append(
            Cut(
                cut_id=cut_id,
                section=section_from_cut_id(cut_id),
                start=start,
                end=end,
                label=(row.get("label") or cut_id).strip(),
            )
        )
    return cuts


def load_profiles(path: Path) -> dict[str, Profile]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    profiles = {}
    for row in rows:
        section = (row.get("section") or "").strip()
        mode = (row.get("mode") or "").strip().lower()
        waiver = frozenset(
            code.strip()
            for code in (row.get("waive") or "").split("|")
            if code.strip()
        )
        justification = (row.get("justification") or "").strip()
        if not section or section in profiles:
            raise ValueError(f"비어 있거나 중복된 profile section: {section!r}")
        if section != "GLOBAL" and mode not in MODE_THRESHOLDS:
            raise ValueError(f"알 수 없는 mode: {section}={mode}")
        unknown = waiver - KNOWN_CODES
        if unknown:
            raise ValueError(f"알 수 없는 waive 코드: {section}={sorted(unknown)}")
        if waiver and not justification:
            raise ValueError(f"waive에는 justification이 필요함: {section}")
        profiles[section] = Profile(section, mode, waiver, justification)
    return profiles


def grouped_metrics(cuts: list[Cut]) -> dict[str, dict]:
    grouped: dict[str, list[Cut]] = {}
    for cut in cuts:
        grouped.setdefault(cut.section, []).append(cut)
    metrics = {}
    for section, group in grouped.items():
        total = sum(cut.duration for cut in group)
        longest = max(group, key=lambda cut: cut.duration)
        metrics[section] = {
            "cuts": len(group),
            "total": total,
            "average": total / len(group),
            "maximum": longest.duration,
            "longest_id": longest.cut_id,
        }
    return metrics


def _finding(
    section: str,
    code: str,
    detail: str,
    profile: Profile | None,
) -> Finding:
    waived = profile is not None and code in profile.waive
    return Finding(
        section=section,
        code=code,
        status="WAIVED" if waived else "REVIEW",
        detail=detail,
        justification=profile.justification if waived else "",
    )


def audit(cuts: list[Cut], profiles: dict[str, Profile]) -> tuple[dict[str, dict], list[Finding]]:
    metrics = grouped_metrics(cuts)
    findings: list[Finding] = []

    for section, values in sorted(metrics.items()):
        profile = profiles.get(section)
        if profile is None:
            findings.append(
                _finding(section, "MISSING_PROFILE", "구간 프로필이 없음", None)
            )
            continue
        avg_warn, max_warn = MODE_THRESHOLDS[profile.mode]
        if values["average"] > avg_warn:
            findings.append(
                _finding(
                    section,
                    "AVG_LONG",
                    f"평균 {values['average']:.2f}초 > {avg_warn:.2f}초",
                    profile,
                )
            )
        if values["maximum"] > max_warn:
            findings.append(
                _finding(
                    section,
                    "MAX_LONG",
                    f"최장 {values['maximum']:.2f}초({values['longest_id']}) > {max_warn:.2f}초",
                    profile,
                )
            )
        if (
            profile.mode in {"compress", "radio"}
            and values["cuts"] == 1
            and values["total"] > 8.0
        ):
            findings.append(
                _finding(
                    section,
                    "SINGLE_BLOCK",
                    f"{values['total']:.2f}초 구간이 한 컷으로만 구성됨",
                    profile,
                )
            )

    for section, profile in profiles.items():
        if section != "GLOBAL" and section not in metrics:
            findings.append(
                _finding(section, "MISSING_CUTS", "프로필 구간에 컷이 없음", profile)
            )

    def weighted_average(lo: int, hi: int) -> float | None:
        selected = [
            values
            for section, values in metrics.items()
            if re.fullmatch(r"B\d{2}", section) and lo <= int(section[1:]) <= hi
        ]
        count = sum(values["cuts"] for values in selected)
        if not count:
            return None
        return sum(values["total"] for values in selected) / count

    early = weighted_average(1, 6)
    late = weighted_average(13, 18)
    if early and late and late > early * 1.5:
        profile = profiles.get("GLOBAL")
        findings.append(
            _finding(
                "GLOBAL",
                "LATE_DENSITY_CLIFF",
                f"후반 {late:.2f}초/컷 > 초반 {early:.2f}초/컷 × 1.5",
                profile,
            )
        )

    return metrics, findings


def render_report(
    cutlist: Path,
    profile_path: Path,
    metrics: dict[str, dict],
    findings: list[Finding],
) -> str:
    reviews = [finding for finding in findings if finding.status == "REVIEW"]
    status = "REVIEW_REQUIRED" if reviews else "READY"
    total_cuts = sum(values["cuts"] for values in metrics.values())
    total_seconds = sum(values["total"] for values in metrics.values())
    lines = [
        "# 편집 품질 일관성 감사",
        "",
        "## 상태",
        "",
        f"- 결과: `{status}`",
        f"- 기준 컷리스트: `{cutlist.as_posix()}`",
        f"- 품질 프로필: `{profile_path.as_posix()}`",
        f"- 컷: {total_cuts}개",
        f"- 선택 길이: {total_seconds:.2f}초",
        f"- 미해결 검토: {len(reviews)}건",
        f"- 근거 있는 예외: {sum(f.status == 'WAIVED' for f in findings)}건",
        "",
        "경고선은 목표 컷 길이가 아니라 재검토 기준이다.",
        "",
        "## 구간 지표",
        "",
        "| 구간 | 컷 | 선택 길이 | 평균 | 최장 | 최장 컷 |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for section, values in sorted(
        metrics.items(), key=lambda item: (item[0] != "HOOK", item[0])
    ):
        lines.append(
            f"| {section} | {values['cuts']} | {values['total']:.2f}초 | "
            f"{values['average']:.2f}초 | {values['maximum']:.2f}초 | {values['longest_id']} |"
        )

    lines.extend(
        [
            "",
            "## 발견 사항",
            "",
            "| 상태 | 구간 | 코드 | 내용 | 예외 근거 |",
            "|---|---|---|---|---|",
        ]
    )
    if findings:
        for finding in findings:
            lines.append(
                f"| {finding.status} | {finding.section} | {finding.code} | "
                f"{finding.detail} | {finding.justification or '-'} |"
            )
    else:
        lines.append("| CLEAR | - | - | 자동 경고 없음 | - |")

    lines.extend(
        [
            "",
            "## 다음 조치",
            "",
            "- `REVIEW`는 해당 비트의 microbeat 기록과 원본 경계를 다시 확인한다.",
            "- 긴 컷이 의도된 경우 화면·문장·사건 근거를 프로필에 기록하고 `WAIVED`로 남긴다.",
            "- 컷을 바꾸면 새 버전 보고서를 생성한다. 기존 보고서를 덮어쓰지 않는다.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("cutlist", type=Path)
    parser.add_argument("profile", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    cuts = load_cuts(args.cutlist)
    profiles = load_profiles(args.profile)
    metrics, findings = audit(cuts, profiles)
    report = render_report(args.cutlist, args.profile, metrics, findings)
    if args.output:
        if args.output.exists():
            raise FileExistsError(f"출력 파일이 이미 존재함(덮어쓰기 금지): {args.output}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8", newline="\n")
        print(f"[edit-quality] 완료: {args.output}")
    else:
        print(report)
    review_count = sum(finding.status == "REVIEW" for finding in findings)
    waived_count = sum(finding.status == "WAIVED" for finding in findings)
    print(
        f"[edit-quality] sections={len(metrics)} cuts={len(cuts)} "
        f"review={review_count} waived={waived_count}"
    )


if __name__ == "__main__":
    main()
