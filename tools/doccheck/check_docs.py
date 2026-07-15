#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Small documentation consistency checker."""
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


TEXT_SUFFIXES = {".md", ".py", ".bat", ".txt"}
SKIP_DIRS = {".git", ".agents", ".codex", "workspace", "temp", "inputs", "outputs", "__pycache__"}
SKIP_PREFIXES = {"tools/ffmpeg/"}
MEDIA_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".mp3", ".wav", ".m4a", ".mp4", ".mkv", ".mov", ".avi"}
ALLOWED_TOP_LEVEL_DIRS = {
    ".agents", ".claude", ".codex", ".git", ".githooks", ".github",
    ".pytest_cache", "docs", "inputs", "outputs", "planning_research",
    "skills", "tests", "tools",
}
ALLOWED_ROOT_FILES = {
    ".gitattributes", ".geminiignore", ".gitignore", "01_youtube_production_workflow.md",
    "AGENTS.md", "CLAUDE.md", "GEMINI.md", "PROJECT_BOOTSTRAP.md",
    "PROJECT_RULES.md", "README.md", "SESSION_HANDOFF.md",
}

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
    ".geminiignore",
]

SIZE_LIMITS = {
    "AGENTS.md": 12,
    "CLAUDE.md": 12,
    "GEMINI.md": 12,
    "PROJECT_BOOTSTRAP.md": 60,
    "docs/INDEX.md": 60,
    "PROJECT_RULES.md": 160,
    "docs/AGENT_MAINTENANCE.md": 60,
    "skills/SKILL_CONTRACT.md": 80,
    "SESSION_HANDOFF.md": 20,
}

STALE_PATTERNS = [
    ("문서_인덱스.md", "문서 라우터는 `docs/INDEX.md`다."),
    ("/sessions/", "과거 샌드박스 절대경로를 남기지 않는다."),
    ("workspace/inputs/2026-06-30", "과거 원본 파일명을 현재 기준으로 쓰지 않는다."),
    ("미커밋 변경", "작업트리 상태는 Git 명령으로 확인한다."),
    ("28.64%", "리서치 수치를 운영 검사 기준으로 고정하지 않는다."),
    ("\uae40\uc2e4\ubc84", "프레임워크 문서에는 작업별 고유명사를 고정하지 않는다."),
    ("\ubc31\ub8f8", "프레임워크 문서에는 원본별 고유명사를 고정하지 않는다."),
    ("file:///", "문서 참조에는 절대 file 링크를 쓰지 않는다."),
    ("C:\\Users\\Hugh\\.cache\\codex-runtimes", "특정 사용자 홈의 Python 실행 경로를 고정하지 않는다."),
]

FORBIDDEN_ENTRYPOINTS = ["@PROJECT_RULES.md", "@SESSION_HANDOFF.md", "@docs/INDEX.md"]
MD_REF_RE = re.compile(r"`([^`]+?\.md)`|\]\(([^)]+?\.md)\)")
ALLOW_REFS = {"Workspace/README.md", "outputs/SESSION_HANDOFF.md"}


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


def check_workspace_hygiene(root: Path, findings: list[Finding]) -> None:
    if (root / "temp").exists():
        add(findings, "ERROR", "temp", None, "프로젝트 임시 폴더를 사용하지 않는다.")

    forbidden_skill_phrases = (
        "--out-dir temp",
        "temp/video-watch",
        "temp\\video-watch",
        "workspace/outputs",
        "workspace\\outputs",
    )
    for path in (root / "skills").glob("*/SKILL.md"):
        content = read_text(path)
        for phrase in forbidden_skill_phrases:
            if phrase in content:
                add(findings, "ERROR", rel(path, root), None, f"금지된 임시 출력 경로 `{phrase}`가 있다.")

    backup_name = re.compile(r"(?i)(\.bak(?:[_\.-].*)?$|\.backup$|~$)")
    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if backup_name.search(path.name):
            add(findings, "ERROR", rel(path, root), None, "중복 백업 파일 이름을 사용하지 않는다.")


