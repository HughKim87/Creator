"""Check an explicitly reviewed video skill bundle; never repairs production files."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
SKILLS = ('connect-chrome-profile','coordinate-video-production','notebooklm-research-topic','notebooklm-generate-video','video-to-srt','youtube-title-thumbnail','prepare-youtube-upload')
MANIFEST = '.agents/skills/coordinate-video-production/references/skill-bundle.json'
def digest(p):
    raw=p.read_bytes()
    # Git normalizes text line endings; a Windows checkout must match its commit.
    if p.suffix.lower() in ('.md','.py','.mjs','.json','.yaml','.yml','.txt'):
        raw=raw.decode('utf-8-sig').replace('\r\n','\n').encode('utf-8')
    return hashlib.sha256(raw).hexdigest()
def inspect(root, manifest=None):
    root=Path(root).resolve(); manifest=manifest or root/MANIFEST
    errors=[]
    try:
        data=json.loads(Path(manifest).read_text(encoding='utf-8'))
        files=data['files']
        if data.get('schema_version')!='video-skill-bundle-v1' or not isinstance(files,dict) or not files: raise ValueError('invalid bundle manifest')
        for rel, expected in files.items():
            p=(root/rel).resolve()
            if not p.is_relative_to(root/'.agents/skills') or '..' in Path(rel).parts: raise ValueError('unsafe bundle member')
            if not p.is_file():errors.append('missing: '+rel)
            elif digest(p)!=expected:errors.append('changed: '+rel)
    except (OSError,KeyError,ValueError,TypeError) as e: errors.append(str(e))
    return {'status':'valid' if not errors else 'invalid','root':str(root),'errors':errors}
def record(root):
    root=Path(root).resolve();files={}
    for name in SKILLS:
        for p in sorted((root/'.agents/skills'/name).rglob('*')):
            rel=p.relative_to(root).as_posix()
            if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc' and rel!=MANIFEST:
                files[rel]=digest(p)
    if not all(f'.agents/skills/{s}/SKILL.md' in files for s in SKILLS):raise ValueError('incomplete skill set')
    (root/MANIFEST).write_text(json.dumps({'schema_version':'video-skill-bundle-v1','files':files},indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=Path.cwd());parser.add_argument('--record-reviewed',action='store_true',help='Maintenance only: record a reviewed bundle, never use to bypass a production mismatch')
    args=parser.parse_args()
    if args.record_reviewed:record(args.root)
    result=inspect(args.root);print(json.dumps(result,ensure_ascii=False,indent=2));raise SystemExit(0 if result['status']=='valid' else 1)
