# Agent Entry Router

- Purpose: Route agents to the minimum project documents required for the current task.
- Scope: Document selection and write-back routing only; this file contains no project policy or task state.
- Audience and language: Agents; English.
- Read when: At the start of any task that reads or changes this workspace.
- Write when: Only when document roles or routing rules change.
- Authority: `PROJECT_RULES.md` is the sole global-rule source, `SESSION_HANDOFF.md` is the sole current-state source, and `docs/agent/DOCUMENT_REGISTRY.md` is the sole document-classification registry.

## Required startup

1. Read `PROJECT_RULES.md` completely.
2. Read `SESSION_HANDOFF.md` when continuing, changing, or verifying project work.
3. Select only the additional document or bounded section required by the table below and read that selection completely.
4. If a required authority is missing or ambiguous, stop and read `docs/agent/DOCUMENT_REGISTRY.md`; do not guess from filenames.
5. Do not bulk-read `docs/`, `inputs/`, or `outputs/`.

## Selection protocol

1. Map the request to one stable route ID below. For independent intents, union only the applicable rows and deduplicate the result.
2. Read the startup set, then the exact read delta. Resolve an `affected`, `named`, or `designated` selector to a document ID, bounded heading, or exact user-named item before opening it.
3. A document link, registry relationship, similar wording, or nearby folder is not a read trigger by itself.
4. Use the table directly. Do not expand from one selected document to another unless the same route row explicitly requires it.
5. If the route is ambiguous, a required selector is missing, or a protected path would be crossed, stop the unresolved part and report it to the user; do not guess or silently substitute another route.
6. If no route applies, use `docs/agent/DOCUMENT_REGISTRY.md` to identify the narrowest authority. Add a route only when the task type is expected to recur.

## Task routing

| Route ID | Task intent | Required read delta | Selector before read | Do not read by default |
|---|---|---|---|---|
| `resume_current_work` | Resume or report current work | None | None | Plans, contracts, and reports |
| `execute_rebuild_layer` | Execute or review a rebuild layer | `docs/agent/REBUILD_PLAN.md` | Affected layer section only | Other layers and historical reports |
| `audit_reconstructed_capability` | Audit L0-L4 or review a reconstructed capability | `docs/agent/REBUILD_PLAN.md` and `docs/agent/RECONSTRUCTION_MAP.md` | Affected sections, relevant rows, and only active authorities named there | Migration sources, unrelated documents, and user data |
| `handle_video_task_state` | Read, write, validate, or migrate video-task state | `docs/agent/FILE_DATA_CONTRACT.md` | Exact designated task `state.json` | Other task directories and unrelated contracts |
| `change_rebuild_scope` | Change rebuild direction, scope, or exceptions | `docs/agent/REBUILD_PRINCIPLES.md` and `docs/agent/REBUILD_PLAN.md` | Relevant principle and affected plan section | Unrelated plan sections |
| `design_l5_workflow` | Design L5 workflow rules | `docs/agent/REBUILD_PLAN.md`, `docs/agent/WORKFLOW_FOUNDATION.md`, `docs/agent/EDITING_QUALITY_RULES.md`, and `docs/agent/FILE_DATA_CONTRACT.md` | L5 plan section and applicable contract sections | Migration sources, tool implementation details, and other layers |
| `select_l7_tool` | Select or implement an L7 tool | `docs/agent/REBUILD_PLAN.md` and `docs/agent/TOOL_REQUIREMENTS.md` | L7 section, relevant capability, and active consumer contract | Unselected capabilities and migration sources |
| `select_l8_skill` | Select or implement an L8 skill | `docs/agent/REBUILD_PLAN.md` and `docs/agent/SKILL_REQUIREMENTS.md` | L8 section, relevant responsibility, and active stage/tool contracts | Unselected skills and migration sources |
| `change_framework_capability` | Add, replace, defer, or remove a framework capability | `docs/agent/RECONSTRUCTION_MAP.md` | Relevant row, then only its active authority | Migration sources and unrelated capabilities |
| `change_document_route` | Change or audit document architecture | `docs/agent/DOCUMENT_REGISTRY.md` | Affected active documents only | Document bodies unrelated to the change |
| `review_user_status` | Review current user status | `docs/user/PROJECT_STATUS.md` | None | Agent plans and historical reports |
| `review_history` | Investigate project history or a superseded proposal | None | Exact named file in `docs/reports/` | Other reports and active authorities unless needed to show supersession |
| `work_on_user_data` | Work on user data | None | Exact user-named `inputs/` or `outputs/` item and purpose | Directory enumeration and unrelated data |

## Validated representative profiles

| Profile | Complete read set | Allowed write set | Explicit exclusions |
|---|---|---|---|
| `resume_current_work` | `AGENTS.md`, `PROJECT_RULES.md`, `SESSION_HANDOFF.md` | None for reporting; handoff only if verified state changes | Plans, contracts, and reports |
| `change_document_route` | Startup, `docs/agent/DOCUMENT_REGISTRY.md`, and affected active documents | Registry, router, and affected authorities only | Unrelated documents, user data, and migration sources |
| `handle_video_task_state` | Startup, `docs/agent/FILE_DATA_CONTRACT.md`, and the exact designated `state.json` | Designated state through the approved I/O path; contract only for an approved schema change | Other tasks, rebuild documents, migration sources, and reports |

## Write-back routing

| Write ID | Information changed | Write to |
|---|---|---|
| `global_rule` | Project-wide rule | `PROJECT_RULES.md` |
| `current_state` | Current stage, blocker, active failure, verification, or next action | `SESSION_HANDOFF.md` |
| `document_classification` | Document classification or reference relationship | `docs/agent/DOCUMENT_REGISTRY.md` |
| `rebuild_principle` | Rebuild principle or stop condition | `docs/agent/REBUILD_PRINCIPLES.md` |
| `rebuild_plan` | Layer scope, deliverable, verification, rollback, or gate | `docs/agent/REBUILD_PLAN.md` |
| `file_state_contract` | File-state schema or lifecycle behavior | `docs/agent/FILE_DATA_CONTRACT.md` and its schema/tests |
| `capability_decision` | Capability reconstruction, deferral, or exclusion decision | `docs/agent/RECONSTRUCTION_MAP.md` |
| `workflow_foundation` | Workflow foundation requirement | `docs/agent/WORKFLOW_FOUNDATION.md` |
| `editing_quality` | Editing-quality requirement | `docs/agent/EDITING_QUALITY_RULES.md` |
| `tool_requirement` | Reusable tool requirement | `docs/agent/TOOL_REQUIREMENTS.md` |
| `skill_requirement` | Workflow skill requirement | `docs/agent/SKILL_REQUIREMENTS.md` |
| `user_milestone` | Current user-facing milestone | `docs/user/PROJECT_STATUS.md` |
| `point_in_time_report` | Point-in-time analysis | A Korean file in `docs/reports/`, marked historical or superseded |

Do not duplicate a durable rule, state, plan, classification, or decision. Link to its authority instead.