def check_folder_ownership(root: Path, findings: list[Finding]) -> None:
    for path in root.iterdir():
        if path.is_dir() and path.name not in ALLOWED_TOP_LEVEL_DIRS:
            add(findings, "ERROR", path.name, None, "분류되지 않은 루트 폴더다. 영상 작업 폴더는 outputs/ 아래에 둔다.")
        elif path.is_file() and path.name not in ALLOWED_ROOT_FILES:
            add(findings, "ERROR", path.name, None, "분류되지 않은 루트 파일이다. 입력 기반 파일은 outputs/ 아래에 둔다.")

    if (root / "NEXT_SESSION_TASK.md").exists():
        add(findings, "ERROR", "NEXT_SESSION_TASK.md", None, "루트에 영상별 작업 상태를 중복 저장하지 않는다.")

    handoff = root / "SESSION_HANDOFF.md"
    if handoff.exists():
        content = read_text(handoff)
        if "outputs/SESSION_HANDOFF.md" not in content:
            add(findings, "ERROR", "SESSION_HANDOFF.md", None, "루트 핸드오프는 outputs/SESSION_HANDOFF.md를 안내해야 한다.")
        for task_marker in ("source_id:", "## 현재 목표", "## 다음 작업"):
            if task_marker in content:
                add(findings, "ERROR", "SESSION_HANDOFF.md", None, f"영상별 상태 표식 `{task_marker}`는 outputs/에 둔다.")

    task_state = root / "outputs" / "SESSION_HANDOFF.md"
    if task_state.exists():
        match = re.search(r"source_id:\s*`?([A-Za-z0-9_.-]+)`?", read_text(task_state))
        if match:
            source_id = match.group(1)
            for path in text_files(root):
                if source_id in read_text(path):
                    add(findings, "ERROR", rel(path, root), None, f"현재 영상 식별자 `{source_id}`는 outputs/ 밖에 둘 수 없다.")

    for path in root.rglob("*.py"):
        relative = Path(rel(path, root))
        if not relative.parts or relative.parts[0] in {"inputs", "outputs"}:
            continue
        if relative.parts[0] not in {"tools", "skills", "tests"}:
            add(findings, "ERROR", relative.as_posix(), None, "outputs/ 밖의 Python은 공용 도구·스킬·프레임워크 테스트여야 한다.")


