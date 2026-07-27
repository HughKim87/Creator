"""Validated video-edit timeline primitives."""

from .model import (
    CLIP_FIELDS,
    SEMANTIC_GATE_FIELDS,
    SEQUENCE_FIELDS,
    SOURCE_FIELDS,
    TIMELINE_FIELDS,
    TIMELINE_VERSION,
    TimelineValidationError,
    inspect_timeline,
    validate_timeline,
)
from .premiere_xml import (
    PremiereXmlError,
    build_premiere_xml,
    write_premiere_xml,
)

__all__ = [
    "CLIP_FIELDS",
    "SEMANTIC_GATE_FIELDS",
    "SEQUENCE_FIELDS",
    "SOURCE_FIELDS",
    "TIMELINE_FIELDS",
    "TIMELINE_VERSION",
    "PremiereXmlError",
    "TimelineValidationError",
    "build_premiere_xml",
    "inspect_timeline",
    "validate_timeline",
    "write_premiere_xml",
]
