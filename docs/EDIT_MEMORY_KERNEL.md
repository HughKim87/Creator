# Edit Memory Kernel

- Role: cross-video data contract for cumulative edit decisions, revision lineage, and evidence.
- Read when: creating, revising, promoting, or diagnosing a Stage 7 edit.
- Retain while: `tools/edit_memory.py` is the active edit-memory implementation.
- Per-video facts and databases stay under `outputs/`; this document contains no episode facts.

## Purpose

The kernel preserves edit judgment without turning every preference into a hard
rule. It keeps immutable events and builds queryable current state from them.
Operational retry counters may reset; rejection memory does not disappear until
a later feedback event explicitly supersedes it.

## Model

| Aggregate | Meaning |
|---|---|
| `source_atom` | Time-bounded utterance or visual unit with safe cut evidence |
| `story_beat` | Viewer information and character-state change |
| `revision` | A hypothesis derived from an identified parent revision |
| `timeline_node` | A source range, track, and placement used in a revision |
| `timeline_edge` | Semantic and A/V relationship between adjacent nodes |
| `revision_operation` | Atomic change plus preserved targets |
| `feedback` | Durable judgment attached to a target and scope |
| `evaluation` | Observation method, evidence, and scoped verdict |
| `baseline` | `working`, `preferred`, or user `approved` pointer |

`working` is agent-selected and may advance autonomously. `approved` is stable
user direction. Rejected or superseded revisions cannot be baseline targets.

## Storage

- SQLite is the source of truth for exact IDs, times, lineage, and events.
- Every mutation enters through an append-only event batch.
- Reapplying an identical event is safe; changing an existing event ID fails.
- `CURRENT.json` is a generated view, never the mutation source.
- Similarity search may be added later, but embeddings never replace exact IDs.

## Commands

Use the project Python wrapper.

```bat
tools\run_python.bat tools\edit_memory.py init --db <database>
tools\run_python.bat tools\edit_memory.py apply --db <database> --input <event-batch.json>
tools\run_python.bat tools\edit_memory.py validate --db <database>
tools\run_python.bat tools\edit_memory.py export --db <database> --output <CURRENT.json>
```

Validation errors cover corrupted lineage and invalid pointers. Missing working
or approved baselines and missing actual A/V observations are warnings: they are
visible evidence gaps, not blanket bans on autonomous exploration.
