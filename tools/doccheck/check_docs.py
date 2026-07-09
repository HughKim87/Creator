#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Small documentation consistency checker."""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


TEXT_SUFFIXES = {".md", ".py", ".bat", ".txt"}
SKIP_DIRS = {".git", ".agents", ".codex", "workspace", "temp", "inputs", "__pycache__"}
SKIP_PREFIXES = {"tools/ffmpeg/"}

REQUIRED_FILES = [
    "PROJECT_BOOTSTRAP.md",
    "PROJECT_RULES.md",
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    "SESSION_HANDOFF.md",
    "docs/INDEX.md",
    "docs/AGENT_MAINTENANCE.md",
    "skills/SKILL_CONTRACT.md",
    "README.md",
    "CURRENT_TASK.md",
    ".geminiignore",
]

SIZE_LIMITS = {
    "AGENTS.md": 12,
    "CLAUDE.md": 12,
    "GEMINI.md": 12,
    "PROJECT_BOOTSTRAP.md": 60,
    "docs/INDEX.md": 60,
    "PROJECT_RULES.md": 180,
    "docs/AGENT_MAINTENANCE.md": 60,
    "skills/SKILL_CONTRACT.md": 80,
    "SESSION_HANDOFF.md": 70,
    "CURRENT_TASK.md": 50,
}

STALE_PATTERNS = [
    ("문서_인덱스.md", "문서 라우터는 `docs/INDEX.md`다."),
    ("/sessions/", "과거 샌드박스 절대경로를 남기지 않는다."),
    ("workspace/inputs/2026-06-30", "과거 원본 파일명을 현재 기준으로 쓰지 않는다."),
    ("미커밋 변경", "작업트리 상태는 Git 명령으로 확인한다."),
    ("28.64%", "리서치 수치를 운영 검사 기준으로 고정하지 않는다."),
    ("\uae40\uc2e4\ubc84", "프레임워크 문서에는 작업별 고유명사를 고정하지 않는다."),
    ("\ubc31\ub8f8", "프레임워크 문서에는 원본별 고유명사를 고정하지 않는다."),
]

FORBIDDEN_ENTRYPOINTS = ["@PROJECT_RULES.md", "@SESSION_HANDOFF.md", "@docs/INDEX.md"]
MD_REF_RE = re.compile(r"`([^`]+?\.md)`|\]\(([^)]+?\.md)\)")
ALLOW_REFS = {"Workspace/README.md"}


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
    return any(part in SKIP_DIRS for part in path.relative_to(root).parts) or any(
        relative.startswith(prefix) for prefix in SKIP_PREFIXES
    )


def text_files(root: Path):
    for path in root.rglob("*"):
        if path.is_file() and not is_skipped(path, root) and path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")


def add(findings: list[Finding], level: str, path: str, line: int | None, message: str) -> None:
    findings.append(Finding(level, path, line, message))


def check_required(root: Path, findings: list[Finding]) -> None:
    for item in REQUIRED_FILES:
        if not (root / item).exists():
            add(findings, "ERROR", item, None, "필수 파일이 없다.")


def check_nul_and_stale(root: Path, findings: list[Finding]) -> None:
    for path in text_files(root):
        relative = rel(path, root)
        data = path.read_bytes()
        if b"\x00" in data:
            add(findings, "ERROR", relative, None, "NUL 바이트가 있다. 파일 손상 가능성.")
        for index, line in enumerate(read_text(path).splitlines(), 1):
            if relative == "tools/doccheck/check_docs.py":
                continue
            for phrase, reason in STALE_PATTERNS:
                if phrase in line:
                    add(findings, "ERROR", relative, index, f"`{phrase}` 발견. {reason}")
            if re.search(r"(커밋|commit).*[0-9a-f]{7,40}", line, re.IGNORECASE):
                add(findings, "ERROR", relative, index, "커밋 SHA로 보이는 동적 상태가 문서에 고정됨.")


def check_sizes(root: Path, findings: list[Finding]) -> None:
    for item, limit in SIZE_LIMITS.items():
        path = root / item
        if path.exists():
            lines = len(read_text(path).splitlines())
            if lines > limit:
                add(findings, "ERROR", item, None, f"{lines}줄이다. 목표 {limit}줄 이하.")


def check_entrypoints(root: Path, findings: list[Finding]) -> None:
    required = {
        "AGENTS.md": "PROJECT_BOOTSTRAP.md",
        "CLAUDE.md": "@PROJECT_BOOTSTRAP.md",
        "GEMINI.md": "@PROJECT_BOOTSTRAP.md",
    }
    for item, phrase in required.items():
        path = root / item
        if not path.exists():
            continue
        content = read_text(path)
        if phrase not in content:
            add(findings, "ERROR", item, None, f"`{phrase}` 연결이 없다.")
        for forbidden in FORBIDDEN_ENTRYPOINTS:
            if forbidden in content:
                add(findings, "ERROR", item, None, f"진입점에 `{forbidden}`를 직접 넣지 않는다.")


def check_refs(root: Path, findings: list[Finding]) -> None:
    for path in root.rglob("*.md"):
        if is_skipped(path, root):
            continue
        relative = rel(path, root)
        for index, line in enumerate(read_text(path).splitlines(), 1):
            for group_a, group_b in MD_REF_RE.findall(line):
                raw = (group_a or group_b).strip().lstrip("@")
                if raw.startswith(("http://", "https://", "#", "workspace/")):
                    continue
                if "*" in raw or "?" in raw or raw in ALLOW_REFS:
                    continue
                if not (root / raw).exists():
                    add(findings, "ERROR", relative, index, f"참조한 문서 `{raw}`가 없다.")


def check_gemini_ignore(root: Path, findings: list[Finding]) -> None:
    path = root / ".geminiignore"
    if not path.exists():
        return
    content = read_text(path)
    for phrase in [".git/", "workspace/", "temp/", "tools/ffmpeg/"]:
        if phrase not in content:
            add(findings, "ERROR", ".geminiignore", None, f"`{phrase}` 제외가 없다.")


def run(root: Path) -> int:
    findings: list[Finding] = []
    check_required(root, findings)
    check_nul_and_stale(root, findings)
    check_sizes(root, findings)
    check_entrypoints(root, findings)
    check_refs(root, findings)
    check_gemini_ignore(root, findings)

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
