"""External-tool and format adapters (stage 04 vertical slice).

Adapters wrap file I/O and external executables (FFprobe/FFmpeg) behind
narrow ports; pure calculations live in importable functions with no
subprocess or filesystem access.
"""
