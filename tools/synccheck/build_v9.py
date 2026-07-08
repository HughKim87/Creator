#!/usr/bin/env python3
"""Apply explicit boundary overrides to a cutlist.

This replaces the old project-specific script that modified one hard-coded
Backrooms cutlist. It does not infer creative choices; it only applies the
overrides passed on the command line and writes a new CSV.

Usage:
  python tools/synccheck/build_v9.py INPUT.csv OUTPUT.csv --start 3=00:01:02.5 --end 5=00:03:10
"""
import argparse
import csv
from pathlib import Path


def parse_time(value):
    parts = [float(p) for p in value.strip().split(":")]
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    raise ValueError(f"Bad time: {value}")


def format_time(seconds):
    seconds = round(max(seconds, 0), 1)
    h = int(seconds // 3600)
    m = int(seconds % 3600 // 60)
    s = seconds - h * 3600 - m * 60
    if abs(s - round(s)) < 1e-9:
        return f"{h:02d}:{m:02d}:{int(round(s)):02d}"
    return f"{h:02d}:{m:02d}:{s:04.1f}"


def parse_override(value):
    index, time_value = value.split("=", 1)
    return int(index), parse_time(time_value)


def pick_field(fieldnames, names):
    lowered = {name.lower(): name for name in fieldnames}
    for name in names:
        if name in fieldnames:
            return name
        if name.lower() in lowered:
            return lowered[name.lower()]
    raise KeyError(f"Missing column. Expected one of: {', '.join(names)}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--start", action="append", default=[], help="1-based row override, e.g. 3=00:01:02.5")
    parser.add_argument("--end", action="append", default=[], help="1-based row override, e.g. 5=00:03:10")
    args = parser.parse_args()

    if not args.input.exists():
        raise SystemExit(f"Input cutlist not found: {args.input}")
    if args.output.exists():
        raise SystemExit(f"Output already exists, refusing to overwrite: {args.output}")

    start_overrides = dict(parse_override(item) for item in args.start)
    end_overrides = dict(parse_override(item) for item in args.end)

    with args.input.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    start_field = pick_field(fieldnames, ["start", "시작"])
    end_field = pick_field(fieldnames, ["end", "끝"])

    changes = []
    for idx, row in enumerate(rows, 1):
        old_start = parse_time(row[start_field])
        old_end = parse_time(row[end_field])
        new_start = start_overrides.get(idx, old_start)
        new_end = end_overrides.get(idx, old_end)
        if not new_start < new_end:
            raise SystemExit(f"Invalid override at row {idx}: {new_start} >= {new_end}")
        if new_start != old_start or new_end != old_end:
            changes.append((idx, old_start, new_start, old_end, new_end))
        row[start_field] = format_time(new_start)
        row[end_field] = format_time(new_end)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote: {args.output}")
    print(f"Changed rows: {len(changes)}")
    for idx, old_start, new_start, old_end, new_end in changes:
        print(
            f"[{idx:02d}] start {format_time(old_start)} -> {format_time(new_start)} | "
            f"end {format_time(old_end)} -> {format_time(new_end)}"
        )


if __name__ == "__main__":
    main()
