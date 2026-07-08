#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Project documentation consistency checker.

This checker is intentionally small and dependency-free. It catches the
documentation drift patterns that have caused trouble in this project:
stale status text, old session paths, missing skill gates, and bloated
always-loaded documents.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


TEXT_SUFFIXES = {".md", ".py", ".bat", ".txt"}
SKIP_DIRS = {
    ".git",
    ".agents",
    ".codex",
    "workspace",
    "temp",
    "inputs",
    "__pycache__",
}
SKIP_PREFIXES = {
    "tools/ffmpeg/",
}

ROOT_DOCS = [
    "PROJECT_RULES.md",
    "SESSION_HANDOFF.md",
    "문서_인덱스.md",
    "README.md",
    "CURRENT_TASK.md",
]

ALWAYS_LOAD_DOCS = [
    "PROJECT_RULES.md",
    "SESSION_HANDOFF.md",
    "문서_인덱스.md",
]

STALE_PATTERNS = [
    ("최근 커밋", "Git으로 확인할 동적 상태를 문서에 고정하지 않는다."),
    ("커밋 필요", "커밋 대기 상태가 남아 있는지 확인한다."),
    ("커밋 여부", "커밋 완료 후 남은 대기 문구인지 확인한다."),
    ("보강 필요", "완료된 작업이 아직 필요 상태로 남았는지 확인한다."),
    ("정리 필요", "완료된 작업이 아직 필요 상태로 남았는지 확인한다."),
    ("복구되어 있다", "삭제/폐기 처리된 자료가 살아있는 것처럼 적혔는지 확인한다."),
    ("현재는 보존", "삭제 또는 폐기 처리 이후 남은 과거 상태 문구인지 확인한다."),
    ("보강 중", "완료된 작업이 진행 중처럼 남았는지 확인한다."),
]

OLD_PATH_PATTERNS = [
    ("/sessions/", "과거 샌드박스 절대경로를 제거한다."),
    ("workspace/inputs/2026-06-30", "과거 백룸 원본 파일명을 제거한다."),
]

SKILL_REQUIRED_PATTERNS = {
    "입력": re.compile(r"입력"),
    "출력": re.compile(r"출력|산출물"),
    "게이트": re.compile(r"게이트|통과"),
    "중단 조건": re.compile(r"중단 조건|멈출 조건"),
    "AI 확정 금지": re.compile(r"AI가 확정하지 말 것"),
    "요청 예시": re.compile(r"좋은 요청 예시"),
}


@dataclass
class Finding:
    level: str
    path: str
    line: int | None
    message: str

    def render(self) -> str:
        loc = self.path if self.line is None else f"{self.path}:{self.line}"
        return f"[{self.level}] {loc} - {self.message}"


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def is_skipped(path: Path, root: Path) -> bool:
    relative = rel(path, root)
    if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
        return True
    return any(relative.startswith(prefix) for prefix in SKIP_PREFIXES)


def text_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if is_skipped(path, root):
            continue
        if path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")


def allowed_pattern_definition(path: str, line: str) -> bool:
    if path == "tools/doccheck/check_docs.py":
        return True
    if path == "PROJECT_RULES.md" and "rg -n" in line:
        return True
    return False


def check_required_docs(root: Path, findings: list[Finding]) -> None:
    for doc in ROOT_DOCS:
        if not (root / doc).exists():
            findings.append(Finding("ERROR", doc, None, "필수 문서가 없다."))


def check_stale_text(root: Path, findings: list[Finding]) -> None:
    for path in text_files(root):
        relative = rel(path, root)
        for index, line in enumerate(read_text(path).splitlines(), 1):
            if allowed_pattern_definition(relative, line):
                continue
            for phrase, reason in STALE_PATTERNS:
                if phrase in line:
                    findings.append(Finding("ERROR", relative, index, f"낡은 상태 문구 `{phrase}` 발견. {reason}"))
            for phrase, reason in OLD_PATH_PATTERNS:
                if phrase in line:
                    findings.append(Finding("ERROR", relative, index, f"과거 경로 `{phrase}` 발견. {reason}"))
            if re.search(r"(커밋|commit).*[0-9a-f]{7,40}", line, re.IGNORECASE):
                findings.append(Finding("ERROR", relative, index, "커밋 SHA로 보이는 동적 상태가 문서에 고정되어 있다."))


def check_always_load_size(root: Path, findings: list[Finding]) -> None:
    for doc in ALWAYS_LOAD_DOCS:
        path = root / doc
        if not path.exists():
            continue
        lines = read_text(path).splitlines()
        if len(lines) > 220:
            findings.append(Finding("WARN", doc, None, f"기본 로드 문서가 {len(lines)}줄이다. 분리 검토가 필요하다."))


def check_index_links(root: Path, findings: list[Finding]) -> None:
    index = root / "문서_인덱스.md"
    if not index.exists():
        return
    content = read_text(index)
    for doc in ROOT_DOCS:
        if doc not in content:
            findings.append(Finding("ERROR", "문서_인덱스.md", None, f"`{doc}` 읽는 조건이 인덱스에 없다."))


def check_skills(root: Path, findings: list[Finding]) -> None:
    skills_dir = root / "skills"
    if not skills_dir.exists():
        findings.append(Finding("ERROR", "skills", None, "skills 폴더가 없다."))
        return

    for skill_dir in sorted(path for path in skills_dir.iterdir() if path.is_dir()):
        skill_file = skill_dir / "SKILL.md"
        relative = rel(skill_file, root)
        if not skill_file.exists():
            findings.append(Finding("ERROR", rel(skill_dir, root), None, "SKILL.md가 없다."))
            continue

        content = read_text(skill_file)
        if not content.startswith("---"):
            findings.append(Finding("ERROR", relative, 1, "YAML frontmatter가 없다."))
        for label, pattern in SKILL_REQUIRED_PATTERNS.items():
            if not pattern.search(content):
                findings.append(Finding("ERROR", relative, None, f"필수 섹션 또는 표현 누락: {label}"))


def run(root: Path) -> int:
    findings: list[Finding] = []
    check_required_docs(root, findings)
    check_stale_text(root, findings)
    check_always_load_size(root, findings)
    check_index_links(root, findings)
    check_skills(root, findings)

    errors = [item for item in findings if item.level == "ERROR"]
    warnings = [item for item in findings if item.level == "WARN"]

    if findings:
        print("doccheck findings")
        for item in findings:
            print(item.render())
    else:
        print("doccheck OK")

    print(f"summary: errors={len(errors)} warnings={len(warnings)}")
    return 1 if errors else 0


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    if len(sys.argv) > 1:
        root = Path(sys.argv[1]).resolve()
    return run(root)


if __name__ == "__main__":
    raise SystemExit(main())
