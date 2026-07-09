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
    "PROJECT_BOOTSTRAP.md",
    "PROJECT_RULES.md",
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    "SESSION_HANDOFF.md",
    "docs/INDEX.md",
    "docs/AGENT_MAINTENANCE.md",
    "README.md",
    "CURRENT_TASK.md",
    ".geminiignore",
]

ALWAYS_LOAD_DOCS = [
    "PROJECT_BOOTSTRAP.md",
    "docs/INDEX.md",
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
    ("문서_인덱스.md", "문서 라우터는 표준 경로 `docs/INDEX.md`를 사용한다."),
]

# 본문(.md)에서 참조하는 다른 .md 경로의 존재를 검사할 때 예외로 두는 대상.
REFERENCE_ALLOWLIST = {
    "Workspace/README.md",  # Tier-1 상위 저장소 포인터. 이 서브프로젝트 밖 문서다.
}
MD_REFERENCE_PATTERN = re.compile(r"`([^`]+?\.md)`|\]\(([^)]+?\.md)\)")

REQUIRED_PROJECT_RULES_PHRASES = [
    "# PROJECT_RULES.md — Full Rules (Conditional Source of Truth)",
    "This file is the full rule source for this project. It is not the default",
    "Every AI agent starts with `PROJECT_BOOTSTRAP.md`",
    "If the same objective fails 3 times in a row (fix → verify → fail), stop.",
    "the last confirmed cause, the risk of continuing, and what to re-research",
    "This outranks task persistence.",
    "## Local Additions — 김실버유튜브",
]

FORBIDDEN_PROJECT_RULES_PHRASES = [
    "must read and follow it first",
    "1. `PROJECT_RULES.md`\n2. `SESSION_HANDOFF.md`",
    "The rules above are copied from the repo-root",
    "must not be\nrewritten in this sub-project",
]

REQUIRED_BOOTSTRAP_PHRASES = [
    "Status: always-load kernel",
    "Full rule source: `PROJECT_RULES.md`",
    "Document router: `docs/INDEX.md`",
    "Full Rule Load Triggers",
    "If the same objective fails 3 times in a row, stop.",
    "This file is a loader, not a replacement for `PROJECT_RULES.md`.",
]

POINTER_FILES = {
    "AGENTS.md": [
        "Mandatory Bootstrap Load Gate",
        "read `PROJECT_BOOTSTRAP.md`",
        "first line to the last line",
        "`PROJECT_RULES.md` only when the bootstrap trigger conditions",
    ],
    "CLAUDE.md": [
        "Mandatory Bootstrap Load Gate",
        "@PROJECT_BOOTSTRAP.md",
        "first line to the last line",
        "mandatory bootstrap source",
    ],
    "GEMINI.md": [
        "Mandatory Bootstrap Load Gate",
        "@PROJECT_BOOTSTRAP.md",
        "first line to the last line",
        "mandatory bootstrap source",
    ],
}

POINTER_FORBIDDEN_PATTERNS = {
    "@PROJECT_RULES.md": "포인터 파일에는 전체 규칙 원본을 직접 import하지 않는다. PROJECT_BOOTSTRAP.md를 import한다.",
    "@SESSION_HANDOFF.md": "포인터 파일에는 상태 문서를 직접 import하거나 규칙처럼 넣지 않는다.",
    "@docs/INDEX.md": "포인터 파일에는 라우터를 직접 import하지 않는다. PROJECT_RULES.md가 읽기 경로를 가진다.",
    "Imported Claude Cowork": "포인터 파일에는 도메인 규칙이나 가져온 지침을 넣지 않는다.",
}

