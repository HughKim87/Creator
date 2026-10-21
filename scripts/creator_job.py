"""Creator job CLI; keeps imports and bytecode out of Core."""
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'extension/src'))
from creator_workspace import main

if __name__ == '__main__':
    raise SystemExit(main())
