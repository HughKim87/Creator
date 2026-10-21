"""Reproduce the reviewed branch absorption scope without modifying any refs.

Compares net changes since the common ancestor, not historical patches that may
already be superseded. Protected data and Core are excluded before enumeration.
"""
import argparse
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
TAGS = ('before-codex-wardogs', 'before-codex-24HReplier', 'before-codex-ainotebook',
        'before-claude-dokkaebi', 'before-codex-TRYALLGAME', 'before-codex-backroom-video')
EXCLUDES = [':!core', ':(exclude,glob)**/inputs/**', ':(exclude,glob)**/outputs/**']
DOKKAEBI = {
    'extension/rules/video-editing-boundary-quality.md',
    'extension/rules/video-editing-intake-and-instructions.md',
    'extension/rules/video-editing-story-and-cut-design.md',
    'extension/rules/video-post-production.md',
    'extension/docs/domain/youtube/PREMIERE_CS6_XML_COMPAT.md',
    'extension/docs/domain/youtube/VIDEO_EDITING_PROFILES.md',
    'extension/docs/domain/youtube/VIDEO_EDITING_RULE_CANDIDATES.md',
    'extension/docs/domain/youtube/VIDEO_EDITING_WORKFLOW_CONTRACT.md',
    'extension/tests/test_extension_rule_routing.py',
    'extension/tests/test_video_editing_workflow.py',
}
REPLIER_SCRIPTS = {'scripts/Build-24HReplier.ps1', 'scripts/Start-24HReplier.cmd',
                   'scripts/Install-24HReplierLLM.ps1', 'extension/config/replier-llm-local.json'}


def git(*args):
    return subprocess.check_output(['git', '--no-optional-locks', '-c', 'core.quotepath=false', '-C', str(ROOT), *args], text=True, encoding='utf-8').strip()


def classify(tag, path):
    if tag == 'before-codex-24HReplier' and path in {
        '7ea3474f7ada43ff91ab3634b78bb7e8/content/V0000000001.json', 'comment-display-preview.png'}:
        return 'generated-fixture-preserved', 'Synthetic V0000000001 cache / UI preview; implementation and fixture generators are absorbed. Historical bytes remain in the source tag and recovery bundle.'
    if path.startswith(('state/', 'extension/work/')) or path == 'SESSION_HANDOFF.md':
        return 'task-record-preserved', 'Historical task data remains in its original worktree and recovery bundle; not a reusable implementation.'
    if tag == 'before-codex-24HReplier' and (path.startswith(('extension/src/replier/', 'extension/tests/replier_'))
            or path == 'extension/tests/test_replier.py' or path in REPLIER_SCRIPTS):
        return 'absorbed', 'Replier implementation/checks inherited in 5b5c6c9; runtime paths adapted for shared main workspace.'
    if tag == 'before-claude-dokkaebi' and path in DOKKAEBI:
        return 'absorbed-or-superseded', 'Main preserves viewer analysis and TC34..TC40; remaining compatibility evidence/style choices inherited in 5b5c6c9. See maintained consolidation report.'
    if tag == 'before-codex-TRYALLGAME' and path == '.gitignore':
        return 'superseded', 'Single task ignore replaced with /extension/jobs/ for all future jobs.'
    if tag == 'before-codex-backroom-video' and path == 'PROJECT_RULES.md':
        return 'superseded', 'The preservation rule is retained; per-worktree production replaced with job-scoped ownership.'
    if tag == 'before-codex-backroom-video' and (path.startswith('extension/docs/domain/youtube/BACKROOM_')
            or path == 'extension/reports/2026-08-26_BACKROOM_EDITING_RESUME_PLAN.md'):
        return 'task-record-preserved', 'Historical editorial plans remain recoverable, not shared workflow definitions.'
    return 'unreviewed', 'Requires explicit content review before any branch/worktree removal.'


def audit():
    result = []
    for tag in TAGS:
        base = git('merge-base', 'before', tag)
        paths = git('diff', '--name-only', base, tag, '--', '.', *EXCLUDES).splitlines()
        for path in paths:
            status, reason = classify(tag, path)
            # An absorption claim needs a real file on main, not only a table row.
            if status in {'absorbed', 'absorbed-or-superseded'} and not (ROOT / path).is_file():
                status, reason = 'unreviewed', 'Expected main owner is missing.'
            result.append({'source': tag, 'path': path, 'decision': status, 'reason': reason})
    return {'schema_version': 'creator-absorption-audit-v1', 'main_commit': git('rev-parse', 'HEAD'),
            'unreviewed': [x for x in result if x['decision'] == 'unreviewed'], 'items': result,
            'limits': 'Reviewed net tracked changes only; semantic evidence is the report and tests. Ignored task scripts/data require migration review before worktree deletion.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    report = audit()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'reviewed_items': len(report['items']), 'unreviewed': report['unreviewed']}, ensure_ascii=False, indent=2))
    return bool(report['unreviewed'])


if __name__ == '__main__':
    raise SystemExit(main())