MAINTENANCE_REQUIRED_PHRASES = [
    "## 7. 구조적 문제",
    "## 8. 방법별 점수",
    "## 9. 조합 전략",
    "Mandatory Bootstrap Load Gate",
    "PROJECT_BOOTSTRAP.md",
    "기본 로드 2개",
    "Context Bloat",
    "28.64%",
    "20% 이상",
    "https://developers.openai.com/codex/guides/agents-md",
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
    if path == "docs/AGENT_MAINTENANCE.md":
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
    index = root / "docs" / "INDEX.md"
    if not index.exists():
        return
    content = read_text(index)
    for doc in ROOT_DOCS:
        if doc not in content:
            findings.append(Finding("ERROR", "docs/INDEX.md", None, f"`{doc}` 읽는 조건이 인덱스에 없다."))


def check_agent_entrypoints(root: Path, findings: list[Finding]) -> None:
    bootstrap = root / "PROJECT_BOOTSTRAP.md"
    if bootstrap.exists():
        content = read_text(bootstrap)
        for phrase in REQUIRED_BOOTSTRAP_PHRASES:
            if phrase not in content:
                findings.append(Finding("ERROR", "PROJECT_BOOTSTRAP.md", None, f"부트스트랩 필수 기준 누락: {phrase}"))

    rules = root / "PROJECT_RULES.md"
    if rules.exists():
        content = read_text(rules)
        for phrase in REQUIRED_PROJECT_RULES_PHRASES:
            if phrase not in content:
                findings.append(Finding("ERROR", "PROJECT_RULES.md", None, f"최상위 Stop Rule 원문 또는 로컬 추가 기준 누락: {phrase}"))
        for phrase in FORBIDDEN_PROJECT_RULES_PHRASES:
            if phrase in content:
                findings.append(Finding("ERROR", "PROJECT_RULES.md", None, f"조건부 로드 정책과 충돌하는 과거 문구: {phrase}"))

    for filename, required_phrases in POINTER_FILES.items():
        path = root / filename
        if not path.exists():
            continue
        content = read_text(path)
        for phrase in required_phrases:
            if phrase not in content:
                findings.append(Finding("ERROR", filename, None, f"포인터 파일에 `{phrase}` 연결이 없다."))
        for phrase, reason in POINTER_FORBIDDEN_PATTERNS.items():
            if phrase in content:
                findings.append(Finding("ERROR", filename, None, reason))

    gemini_ignore = root / ".geminiignore"
    if gemini_ignore.exists():
        content = read_text(gemini_ignore)
        for phrase in ["workspace/", "temp/", "tools/ffmpeg/", ".git/"]:
            if phrase not in content:
                findings.append(Finding("ERROR", ".geminiignore", None, f"Gemini 제외 목록에 `{phrase}`가 없다."))

    maintenance = root / "docs" / "AGENT_MAINTENANCE.md"
    if maintenance.exists():
        content = read_text(maintenance)
        for phrase in MAINTENANCE_REQUIRED_PHRASES:
            if phrase not in content:
                findings.append(Finding("ERROR", "docs/AGENT_MAINTENANCE.md", None, f"에이전트 유지관리 기준 누락: {phrase}"))


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


def check_reference_links(root: Path, findings: list[Finding]) -> None:
    """본문(.md)에서 참조한 다른 .md 문서가 실제로 존재하는지 검사한다.

    glob 패턴(`skills/*/SKILL.md`), `@import` 경로, 런타임 `workspace/` 경로,
    상위 티어 포인터는 정상 참조로 보고 건너뛴다.
    """
    for path in root.rglob("*.md"):
        if is_skipped(path, root):
            continue
        relative = rel(path, root)
        for index, line in enumerate(read_text(path).splitlines(), 1):
            for group_a, group_b in MD_REFERENCE_PATTERN.findall(line):
                raw = (group_a or group_b).strip()
                if raw.startswith(("http://", "https://")):
                    continue
                ref = raw.lstrip("@")
                if ref.startswith("./"):
                    ref = ref[2:]
                if not ref or ref.startswith("#"):
                    continue
                if "*" in ref or "?" in ref:
                    continue
                if ref.startswith("workspace/"):
                    continue
                if ref in REFERENCE_ALLOWLIST:
                    continue
                if not (root / ref).exists():
                    findings.append(
                        Finding(
                            "ERROR",
                            relative,
                            index,
                            f"참조한 문서 `{ref}`가 존재하지 않는다. 링크를 고치거나 문서를 만든다.",
                        )
                    )


def run(root: Path) -> int:
    findings: list[Finding] = []
    check_required_docs(root, findings)
    check_stale_text(root, findings)
    check_always_load_size(root, findings)
    check_index_links(root, findings)
    check_reference_links(root, findings)
    check_agent_entrypoints(root, findings)
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
