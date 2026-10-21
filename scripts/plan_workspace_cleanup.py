"""Build a reviewable migration manifest; no move/delete mode exists.

Final candidates come from explicit reviewed task records, not mtime or a
largest-revision heuristic. XML references are recorded without opening sources.
"""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def create_plan(inventory):
    trees = inventory['worktrees']
    roots = {Path(t['root']).name: t['root'] for t in trees}
    main = str(ROOT)
    wardogs = next(t['root'] for t in trees if 'worktrees' in t['root'].lower() and 'wardogs' in t['root'].lower())
    notebook = roots['Creator-ainotebook']
    dokkaebi = roots['Creator-dokkaebi']
    selections = [
        {'job': 'wardogs', 'root': wardogs, 'prefixes': [
            'extension/outputs/wardogs/post-r27/wardogs-final-with-outro-r27.mp4',
            'extension/outputs/wardogs/post-r27/subtitles/wardogs-final-with-outro-r27.ko.srt',
            'extension/outputs/wardogs/post-r27/youtube-description.txt',
            'extension/work/wardogs-thumbnail-r2/thumbnail-master.png'],
         'reason': 'Latest rendered R27 and thumbnail R2 in source task record. Thumbnail metadata will be separated from the user-facing package.'},
        {'job': 'zeus-month-review', 'root': main, 'prefixes': ['extension/outputs/zeus-month-review-cs6-r9.xml'],
         'reason': 'Latest available XML candidate. Requires finality review and dependency retention before older versions are removed.'},
        {'job': 'dokkaebi-play-review', 'root': dokkaebi, 'prefixes': ['extension/outputs/dokkaebi-edit/dokkaebi-post-r6.xml', 'extension/outputs/dokkaebi-edit/dokkaebi-post-r6.srt'],
         'reason': 'Source state records post-r6 as accepted. XML dependencies are part of the final package.'},
        {'job': 'dokkaebi-voice-review', 'root': dokkaebi, 'prefixes': ['extension/outputs/dokkaebi-review/dokkaebi-user-edit.srt', 'extension/outputs/dokkaebi-review/dokkaebi-voice-cut-r6.xml'],
         'reason': 'User-edit SRT is a separate later editorial basis. Keep it alongside latest generated XML; do not claim they are a matched pair.'},
        {'job': 'dokkaebi-deck', 'root': dokkaebi, 'prefixes': ['extension/outputs/dokkaebi-deck/dokkaebi-deck-cut-r4.xml', 'extension/outputs/dokkaebi-deck/dokkaebi-deck-cut-r4.srt'],
         'reason': 'Latest cut and corrected caption file. Thumbnail alternatives are unselected in the recorded state, so none are automatically discarded.'},
        {'job': 'backroom-shorts', 'root': main, 'prefixes': ['extension/outputs/backroom-shorts-review-20261010/final-r6/'],
         'reason': 'Explicit final-r6 folder is a preservation candidate; unused preview renders require separate approval.'},
    ]
    for job in ('2026-10-17-nanobrowser', '2026-10-15-meta-muse-wonder', '2026-10-14-rea', '2026-10-14-gemini4-argon-news', '2026-10-14-context-mode'):
        selections.append({'job': job, 'root': notebook, 'prefixes': ['extension/outputs/' + job + '/'],
                           'reason': 'Existing four-file manual upload package; preserve all four files.'})
    by_root = {t['root']: t['files'] for t in trees}
    for selection in selections:
        available = by_root[selection['root']]
        selection['files'] = [f for f in available if any(
            f['path'].startswith(prefix) if prefix.endswith('/') else f['path'] == prefix
            for prefix in selection['prefixes'])]
        selection['xml_dependencies'] = []
        for f in selection['files']:
            if not f['path'].endswith('.xml'):
                continue
            source = Path(selection['root']) / f['path']
            raw = source.read_bytes()
            if b'<!ENTITY' in raw.upper():
                raise ValueError('XML entity definitions are not accepted')
            tree = ET.fromstring(raw)
            urls = sorted({el.text for el in tree.iter('pathurl') if el.text})
            selection['xml_dependencies'].append({'xml': f['path'], 'sha256': hashlib.sha256(raw).hexdigest(),
                'references': urls, 'reference_count': len(urls),
                'source_reads': 'not_run; do not remove referenced media/assets'})
        selection['target'] = 'extension/jobs/' + selection['job'] + '/outputs/'
        selection['status'] = 'preservation-candidate-not-moved'
    tool_prefixes = {
        main: ['extension/.runtime/' + name + '/' for name in ('ffmpeg', 'whisper.cpp', 'qwen-tts', 'gpt-sovits')],
        wardogs: ['extension/.runtime/qwen-asr/'],
        notebook: ['extension/.runtime/models/', 'extension/.runtime/python-deps/'],
        roots['Creator-24HReplier']: ['extension/.runtime/replier-llm/'],
    }
    retained = {(s['root'], f['path']) for s in selections for f in s['files']}
    required_references = set()
    for s in selections:
        for dependency in s['xml_dependencies']:
            for url in dependency['references']:
                parts = urlsplit(url)
                path = unquote(parts.path).lstrip('/')
                if parts.netloc and parts.netloc.lower() != 'localhost':
                    path = '//' + parts.netloc + '/' + path
                required_references.add(path.replace('\\', '/').casefold())
    candidates = []
    for t in trees:
        for f in t['files']:
            absolute = str(Path(t['root']) / f['path']).replace('\\', '/').casefold()
            if ((t['root'], f['path']) in retained or absolute in required_references
                    or any(f['path'].startswith(p) for p in tool_prefixes.get(t['root'], []))):
                continue
            candidates.append({'root': t['root'], **f,
                'decision': 'review-and-archive-before-removal',
                'approval': 'pending', 'reason': 'Not a selected final file or retained shared runtime. No regeneration or redundancy claim is made.'})
    return {'schema_version': 'creator-cleanup-plan-v1', 'mode': 'read-only',
            'inventory_checked_at': inventory['checked_at'], 'final_candidates': selections,
            'shared_runtime_preserve': tool_prefixes, 'remaining_review_files': candidates,
            'proposed_archive_root': 'D:/AI Agent/Creator-Archive/2026-10-21',
            'requirements': ['No deletion/move/worktree removal before explicit approval.',
                             'Source inputs and private credentials are not inventoried; preserve their owner and secure backup separately.',
                             'Recheck current sizes/mtime/hash and XML dependency closure immediately before migration.',
                             'Content backup and restored sample verification required before ignored files are removed.',
                             'Logical byte counts do not prove physical disk space savings (links/sparse data may share storage).']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--inventory', type=Path, default=ROOT / 'extension/data/consolidation/baseline.json')
    p.add_argument('--output', type=Path, default=ROOT / 'extension/data/consolidation/cleanup-plan.json')
    args = p.parse_args()
    plan = create_plan(json.loads(args.inventory.read_text(encoding='utf-8')))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'final_candidate_jobs': len(plan['final_candidates']),
                      'remaining_review_files': len(plan['remaining_review_files']),
                      'mode': plan['mode']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
