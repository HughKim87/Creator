# File-Based Work State and Output Lifecycle Contract

- Purpose: Define the minimum persisted state, output lifecycle, and safe file-I/O behavior for one video task.
- Scope: `outputs/<project_id>/state.json`, schema, paths, versions, current/superseded state, approval, retention, integrity, eligibility, and atomic replacement.
- Audience and language: Agents and implementation tools; English.
- Read when: Creating, reading, validating, migrating, or changing file-based video-task state.
- Write when: A verified consumer requires a schema field or the state I/O contract changes.
- Authority: This is the sole L2-L4 state and output-lifecycle contract. Project-wide rules remain in `PROJECT_RULES.md`; current progress remains in `SESSION_HANDOFF.md`; JSON shape is declared in `docs/agent/schemas/video_task_state.schema.json`.

## Contract goals

- Keep one authoritative state file per video task.
- Store only fields required to resume the next operation.
- Preserve stable source identity without copying source content into state.
- Identify each output's role, version, currency, integrity, approval, and next-use eligibility.
- Preserve superseded and failed files unless the user explicitly requests cleanup.
- Reject incomplete, ambiguous, or expanded payloads instead of guessing.
- Never damage the last valid state when a write is interrupted.

## Location and encoding

- State path: `outputs/<project_id>/state.json`.
- Encoding: UTF-8 without a byte-order mark, JSON, one trailing LF.
- `<project_id>` is a portable lowercase ASCII identifier matching
  `[a-z0-9]+(?:[._-][a-z0-9]+)*`.
- Paths stored in the document are repository-relative POSIX paths. They may contain existing Unicode
  filenames, but must not be absolute, contain backslashes, or contain `.` or `..` segments.
- `reference_input.path` must be below `inputs/`.
- Every `outputs[].path` and non-null `outputs[].supersedes` must be below `outputs/<project_id>/`.

## Version 3 schema

The formal structural schema is `docs/agent/schemas/video_task_state.schema.json`. The runtime validator
remains authoritative for cross-record lineage, project-path binding, real-file integrity, and promotion.

```json
{
  "schema_version": 3,
  "project_id": "sample_project",
  "current_stage": "analysis",
  "reference_input": {
    "source_id": "source_001",
    "path": "inputs/synthetic_sample.mp4",
    "fingerprint": {
      "algorithm": "sha256",
      "digest": "0000000000000000000000000000000000000000000000000000000000000000",
      "size_bytes": 1024
    }
  },
  "outputs": [
    {
      "role": "analysis",
      "version": 1,
      "path": "outputs/sample_project/analysis__v001.json",
      "source_id": "source_001",
      "status": "superseded",
      "supersedes": null,
      "integrity": {
        "algorithm": "sha256",
        "digest": "1111111111111111111111111111111111111111111111111111111111111111",
        "size_bytes": 512
      },
      "validation_level": "structure_validated",
      "approval_state": "approved",
      "approval_scope": "next_stage",
      "next_use": "ineligible"
    },
    {
      "role": "analysis",
      "version": 2,
      "path": "outputs/sample_project/analysis__v002.json",
      "source_id": "source_001",
      "status": "current",
      "supersedes": "outputs/sample_project/analysis__v001.json",
      "integrity": {
        "algorithm": "sha256",
        "digest": "2222222222222222222222222222222222222222222222222222222222222222",
        "size_bytes": 640
      },
      "validation_level": "tool_validated",
      "approval_state": "approved",
      "approval_scope": "next_stage",
      "next_use": "eligible"
    }
  ],
  "next_action": "review_analysis",
  "blocker": null,
  "user_decision": null,
  "validation_level": "structure_validated"
}
```

All listed fields are required. Unknown fields are rejected at every object level. Version 1 and version 2
payloads are rejected rather than guessed; no real user state was mapped before version 3 was activated.

## Field rules

| Field | Rule |
|---|---|
| `schema_version` | Integer `3`; booleans are not integers. |
| `project_id` | Portable identifier and identical to the containing directory name. |
| `current_stage` | Non-empty portable identifier for the active stage. |
| `reference_input.source_id` | Stable portable identifier for the exact source fingerprint. A changed fingerprint requires a new source ID. |
| `reference_input.path` | Safe repository-relative path below `inputs/`. |
| `reference_input.fingerprint` | Exact `sha256` digest and non-negative byte size; it identifies without embedding source content. |
| `outputs` | Zero or more retained output records. Paths and `(role, version)` pairs must be unique and use the reference source ID. |
| `outputs[].role` | Non-empty portable identifier describing the consumer-visible output role. |
| `outputs[].version` | Positive integer. Reuse the existing version when governing input and decisions are unchanged. |
| `outputs[].path` | Preserved repository-relative file path below the task directory. Metadata, not the filename, is authoritative. |
| `outputs[].status` | `current`, `superseded`, or `failed`. A role has at most one current output. |
| `outputs[].supersedes` | `null` or the path of one lower version with the same role and source ID. The target must be retained with `superseded` status. |
| `outputs[].integrity` | Exact `sha256` digest and non-negative byte size for the recorded output file. |
| `outputs[].validation_level` | One value from the validation-level list below. |
| `outputs[].approval_state` | `not_required`, `pending`, `approved`, or `revision_requested`. |
| `outputs[].approval_scope` | `none`, `calibration`, `next_stage`, or `final_release`; it states what the decision authorizes. |
| `outputs[].next_use` | `eligible` or `ineligible`; this is the explicit next-operation gate. |
| `next_action` | Non-empty portable identifier for the single next operation. |
| `blocker` | `null` or a non-empty string describing the active blocker. |
| `user_decision` | `null` or a non-empty string containing the latest decision needed by the next operation. |
| `validation_level` | Highest verified level for the state document as a whole. |

