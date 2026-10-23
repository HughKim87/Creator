"""Suggest SRT chapter boundaries or validate human-reviewed Korean headings."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'extension/src'))
from youtube_analysis import chapter_candidates, read_srt, validate_chapters


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['suggest', 'validate'])
    p.add_argument('input', type=Path)
    p.add_argument('--duration', required=True, type=float)
    p.add_argument('--target', type=int, default=7)
    a = p.parse_args()
    try:
        result = (chapter_candidates(read_srt(a.input), a.duration, a.target) if a.mode == 'suggest'
                  else validate_chapters(json.loads(a.input.read_text(encoding='utf-8-sig')), a.duration))
    except (ValueError, OSError, KeyError) as e:
        p.error(str(e))
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    raise SystemExit(1 if result.get('valid') is False else 0)


if __name__ == '__main__':
    main()
