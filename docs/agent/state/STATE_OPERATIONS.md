---
doc_id: doc.state_operations
kind: contract
domain: state
lifecycle: active
authority: normative for normal video-task state I/O, lifecycle, approval, and next-use operations
audience: agent_tool
language: en
validation: tool_validated
purpose: Define how an agent safely reads, writes, promotes, retains, and consumes a designated video task state.
scope: Normal version-3 operations through tools/state_io.py; schema-field changes and migrations live in VIDEO_TASK_STATE.md.
read_when: Reading, writing, validating, promoting, or deciding next use for an exact designated state.json.
write_when: Safe I/O, output lifecycle, approval, retention, or next-use behavior changes without changing the state shape.
---
# Video Task State Operations

## Location and encoding

- State path: `outputs/<project_id>/state.json`.
- Encoding: UTF-8 without BOM, JSON, one trailing LF.
- `<project_id>` matches `[a-z0-9]+(?:[._-][a-z0-9]+)*`.
- Stored paths are repository-relative POSIX paths. Reference input stays below `inputs/`; outputs and `supersedes` stay below `outputs/<project_id>/`.
- The caller supplies the exact project ID and state path. Never enumerate sibling tasks.

## Filename and version

- Preserve existing filenames. For a new internal versioned output, prefer `<role>__v<zero-padded-version>.<ext>` unless a consumer requires a fixed name.
- Reuse the current output and version when governing input and decisions are unchanged. Create a higher version only when they change the result.
- `state.json` is the only current pointer; do not add `CURRENT.json` or rely on filenames for currency.

## Lifecycle and retention

- A role has at most one `current` output.
- Promoting a new current output marks its retained predecessor `superseded` and records that predecessor path.
- A `failed` record exists only when a file exists, never supersedes another file, and is always ineligible.
- Preserve current, superseded, and failed files. Report cleanup candidates but never delete or move them without explicit user approval.

## Approval and next use

- `not_required` uses scope `none`; `pending`, `approved`, and `revision_requested` name `calibration`, `next_stage`, or `final_release`.
- `eligible` requires `current`, at least `structure_validated`, and approval `not_required` or `approved`.
- An otherwise valid current output may remain ineligible for a task-specific reason recorded in `blocker` or `user_decision`.
- `superseded`, `failed`, `pending`, `revision_requested`, `generated`, and `parsed` outputs are ineligible.

## Approved I/O path

| Operation | Required call and evidence |
|---|---|
| Read or validate | `load_state(outputs_root, project_id)` returns one complete version-3 state or fails closed |
| Save draft | `save_state(outputs_root, project_id, state)` rejects every eligible output |
| Promote | `save_promoted_state(workspace_root, outputs_root, project_id, state)` verifies the reference and promotion-scope files before atomic replacement |
| Consume next | `validate_reference_input(workspace_root, state)` and `validate_output_files(workspace_root, state, scope="eligible")` both pass |
| Full audit | `validate_output_files(..., scope="all")` only after an explicit full-audit request |

The implementation validates the complete in-memory payload before writes, confines paths below caller-provided roots, rejects escaping symlinks, writes a same-directory temporary file, flushes and syncs it, and atomically replaces `state.json`. Failure removes the temporary file and preserves the previous state.

Output scopes are `eligible` by default, `promotion` for eligible outputs plus direct predecessors, and `all` for every retained output. Every selected file must exist and match its SHA-256 digest and byte size.

## Failure and authority

- Invalid UTF-8 or JSON, unknown fields or versions, unsafe paths, type errors, source mismatch, duplicate paths or versions, current conflicts, invalid lineage, integrity mismatch, or inconsistent eligibility is a non-zero failure.
- `tools/state_io.py` is the reference implementation. It does not discover user data or infer a project.
- The caller still obeys `PROJECT_RULES.md`; an Obsidian exclusion is never an access-control boundary.
- Schema or field changes route to `VIDEO_TASK_STATE.md` and its schema/tests instead of expanding this operational read.
