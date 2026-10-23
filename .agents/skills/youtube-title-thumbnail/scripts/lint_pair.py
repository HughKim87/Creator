"""Advisory Korean title/thumbnail text checks; no quality or CTR score."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'extension/src'))
from youtube_analysis import lint_pair


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--title', required=True)
    p.add_argument('--thumbnail', required=True)
    a = p.parse_args()
    result = lint_pair(a.title, a.thumbnail)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(1 if result['errors'] else 0)
