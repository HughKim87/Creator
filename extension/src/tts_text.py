"""Bounded text chunks for local speech engines, preserving words and punctuation."""
import re

CHUNK_CHARACTERS = 180


def split_script(script, maximum=CHUNK_CHARACTERS):
    if maximum < 1:
        raise ValueError('Chunk size must be positive')
    remaining = (script or '').strip()
    chunks = []
    while len(remaining) > maximum:
        window = remaining[:maximum]
        # Prefer complete sentences/paragraphs, then words; hard split only
        # when a long sentence has no usable boundary.
        boundaries = list(re.finditer(r'[.!?。！？]+[\"\'”’」』)]*(?=\s|$)|\n+', window))
        end = boundaries[-1].end() if boundaries else 0
        if not end:
            spaces = list(re.finditer(r'\s+', window))
            end = spaces[-1].end() if spaces else maximum
        chunks.append(remaining[:end].rstrip())
        remaining = remaining[end:].lstrip()
    if remaining:
        chunks.append(remaining)
    return chunks
