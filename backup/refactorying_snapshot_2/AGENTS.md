# Agent Entry Router

- Purpose: Route agents to the minimum project documents required for the current task.
- Scope: Document selection and write-back routing only; this file contains no project policy or task state.
- Audience and language: Agents; English.
- Read when: At the start of any task that reads or changes this workspace.
- Write when: Only when document roles or routing rules change.
- Authority: `PROJECT_RULES.md` is the sole global-rule source, `SESSION_HANDOFF.md` is the sole current-state source, and `docs/agent/navigation/DOCUMENT_REGISTRY.md` is the sole document-classification contract.

## Required startup

1. Read `PROJECT_RULES.md` completely.
2. Read `SESSION_HANDOFF.md` when continuing, changing, or verifying project work.
3. Select only the additional document or bounded section required by the table below and read that selection completely.
4. If a known authority's properties are missing or ambiguous, read `docs/agent/navigation/DOCUMENT_REGISTRY.md`. If no route applies or a selector cannot be resolved, use the bounded discovery procedure below.
5. Do not bulk-read `docs/`, `inputs/`, or `outputs/`.

## Selection protocol

1. Map the request to one stable route ID below. For independent intents, union only the applicable rows and deduplicate the result.
2. Read the startup set, then the exact read delta. Resolve an `affected`, `named`, or `designated` selector to a document ID, bounded heading, or exact user-named item before opening it.
3. A document link, registry relationship, similar wording, or nearby folder is not a read trigger by itself.
4. Use the table directly for every known route. Do not expand from one selected document to another unless the same route row explicitly requires it.
5. If no route applies or an affected authority cannot be resolved by exact ID or path, read `docs/agent/tooling/TOOL_REQUIREMENTS.md#agent-document-discovery-contract` and call the official Obsidian CLI directly against the narrowest Base domain view or domain folder.
6. Treat CLI results as candidates, not read authority. Compare only the `purpose` and `authority` properties; read `scope` and `read_when` only for a tie. Select one atomic note before reading its content.
7. If discovery fails, returns no result, remains ambiguous, or would cross a protected path, stop the unresolved part and report it; do not guess, silently use direct routing, or switch to another search engine.
8. Add a stable route only when a task type recurs and the direct route removes measured discovery work; do not add routes for one-off searches.

## Task routing

