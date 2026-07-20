---
doc_id: doc.file_state
kind: contract
domain: state
lifecycle: active
authority: normative for the versioned video-task state model and field meaning
audience: agent_tool
language: en
validation: tool_validated
purpose: Define the versioned shape and semantic invariants of one video task state file.
scope: Schema identity, fields, source binding, lineage, and evolution; normal read, write, promotion, retention, and next-use procedures live in STATE_OPERATIONS.md.
read_when: Changing the state schema, diagnosing a field or lineage error, or migrating an explicitly designated state file.
write_when: A verified consumer requires a schema version, field, enum, or cross-record invariant change.
---
# Video Task State Contract

## Model goals

- Keep one authoritative `state.json` per video task.
- Store only fields required to resume the next operation.
- Bind one stable source ID to one exact fingerprint without embedding source content.
- Identify every output's role, version, currency, lineage, integrity, approval, and next-use eligibility.
- Reject incomplete, ambiguous, unknown-version, or expanded payloads instead of guessing.

## Version 3 shape

The machine shape is `docs/agent/state/schemas/video_task_state.schema.json`. All declared fields are required and unknown fields are rejected at every object level. `tools/state_io.py` additionally validates cross-record lineage, project-path binding, real-file integrity, and promotion.

| Field | Semantic invariant |
|---|---|
| `schema_version` | Integer `3`; prior versions require an explicit migration decision |
| `project_id` | Portable ID equal to the containing task directory |
| `current_stage` | Non-empty portable ID for the active stage |
| `reference_input` | Exact source ID, safe `inputs/` path, SHA-256 digest, and byte size |
| `outputs` | Unique paths and `(role, version)` pairs bound to the reference source ID |
| `outputs[].role` | Consumer-visible portable output role |
| `outputs[].version` | Positive integer; unchanged governing input reuses the version |
| `outputs[].path` | Safe path below the designated task directory; metadata is authoritative |
| `outputs[].status` | `current`, `superseded`, or `failed`; at most one current item per role |
| `outputs[].supersedes` | `null` or one retained lower version with the same role and source ID |
| `outputs[].integrity` | Exact SHA-256 digest and non-negative byte size |
| `outputs[].validation_level` | `generated`, `parsed`, `structure_validated`, `tool_validated`, `app_validated`, or `user_validated` |
| `outputs[].approval_state` | `not_required`, `pending`, `approved`, or `revision_requested` |
| `outputs[].approval_scope` | `none`, `calibration`, `next_stage`, or `final_release` |
| `outputs[].next_use` | Explicit `eligible` or `ineligible` consumer gate |
| `next_action` | One non-empty portable next-operation ID |
| `blocker` | `null` or one non-empty active blocker |
| `user_decision` | `null` or the latest decision needed by the next operation |
| `validation_level` | Highest evidence-backed validation level for the state document |

Booleans are never accepted as integers. Paths are repository-relative POSIX paths without absolute roots, backslashes, `.` segments, `..` segments, or boundary escapes.

## Source and lineage invariants

- A changed source fingerprint requires a new source ID.
- Output paths and `(role, version)` pairs are unique and use the reference source ID.
- A superseding output keeps the same role and source ID, has a higher integer version, and points to one retained predecessor marked `superseded`.
- A failed output never supersedes another output and is always ineligible.
- Validation labels are not promoted without matching evidence.

## Evolution boundary

- A schema change requires a new integer version, updated JSON Schema, runtime validation, synthetic regression tests, and an explicit migration decision for any designated older state.
- Original time/frame evidence remains with source-derived asset records unless a verified consumer requires it here.
- Stage-specific workflow order belongs to the workflow authority; this contract owns only common persisted state.
- A generated `STATE.md` may be a derivative view but never a second state source.
