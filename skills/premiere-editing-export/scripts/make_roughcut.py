#!/usr/bin/env python3
"""컷리스트로 러프컷 초안 mp4를 만든다.

원본은 절대 수정하지 않고, 컷 구간을 재인코딩해 이어붙인 새 파일을 만든다.
프리미어 정밀 편집 전에 흐름을 확인하는 '초안' 용도다.

사용법:
    python3 make_roughcut.py 원본.mkv 컷리스트.csv 출력.mp4 [--crf 20] [--preset veryfast]

컷리스트.csv 형식 (헤더 없이, # 주석 허용):
    시작,끝[,라벨]
    00:01:39,00:02:14,서비스종료 이야기
    21:00,22:30
시각은 SS / MM:SS / HH:MM:SS 모두 허용.
"""
import argparse
import csv
import subprocess
import sys
import tempfile
from pathlib import Path


def parse_ts(ts: str) -> float:
    parts = [float(p) for p in ts.strip().split(":")]
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    raise ValueError(f"시각 형식 오류: {ts}")


def read_cuts(path: Path):
    cuts = []
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.reader(f):
            if not row or row[0].strip().startswith("#"):
                continue
            start, end = parse_ts(row[0]), parse_ts(row[1])
            label = row[2].strip() if len(row) > 2 else ""
            if end <= start:
                raise ValueError(f"끝이 시작보다 빠름: {row}")
            cuts.append((start, end, label))
    if not cuts:
        raise ValueError("컷리스트가 비어 있음")
    return cuts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("cutlist")
    ap.add_argument("output")
    ap.add_argument("--crf", default="20")
    ap.add_argument("--preset", default="veryfast")
    args = ap.parse_args()

    src, out = Path(args.source), Path(args.output)
    if not src.exists():
        sys.exit(f"원본 없음: {src}")
    if out.exists():
        sys.exit(f"출력 파일이 이미 존재함(덮어쓰기 금지): {out}")
    out.parent.mkdir(parents=True, exist_ok=True)

    cuts = read_cuts(Path(args.cutlist))
    total = sum(e - s for s, e, _ in cuts)
    print(f"[roughcut] 컷 {len(cuts)}개, 합계 {total/60:.1f}분")

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        seg_paths = []
        for i, (s, e, label) in enumerate(cuts, 1):
            seg = tmpdir / f"seg_{i:03d}.mp4"
            print(f"[roughcut] {i}/{len(cuts)} {s:.1f}s → {e:.1f}s {label}")
            r = subprocess.run(
                ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                 "-ss", str(s), "-to", str(e), "-i", str(src),
                 "-c:v", "libx264", "-preset", args.preset, "-crf", args.crf,
                 "-c:a", "aac", "-b:a", "160k", str(seg)])
            if r.returncode != 0:
                sys.exit(f"구간 추출 실패: 컷 {i}")
            seg_paths.append(seg)

        concat_file = tmpdir / "concat.txt"
        concat_file.write_text(
            "".join(f"file '{p.as_posix()}'\n" for p in seg_paths), encoding="utf-8")
        r = subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error",
             "-f", "concat", "-safe", "0", "-i", str(concat_file),
             "-c", "copy", str(out)])
        if r.returncode != 0:
            sys.exit("이어붙이기 실패")

    print(f"[roughcut] 완료: {out}")


if __name__ == "__main__":
    main()
