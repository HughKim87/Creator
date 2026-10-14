"""Make a >=20s fixture from the downloaded official public example."""
import subprocess
import json
import math


def public_reference(verification):
    source = verification / "official-reference.wav"
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(source)], capture_output=True, check=True, timeout=10)
    duration = float(json.loads(probe.stdout)["format"]["duration"])
    repeats = max(1, math.ceil(20 / duration))
    target = verification / f"official-reference-{repeats}x.wav"
    if not target.exists():
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-stream_loop", str(repeats-1),
                        "-i", str(source), "-c:a", "pcm_s16le", str(target)], check=True, timeout=30)
    text = "Okay. Yeah. I resent you. I love you. I respect you. But you know what? You blew it! And thanks to you."
    return str(target), " ".join([text] * repeats)
