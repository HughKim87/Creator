"""Compare observed videos only within explicit, comparable cohorts (no network)."""
import argparse
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path


def compare(rows, min_samples=4):
    if not isinstance(rows, list) or min_samples < 4:
        raise ValueError('videos는 목록, min_samples는 4 이상이어야 합니다.')
    groups = defaultdict(list)
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('각 영상은 객체여야 합니다.')
        for key in ('url', 'title', 'channel', 'format', 'cohort', 'checked_at'):
            if not isinstance(row.get(key), str) or not row[key].strip():
                raise ValueError(f'{key}: 비어 있지 않은 문자열이 필요합니다.')
        if row['url'] in seen:
            raise ValueError('같은 영상 URL이 중복됐습니다.')
        seen.add(row['url'])
        views = row.get('views')
        if isinstance(views, bool) or not isinstance(views, (int, float)) or not math.isfinite(views) or views < 0:
            raise ValueError('views: 확인한 유한한 0 이상 숫자가 필요합니다.')
        groups[(row['channel'], row['format'], row['cohort'])].append(row)
    results, skipped = [], []
    for (channel, form, cohort), videos in groups.items():
        median = statistics.median(v['views'] for v in videos)
        if len(videos) < min_samples or median <= 0:
            skipped.append(dict(channel=channel, format=form, cohort=cohort, samples=len(videos),
                                reason='표본 부족' if len(videos) < min_samples else '중앙값 0'))
            continue
        for video in videos:
            results.append(dict(video, median=median, samples=len(videos),
                                multiple=round(video['views'] / median, 4)))
    return {'videos': sorted(results, key=lambda r: -r['multiple']), 'skipped': skipped,
            'interpretation': '관측 표본 내 비교입니다. 예상 조회수나 소재의 인과 효과가 아닙니다.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('input', type=Path)
    p.add_argument('--min-samples', type=int, default=4)
    a = p.parse_args()
    try:
        result = compare(json.loads(a.input.read_text(encoding='utf-8-sig')), a.min_samples)
    except (ValueError, OSError) as e:
        p.error(str(e))
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
