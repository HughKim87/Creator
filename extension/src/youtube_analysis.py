"""Read-only Korean YouTube analysis helpers. No downloads or account writes."""
from __future__ import annotations

import csv
import math
import re
import unicodedata
from pathlib import Path


def number(value):
    result = float(str(value).strip().replace(',', ''))
    if not math.isfinite(result):
        raise ValueError('유한한 숫자가 필요합니다.')
    return result


def timestamp(value):
    parts = str(value).strip().replace(',', '.').split(':')
    if len(parts) == 1:
        return number(parts[0])
    if len(parts) not in (2, 3):
        raise ValueError('시간은 초 또는 MM:SS / HH:MM:SS 형식이어야 합니다.')
    values = [number(p) for p in parts]
    if any(v < 0 for v in values) or any(v >= 60 for v in values[1:]):
        raise ValueError('잘못된 시간 좌표입니다.')
    return sum(v * 60 ** i for i, v in enumerate(reversed(values)))


def read_srt(path):
    text = Path(path).read_text(encoding='utf-8-sig').replace('\r\n', '\n').strip()
    cues = []
    for block in re.split(r'\n\s*\n', text):
        lines = block.splitlines()
        if lines and lines[0].strip().isdigit():
            lines = lines[1:]
        if len(lines) < 2 or '-->' not in lines[0]:
            raise ValueError('잘못된 SRT 블록입니다.')
        bounds = lines[0].split('-->')
        if len(bounds) != 2:
            raise ValueError('잘못된 SRT 시간입니다.')
        start, end = [timestamp(v.strip()) for v in bounds]
        if start < 0 or end <= start or (cues and start < cues[-1]['end'] - .001):
            raise ValueError('SRT 시간 역전 또는 겹침이 있습니다.')
        cues.append({'start': start, 'end': end, 'text': ' '.join(lines[1:]).strip()})
    if not cues:
        raise ValueError('자막이 비어 있습니다.')
    return cues


def read_retention(path, *, position_column, retention_column, axis, unit, duration):
    if axis not in ('seconds', 'percent', 'ratio') or unit not in ('percent', 'ratio'):
        raise ValueError('축과 유지율 단위를 명시하세요.')
    duration = number(duration)
    if duration <= 0 or position_column == retention_column:
        raise ValueError('영상 길이와 서로 다른 열 이름이 필요합니다.')
    points = []
    with Path(path).open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not {position_column, retention_column} <= set(reader.fieldnames):
            raise ValueError('지정한 CSV 열을 찾을 수 없습니다.')
        for index, row in enumerate(reader, 2):
            if not any(v for v in row.values()):
                continue
            try:
                raw_x, raw_y = row[position_column].strip(), row[retention_column].strip()
                if (raw_x.endswith('%') and axis != 'percent') or (raw_y.endswith('%') and unit != 'percent'):
                    raise ValueError('퍼센트 기호와 지정 단위가 다릅니다.')
                x = timestamp(raw_x) if axis == 'seconds' else number(raw_x.removesuffix('%'))
                y = number(raw_y.removesuffix('%')) * (100 if unit == 'ratio' else 1)
                if axis == 'percent':
                    x = x / 100 * duration
                elif axis == 'ratio':
                    x *= duration
                if x < 0 or x > duration or y < 0 or (points and x <= points[-1][0]):
                    raise ValueError('좌표 범위, 순서 또는 유지율이 잘못됐습니다.')
                points.append((x, y))
            except (ValueError, AttributeError, TypeError) as e:
                raise ValueError(f'CSV {index}행: {e}') from e
    if len(points) < 2:
        raise ValueError('유효한 데이터가 2개 이상 필요합니다.')
    return points


def retention_report(points, duration, cues=(), top=5):
    duration = number(duration)
    if duration <= 0 or top < 1:
        raise ValueError('양수 길이와 후보 수가 필요합니다.')
    if cues and cues[-1]['end'] > duration + .001:
        raise ValueError('SRT가 영상 길이를 넘습니다. 최종 영상 좌표인지 확인하세요.')
    # Boundary points are interpolated only inside observed coverage, never extrapolated.
    def value_at(t):
        for (x0, y0), (x1, y1) in zip(points, points[1:]):
            if x0 <= t <= x1:
                return y0 + (y1 - y0) * (t - x0) / (x1 - x0)
        return None
    opening_end = min(30, duration)
    first, last = value_at(0), value_at(opening_end)
    intervals = []
    for (start, before), (end, after) in zip(points, points[1:]):
        drop = before - after
        if drop > 0:
            intervals.append({'start': start, 'end': end, 'drop_pp': round(drop, 4),
                              'drop_pp_per_second': round(drop / (end - start), 4),
                              'transcript': [dict(c) for c in cues if c['start'] < end and c['end'] > start]})
    intervals.sort(key=lambda r: (-r['drop_pp_per_second'], -r['drop_pp']))
    middle = [(max(a, opening_end), b, (ya - yb) / (b - a))
              for (a, ya), (b, yb) in zip(points, points[1:]) if b > opening_end]
    span = sum(b - a for a, b, _ in middle)
    return {'coverage_seconds': [points[0][0], points[-1][0]],
            'opening_end_seconds': opening_end,
            'opening_drop_pp': round(first - last, 4) if first is not None and last is not None else None,
            'drop_candidates': intervals[:top],
            'middle_net_drop_pp_per_second': round(sum((b - a) * r for a, b, r in middle) / span, 6) if span else None,
            'limitations': ['급락 후보는 관측 구간이며 이탈 원인·정확한 사건 시점이 아닙니다.',
                            '유지율은 재시청으로 100%를 넘을 수 있습니다. 발화·영상·유입 경로를 함께 검토하세요.']}