| Route ID | Task intent | Required read delta | Selector before read | Do not read by default |
|---|---|---|---|---|
| `resume_current_work` | Resume or report current work | None | None | Plans, contracts, and reports |
| `execute_rebuild_layer` | Execute or review a rebuild layer | `docs/agent/rebuild/REBUILD_PLAN.md` | Affected layer section only | Other layers and historical reports |
| `audit_reconstructed_capability` | Audit L0-L4 or review a reconstructed capability | `docs/agent/rebuild/REBUILD_PLAN.md` and `docs/agent/rebuild/RECONSTRUCTION_MAP.md` | Affected sections, relevant rows, and only active authorities named there | Migration sources, unrelated documents, and user data |
| `handle_video_task_state` | Read, write, validate, promote, or decide next use for video-task state | `docs/agent/state/STATE_OPERATIONS.md` | Exact designated task `state.json` and operation | Other task directories, schema internals, and unrelated contracts |
| `change_video_state_contract` | Change state fields, schema version, or migration semantics | `docs/agent/state/VIDEO_TASK_STATE.md` and `docs/agent/state/schemas/video_task_state.schema.json` | Affected field/version and exact designated migration item, if any | Normal operations, other tasks, and unrelated contracts |
| `change_rebuild_scope` | Change rebuild direction, scope, or exceptions | `docs/agent/rebuild/REBUILD_PRINCIPLES.md` and `docs/agent/rebuild/REBUILD_PLAN.md` | Relevant principle and affected plan section | Unrelated plan sections |
| `design_l5_workflow` | Design L5 workflow rules | `docs/agent/rebuild/REBUILD_PLAN.md`, `docs/agent/workflow/WORKFLOW_FOUNDATION.md`, `docs/agent/workflow/EDITING_QUALITY_RULES.md`, and `docs/agent/state/STATE_OPERATIONS.md` | L5 plan section and applicable contract sections | Migration sources, schema internals, tool implementation details, and other layers |
| `select_l7_tool` | Select or implement an L7 tool | `docs/agent/rebuild/REBUILD_PLAN.md` and `docs/agent/tooling/TOOL_REQUIREMENTS.md` | L7 section, relevant capability, and active consumer contract | Unselected capabilities and migration sources |
| `select_l8_skill` | Select or implement an L8 skill | `docs/agent/rebuild/REBUILD_PLAN.md` and `docs/agent/tooling/SKILL_REQUIREMENTS.md` | L8 section, relevant responsibility, and active stage/tool contracts | Unselected skills and migration sources |
| `change_framework_capability` | Add, replace, defer, or remove a framework capability | `docs/agent/rebuild/RECONSTRUCTION_MAP.md` | Relevant row, then only its active authority | Migration sources and unrelated capabilities |
| `change_document_route` | Move, rename, split, merge, or relink a document | `docs/agent/navigation/DOCUMENT_PLACEMENT.md` | Exact affected note properties and destination | Unrelated note bodies, user data, and historical reports |
| `change_document_classification` | Change document properties, domains, lifecycle classes, or Base views | `docs/agent/navigation/DOCUMENT_REGISTRY.md` | Exact affected note properties or Base view | Unrelated note bodies and user data |
| `review_user_status` | Review current user status | `docs/user/PROJECT_STATUS.md` | None | Agent plans and historical reports |
| `review_history` | Investigate project history or a superseded proposal | None | Exact named file in `docs/reports/` | Other reports and active authorities unless needed to show supersession |
| `work_on_user_data` | Work on user data | None | Exact user-named `inputs/` or `outputs/` item and purpose | Directory enumeration and unrelated data |

## Write-back routing

| Write ID | Information changed | Write to |
|---|---|---|
| `global_rule` | Project-wide rule | `PROJECT_RULES.md` |
| `current_state` | Current stage, blocker, active failure, verification, or next action | `SESSION_HANDOFF.md` |
| `document_classification` | One note's classification | Its YAML properties; `docs/agent/navigation/DOCUMENT_REGISTRY.md` only when the property schema or Base changes |
| `document_placement` | Folder, name, split, merge, move, or reference behavior | `docs/agent/navigation/DOCUMENT_PLACEMENT.md` |
| `rebuild_principle` | Rebuild principle or stop condition | `docs/agent/rebuild/REBUILD_PRINCIPLES.md` |
| `rebuild_plan` | Layer scope, deliverable, verification, rollback, or gate | `docs/agent/rebuild/REBUILD_PLAN.md` |
| `file_state_model` | File-state field, schema, or migration behavior | `docs/agent/state/VIDEO_TASK_STATE.md` and its schema/tests |
| `state_operation` | State I/O, lifecycle, approval, retention, or next-use behavior | `docs/agent/state/STATE_OPERATIONS.md` and implementation tests |
| `capability_decision` | Capability reconstruction, deferral, or exclusion decision | `docs/agent/rebuild/RECONSTRUCTION_MAP.md` |
| `workflow_foundation` | Workflow foundation requirement | `docs/agent/workflow/WORKFLOW_FOUNDATION.md` |
| `editing_quality` | Editing-quality requirement | `docs/agent/workflow/EDITING_QUALITY_RULES.md` |
| `tool_requirement` | Reusable tool requirement | `docs/agent/tooling/TOOL_REQUIREMENTS.md` |
| `skill_requirement` | Workflow skill requirement | `docs/agent/tooling/SKILL_REQUIREMENTS.md` |
| `user_milestone` | Current user-facing milestone | `docs/user/PROJECT_STATUS.md` |
| `point_in_time_report` | Point-in-time analysis | A Korean file in `docs/reports/`, marked historical or superseded |

Do not duplicate a durable rule, state, plan, classification, or decision. Link to its authority instead.