Allowed validation levels, from weakest to strongest, are:

1. `generated`
2. `parsed`
3. `structure_validated`
4. `tool_validated`
5. `app_validated`
6. `user_validated`

These labels must not be promoted without the matching evidence.

## Filename and version rules

- Preserve every existing filename. Do not rename prior files to satisfy a new convention.
- For new internal versioned outputs, prefer `<role>__v<zero-padded-version>.<ext>` when the consumer does
  not require a fixed filename. The `role`, `version`, and `path` fields remain authoritative.
- Rerunning unchanged governing inputs and decisions reuses the recorded output and version.
- Create a higher version only when governing input or a user/agent decision changes the result.
- `state.json` is the only current pointer. Do not create a second `CURRENT.json` or encode current status
  only in a filename.

## Lifecycle and retention rules

- A role has at most one `current` record. Multiple current records are a validation failure.
- Promoting a new current version changes the prior record to `superseded` and sets the newer record's
  `supersedes` field to the prior path.
- Every superseded record is referenced by at least one newer retained record. The relation must keep the
  same role and source ID and move to a higher integer version.
- A `failed` record never supersedes another file and is always ineligible. Record it only when a file exists;
  failures without a file belong in task state or the project failure ledger.
- Superseded and failed files remain in place. Report cleanup candidates, but never delete or move them
  without an explicit user request.

## Approval and next-use rules

- `not_required`: no user decision is needed for the next consumer.
- `pending`: the required decision has not been made.
- `approved`: the required user decision is recorded.
- `revision_requested`: the output must be revised before the next consumer uses it.
- `approval_scope` records the purpose of a required decision. `not_required` must use `none`; every other
  approval state must name `calibration`, `next_stage`, or `final_release`.
- `eligible` requires `current` status, at least `structure_validated`, and approval state `not_required` or
  `approved`. A consumer may still mark an otherwise valid current output `ineligible` for a task-specific
  reason recorded in `blocker` or `user_decision`.
- `superseded`, `failed`, `pending`, `revision_requested`, `generated`, and `parsed` outputs cannot be eligible.

## Read and write behavior

1. Validate the requested project ID and the complete in-memory payload before filesystem writes.
2. `save_state(outputs_root, project_id, state)` accepts draft state only. It rejects any `eligible` output,
   so callers cannot persist a promotion without file validation.
3. `save_promoted_state(workspace_root, outputs_root, project_id, state)` requires at least one eligible
   output, binds `outputs_root` to `<workspace_root>/outputs`, validates the designated reference input,
   validates promotion-scope output files, and only then writes the state.
4. Resolve the project directory below the caller-provided outputs root and reject boundary escapes,
   including existing symlinks that resolve outside that root.
5. Write UTF-8 JSON to a temporary file in the same project directory, flush it, and sync it.
6. Atomically replace `state.json` with the temporary file.
7. Delete the temporary file if writing or replacement fails. The previous `state.json` must remain unchanged.
8. On read, reject invalid UTF-8, invalid JSON, unknown versions or fields, bad types, invalid identifiers,
   unsafe paths, source mismatches, duplicate paths or versions, current conflicts, invalid lineage, and
   inconsistent eligibility.
9. Before consuming an eligible output, call `validate_reference_input(workspace_root, state)` and
   `validate_output_files(workspace_root, state, scope="eligible")`.

Output validation never enumerates sibling task directories and supports three bounded scopes:

- `eligible` (default): verify only outputs marked eligible for the next consumer.
- `promotion`: verify eligible outputs and their directly superseded predecessors.
- `all`: verify every retained output for an explicit full audit.

Every selected file must exist inside the workspace and match its SHA-256 digest and byte size. Reference
input validation applies the same checks to the exact declared `reference_input.path`; it does not discover
or infer an input.

`tools/state_io.py` is the reference implementation. It does not enumerate user data, infer a project, or
create a real sample. Its caller must still follow `PROJECT_RULES.md` authorization and user-data boundaries.

## Evolution boundary

- Schema changes require an explicit version change and consumer evidence.
- Original time/frame evidence remains attached to source-derived asset records. Add it to task state only when
  an active consumer needs it; L2 must not duplicate those coordinates speculatively.
- Stage-specific approval decisions and workflow order belong to L5; this contract defines only the common
  storage states needed to enforce next-use safety.
- A generated human-readable `STATE.md` may be added later as a derivative, never as a second state source.