def find_new_python_files(root: Path, findings: list[Finding]) -> list[Path]:
    git = ["git", "-c", f"safe.directory={root.as_posix()}"]
    commands = [
        git + ["ls-files", "--others", "--exclude-standard", "--", "*.py"],
        git + ["diff", "--name-only", "--diff-filter=A", "HEAD", "--", "*.py"],
    ]
    paths: set[Path] = set()
    for command in commands:
        try:
            result = subprocess.run(
                command, cwd=root, capture_output=True, text=True, timeout=30,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            add(findings, "WARN", "Git", None, f"신규 Python 파일을 확인하지 못했다: {exc}")
            return []
        if result.returncode != 0:
            add(findings, "WARN", "Git", None, "신규 Python 파일을 확인하지 못했다.")
            return []
        paths.update(Path(line.strip()) for line in result.stdout.splitlines() if line.strip())
    return sorted(paths, key=lambda item: item.as_posix())


def check_python_lifecycle(
    root: Path,
    findings: list[Finding],
    new_files: list[Path] | None = None,
) -> None:
    candidates = find_new_python_files(root, findings) if new_files is None else new_files
    tools_doc = read_text(root / "tools" / "README.md") if (root / "tools" / "README.md").exists() else ""
    for relative in candidates:
        relative = Path(relative)
        path = root / relative
        parts = relative.parts
        if not parts or not path.exists():
            continue
        relative_text = relative.as_posix()

        if parts[0] == "tests":
            if path.name.startswith("test_"):
                continue
            add(findings, "ERROR", relative_text, None, "테스트 파일 이름은 `test_`로 시작해야 한다.")
            continue

        if parts[0] == "tools":
            if path.name not in tools_doc and relative_text not in tools_doc:
                add(findings, "ERROR", relative_text, None, "신규 Python 도구가 `tools/README.md`에 등록되지 않았다.")
            continue

        if len(parts) >= 4 and parts[0] == "skills" and parts[2] == "scripts":
            skill_doc = root / "skills" / parts[1] / "SKILL.md"
            content = read_text(skill_doc) if skill_doc.exists() else ""
            if path.name not in content and relative_text not in content:
                add(findings, "ERROR", relative_text, None, "신규 스킬 스크립트가 담당 `SKILL.md`에 등록되지 않았다.")
            continue

        if parts[0] == "outputs":
            if "support" not in parts[1:-1]:
                add(findings, "ERROR", relative_text, None, "작업 한정 Python은 `outputs/<stage>/support/` 아래에 둔다.")
                continue
            if path.name.startswith("test_") and "tests" in parts[1:-1]:
                continue
            header = "\n".join(read_text(path).splitlines()[:20]).lower()
            if "lifecycle: task-scoped" not in header or "cleanup:" not in header:
                add(findings, "ERROR", relative_text, None, "첫 20줄에 `Lifecycle: task-scoped`와 `Cleanup:` 조건을 기록한다.")
            else:
                add(findings, "WARN", relative_text, None, "작업 한정 Python이다. 종료 보고에서 유지·통합·승격·정리 판단을 밝힌다.")
            continue

        add(findings, "ERROR", relative_text, None, "신규 Python 파일의 역할이 불명확하다. `tools/`, 스킬 `scripts/`, `tests/`, 또는 단계 `support/`를 사용한다.")


def check_skill_asset_contract(root: Path, findings: list[Finding]) -> None:
    stage_skills = [
        "subtitle-cleanup",
        "dialogue-based-planning",
        "gameplay-video-analysis",
        "video-watch",
        "premiere-editing-export",
        "final-video-review",
    ]
    for name in stage_skills:
        path = root / "skills" / name / "SKILL.md"
        if not path.exists():
            continue
        content = read_text(path)
        if "source_id" not in content:
            add(findings, "ERROR", rel(path, root), None, "단계 간 안정된 source_id 인계가 없다.")

    for name in ("gameplay-video-analysis", "premiere-editing-export", "final-video-review"):
        path = root / "skills" / name / "SKILL.md"
        if not path.exists():
            continue
        content = read_text(path)
        for phrase in ("source_asset_manifest", "CURRENT.json"):
            if phrase not in content:
                add(findings, "ERROR", rel(path, root), None, f"자산 생명주기 필드 `{phrase}`가 없다.")

    watch = root / "skills" / "video-watch" / "SKILL.md"
    if watch.exists():
        for index, line in enumerate(read_text(watch).splitlines(), 1):
            if "python" in line and "--detail transcript" in line and "--out-dir" not in line:
                add(findings, "ERROR", rel(watch, root), index, "필수 --out-dir가 빠진 실행 예시다.")


def iter_json_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from iter_json_strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from iter_json_strings(item)


def check_media_registry(root: Path, findings: list[Finding]) -> None:
    outputs = root / "outputs"
    if not outputs.exists():
        return
    media = [path for path in outputs.rglob("*") if path.is_file() and path.suffix.lower() in MEDIA_SUFFIXES]
    if not media:
        return

    registered_files: set[Path] = set()
    registered_dirs: set[Path] = set()
    manifest = outputs / "06_analysis" / "source_asset_manifest.csv"
    if manifest.exists():
        try:
            with manifest.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            for row in rows:
                if row.get("status") != "current" or not row.get("path"):
                    continue
                path = (root / row["path"]).resolve()
                if not path.is_relative_to(root):
                    add(findings, "ERROR", rel(manifest, root), None, f"자산 경로가 프로젝트를 벗어난다: {row['path']}")
                elif path.is_dir():
                    registered_dirs.add(path)
                elif path.is_file():
                    registered_files.add(path)
                else:
                    add(findings, "ERROR", rel(manifest, root), None, f"현재 자산이 없다: {row['path']}")
        except (OSError, csv.Error) as exc:
            add(findings, "ERROR", rel(manifest, root), None, f"자산 목록을 읽지 못했다: {exc}")

    current_files = list(outputs.rglob("CURRENT.json"))
    for current in current_files:
        try:
            payload = json.loads(read_text(current))
        except (OSError, json.JSONDecodeError) as exc:
            add(findings, "ERROR", rel(current, root), None, f"현재본 포인터를 읽지 못했다: {exc}")
            continue
        for value in iter_json_strings(payload):
            if not value.startswith(("outputs/", "inputs/")):
                continue
            path = (root / value).resolve()
            if not path.is_relative_to(root):
                add(findings, "ERROR", rel(current, root), None, f"현재본 경로가 프로젝트를 벗어난다: {value}")
            elif path.is_dir():
                registered_dirs.add(path)
            elif path.is_file():
                registered_files.add(path)
            else:
                add(findings, "ERROR", rel(current, root), None, f"현재본 참조가 없다: {value}")

    for path in media:
        resolved = path.resolve()
        if resolved in registered_files or any(resolved.is_relative_to(directory) for directory in registered_dirs):
            continue
        add(findings, "ERROR", rel(path, root), None, "원본 자산 목록이나 CURRENT.json에 등록되지 않은 미디어다.")


def run(root: Path) -> int:
    findings: list[Finding] = []
    check_required(root, findings)
    check_nul_and_stale(root, findings)
    check_sizes(root, findings)
    check_entrypoints(root, findings)
    check_refs(root, findings)
    check_gemini_ignore(root, findings)
    check_workspace_hygiene(root, findings)
    check_folder_ownership(root, findings)
    check_python_lifecycle(root, findings)
    check_skill_asset_contract(root, findings)
    check_media_registry(root, findings)

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