def tokens(text):
    return re.findall(r'[가-힣ㄱ-ㅎㅏ-ㅣa-z0-9]+', unicodedata.normalize('NFKC', text).casefold())


def lint_pair(title, thumbnail):
    title = unicodedata.normalize('NFKC', title).strip()
    thumbnail = unicodedata.normalize('NFKC', thumbnail).strip()
    common = sorted(set(tokens(title)) & set(tokens(thumbnail)))
    warnings = []
    if common:
        warnings.append('중복 어절을 검토하세요. 제품명 공유는 가능하며 질문·역할의 중복인지 사람이 판단합니다.')
    if len(title) > 40:
        warnings.append('앞부분만으로 대상과 질문이 전달되는지 실제 모바일 미리보기에서 확인하세요. 40자는 표시 보장이 아닙니다.')
    if len(thumbnail.replace(' ', '').replace('\n', '')) > 18:
        warnings.append('썸네일 문구의 읽기 부담을 모바일 이미지에서 확인하세요. 길이는 참고치입니다.')
    errors = []
    if not title or len(title) > 100:
        errors.append('제목이 비었거나 100자를 넘습니다.')
    if '\n' in title or '\r' in title:
        errors.append('제목은 한 줄이어야 합니다.')
    return {'title': title, 'thumbnail': thumbnail, 'title_chars': len(title),
            'title_front': title[:40], 'shared_tokens': common,
            'errors': errors,
            'warnings': warnings, 'semantic_review': 'not_run', 'performance_status': 'not_measured'}


def validate_chapters(chapters, duration):
    duration = number(duration)
    errors = []
    if duration <= 0 or not isinstance(chapters, list):
        raise ValueError('양수 영상 길이와 챕터 목록이 필요합니다.')
    parsed = []
    for row in chapters:
        if not isinstance(row, dict) or not isinstance(row.get('title'), str) or not row['title'].strip() or '\n' in row['title'] or '\r' in row['title']:
            raise ValueError('각 챕터에는 한 줄 제목이 필요합니다.')
        start = timestamp(row['start'])
        if start < 0 or start != int(start):
            raise ValueError('챕터 시작은 0 이상 정수 초여야 합니다.')
        parsed.append({'start': int(start), 'title': row['title'].strip()})
    if len(parsed) < 3:
        errors.append('챕터는 최소 3개가 필요합니다.')
    if parsed and parsed[0]['start'] != 0:
        errors.append('첫 챕터는 00:00이어야 합니다.')
    for i, row in enumerate(parsed):
        end = parsed[i + 1]['start'] if i + 1 < len(parsed) else duration
        if end - row['start'] < 10:
            errors.append(f'{i + 1}번 챕터: 순서 또는 최소 10초 길이를 확인하세요.')
        if row['start'] >= duration:
            errors.append(f'{i + 1}번 챕터가 영상 범위를 벗어납니다.')
    def label(t):
        return f'{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}' if t >= 3600 else f'{t // 60:02d}:{t % 60:02d}'
    return {'valid': not errors, 'errors': errors, 'chapters': parsed,
            'block': '\n'.join(f"{label(r['start'])} {r['title']}" for r in parsed) if not errors else None,
            'platform_rendering': 'not_verified'}


def chapter_candidates(cues, duration, target=7):
    duration = number(duration)
    if target < 3 or duration <= 0 or not cues or cues[-1]['end'] > duration + .001:
        raise ValueError('후보 수는 3 이상, SRT는 최종 영상 범위 안이어야 합니다.')
    scored = []
    for i in range(1, len(cues)):
        before = set(tokens(' '.join(c['text'] for c in cues[max(0, i-4):i])))
        after = set(tokens(' '.join(c['text'] for c in cues[i:i+4])))
        shift = 1 - len(before & after) / len(before | after) if before | after else 0
        gap = max(0, cues[i]['start'] - cues[i-1]['end'])
        scored.append((gap + shift * 2, int(cues[i]['start'])))
    picked = [0]
    for _, start in sorted(scored, reverse=True):
        if len(picked) >= target:
            break
        if duration - start >= 10 and all(abs(start - p) >= 10 for p in picked):
            picked.append(start)
    picked.sort()
    return {'draft': True, 'candidates': [
        {'start': start, 'evidence': [c['text'] for c in cues if c['start'] >= start and c['start'] < (picked[i+1] if i+1 < len(picked) else duration)][:4]}
        for i, start in enumerate(picked)],
        'next_action': '실제 구간을 확인하고 한국어 제목을 작성한 뒤 validate를 실행하세요.'}
