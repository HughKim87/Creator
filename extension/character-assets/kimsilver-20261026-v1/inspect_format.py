from pathlib import Path
import struct
from build_avatar import validate_native_state

log = Path('C:/Users/Hugh/.veadotube/logs/2026-10-25-21-51-56-mini-08df32e230914c22-00001060.log')
for line in log.read_text(encoding='utf-8', errors='replace').splitlines():
    if any(t in line.lower() for t in ['error', 'exception', 'invalid', 'failed', 'kimsilver', 'load', 'veadotube mini']):
        print(line)

for path in [Path('C:/Users/Hugh/.veadotube/data/mini/autosave.veado'), Path(__file__).parent / 'kimsilver-knight-v2.veado']:
    data = path.read_bytes()
    print(path.name, data[:9])
    offset = 9
    while offset + 12 <= len(data):
        ident, kind, size = struct.unpack_from('<I4sI', data, offset)
        if ident == 0:
            break
        payload = data[offset + 12:offset + 12 + size]
        if kind == b'MSTA':
            name, timings = validate_native_state(payload)
            print('PASS native-state decode:', name, 'blink timings:', timings)
        offset += 12 + size
