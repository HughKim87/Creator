"""Analyze explicitly mapped retention CSV and optional final-video SRT."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'extension/src'))
from youtube_analysis import read_retention, read_srt, retention_report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('csv', type=Path)
    p.add_argument('--position-column', required=True)
    p.add_argument('--retention-column', required=True)
    p.add_argument('--axis', choices=['seconds', 'percent', 'ratio'], required=True)
    p.add_argument('--unit', choices=['percent', 'ratio'], required=True)
    p.add_argument('--duration', type=float, required=True)
    p.add_argument('--srt', type=Path)
    p.add_argument('--top', type=int, default=5)
    a = p.parse_args()
    try:
        points = read_retention(a.csv, position_column=a.position_column, retention_column=a.retention_column,
                                axis=a.axis, unit=a.unit, duration=a.duration)
        result = retention_report(points, a.duration, read_srt(a.srt) if a.srt else (), a.top)
        result['units'] = {'input_axis': a.axis, 'input_retention': a.unit, 'output_axis': 'seconds', 'drop': 'percentage_points'}
    except (ValueError, OSError) as e:
        p.error(str(e))
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
