"""Serialize existing PNGs to the documented veadotube mini .veado format.

Sources: https://veado.tube/docs/tech/file/ and subpages images/, miniavatar/.
No source images are edited. Actual application import is a separate check.
"""
from pathlib import Path
import struct
from PIL import Image

ROOT = Path(__file__).resolve().parent

def integer(value):
    out = bytearray()
    while value >= 128:
        out.append((value & 127) | 128)
        value >>= 7
    return bytes(out + bytes([value]))

def string(value):
    encoded = value.encode('utf-8')
    return integer(len(encoded)) + encoded

def effect(kind, values):
    return string(kind) + b'\x01' + integer(len(values)) + struct.pack('<' + 'd' * len(values), *values)

def build():
    chunks = []
    def add(kind, payload):
        ident = len(chunks) + 1
        chunks.append((ident, kind.encode('ascii'), payload))
        return ident
    add('META', string('Creator avatar pack builder') + string('Kimsilver') + string('Silver knight: idle, talking, blink. Import and microphone verification pending.'))
    add('THMB', (ROOT / '01-idle.png').read_bytes())
    images = []
    for filename in ['01-idle.png', '02-talking.png', '03-blink.png']:
        with Image.open(ROOT / filename) as source:
            rgba = source.convert('RGBA')
            width, height = rgba.size
            raw = rgba.transpose(Image.Transpose.FLIP_TOP_BOTTOM).tobytes()
        texture = add('ABMP', struct.pack('<II', width, height) + b'RAW.' + raw)
        ident = add('AIMG', struct.pack('<II', width, height) + integer(1) + struct.pack('<IIId', texture, 0, 0, 0.0))
        images.append(ident)
    slots = [images[0], images[1], images[2], images[2]]
    # Mini 2.2 native autosaves encode flags as UInt32, not the byte
    # described in the older public format page. They also include three
    # blink timing doubles immediately after the eight image references.
    state = string('Kimsilver Knight') + struct.pack('<I', 2)
    state += struct.pack('<8I', *(slots + slots))
    state += struct.pack('<3d', 0.15, 0.75, 4.0)
    state += integer(0)  # no idle effects
    state += integer(1) + effect('wavemove', [0.0, 0.006, 0.32, 0.0])
    state += integer(1) + effect('jump', [0.012, 1.0])
    state += integer(0)  # no transition back to idle
    state += integer(0) + b'PRES'  # native press shortcut mode, no shortcuts
    state_id = add('MSTA', state)
    add('MLST', struct.pack('<I', state_id))
    assets = b'MINI'
    for ident in images:
        assets += string(f'image{ident:08x}') + struct.pack('<I', ident) + b'\x00'
    add('ASFD', assets)
    result = b'VEADOTUBE'
    for ident, kind, payload in chunks:
        result += struct.pack('<I4sI', ident, kind, len(payload)) + payload
    # Follow the native order: metadata, state list, thumbnail, asset table,
    # states, images, textures. Preserve original IDs for cross-references.
    order = {b'META': 0, b'MLST': 1, b'THMB': 2, b'ASFD': 3, b'MSTA': 4, b'AIMG': 5, b'ABMP': 6}
    result = b'VEADOTUBE'
    for ident, kind, payload in sorted(chunks, key=lambda item: order[item[1]]):
        result += struct.pack('<I4sI', ident, kind, len(payload)) + payload
    result += bytes(12)
    target = ROOT / 'kimsilver-knight-v2.veado'
    target.write_bytes(result)
    verify(target)
    print(f'Created: {target} ({len(result):,} bytes)')

def verify(path):
    data = path.read_bytes()
    assert data[:9] == b'VEADOTUBE'
    offset, found = 9, {}
    while offset < len(data):
        ident, kind, size = struct.unpack_from('<I4sI', data, offset)
        if ident == 0:
            assert kind == bytes(4) and size == 0
            offset += 12
            break
        # The retained native v3 export contains empty MEPL/MANL lists.
        # Accept those observed empty containers; media/state chunks stay nonempty.
        assert kind != bytes(4) and ident not in found
        assert size > 0 or kind in (b'MEPL', b'MANL')
        offset += 12
        payload = data[offset:offset + size]
        assert len(payload) == size
        found[ident] = (kind, payload)
        offset += size
    assert offset == len(data)
    state_ids = [struct.unpack('<I', payload)[0] for kind, payload in found.values() if kind == b'MLST']
    assert len(state_ids) == 1 and found[state_ids[0]][0] == b'MSTA'
    texture_count = 0
    for kind, payload in found.values():
        if kind == b'ABMP':
            w, h = struct.unpack_from('<II', payload)
            assert payload[8:12] == b'RAW.' and len(payload) == 12 + w * h * 4
            texture_count += 1
        elif kind == b'AIMG':
            assert payload[8] == 1
            ref = struct.unpack_from('<I', payload, 9)[0]
            assert found[ref][0] == b'ABMP'
    assert texture_count == 3
    validate_native_state(found[state_ids[0]][1], found)
    print('PASS: chunk boundaries, IDs, state reference, texture references, RGBA lengths.')
    print('NOT RUN: native veadotube import, effect playback, physical microphone reaction.')

def read_integer(data, offset):
    value = shift = 0
    while True:
        byte = data[offset]
        offset += 1
        value |= (byte & 127) << shift
        if byte < 128:
            return value, offset
        shift += 7
        assert shift < 35

def read_string(data, offset):
    size, offset = read_integer(data, offset)
    value = data[offset:offset + size].decode('utf-8')
    assert len(data[offset:offset + size]) == size
    return value, offset + size

def validate_native_state(data, chunks=None):
    name, offset = read_string(data, 0)
    flags = struct.unpack_from('<I', data, offset)[0]
    offset += 4
    assert flags < 8
    refs = struct.unpack_from('<8I', data, offset)
    offset += 32
    timings = struct.unpack_from('<3d', data, offset)
    offset += 24
    assert 0 < timings[0] < 1 and 0 <= timings[1] <= timings[2] <= 60
    if chunks:
        assert all(ref == 0 or chunks[ref][0] == b'AIMG' for ref in refs)
    for _ in range(4):
        count, offset = read_integer(data, offset)
        assert count < 100
        for _ in range(count):
            _, offset = read_string(data, offset)
            effect_flags = data[offset]
            offset += 1
            if effect_flags & 4:
                offset += 4
            elif effect_flags & 2:
                _, offset = read_string(data, offset)
            values, offset = read_integer(data, offset)
            assert values < 100
            offset += 8 * values
    shortcuts, offset = read_integer(data, offset)
    for _ in range(shortcuts):
        _, offset = read_string(data, offset)
        _, offset = read_string(data, offset)
    assert data[offset:offset + 4] in [b'PRES', b'TOGL', b'HOLD']
    offset += 4
    assert offset == len(data), (name, offset, len(data))
    return name, timings

if __name__ == '__main__':
    build()
