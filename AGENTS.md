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

## Task routing

| Task | Read in addition to startup | Do not read by default |
|---|---|---|
| Resume or report current work | No additional document | Plans, contracts, and reports |
| Execute or review a rebuild layer | Only affected sections in `docs/agent/REBUILD_PLAN.md` | Other layers and historical reports |
| Audit L0-L4 or review a reconstructed capability | Affected plan sections, relevant rows in `docs/agent/RECONSTRUCTION_MAP.md`, and only the active authorities named there | Migration sources, unrelated documents, and user data |
| Read, write, validate, or migrate video-task state | `docs/agent/FILE_DATA_CONTRACT.md` and only the designated task state | Other task directories and unrelated contracts |
| Change rebuild direction, scope, or exceptions | Relevant section of `docs/agent/REBUILD_PRINCIPLES.md` and the affected plan section | Unrelated plan sections |
| Design L5 workflow rules | L5 plan section, `docs/agent/WORKFLOW_FOUNDATION.md`, `docs/agent/EDITING_QUALITY_RULES.md`, and the state contract | Migration sources, tool implementation details, and other layers |
| Select or implement an L7 tool | L7 plan section, relevant capability in `docs/agent/TOOL_REQUIREMENTS.md`, and its active consumer contract | Unselected capabilities and migration sources |
| Select or implement an L8 skill | L8 plan section, relevant responsibility in `docs/agent/SKILL_REQUIREMENTS.md`, and its active stage/tool contracts | Unselected skills and migration sources |
| Add, replace, defer, or remove a framework capability | Relevant row in `docs/agent/RECONSTRUCTION_MAP.md`, then only its active authority | Migration sources and unrelated capabilities |
| Change or audit document architecture | `docs/agent/DOCUMENT_REGISTRY.md` and affected active documents | Document bodies unrelated to the change |
| Review current user status | `docs/user/PROJECT_STATUS.md` | Agent plans and historical reports |
| Investigate project history or a superseded proposal | Only the specifically requested file in `docs/reports/` | Active authorities unless needed to show supersession |
| Work on user data | Only the exact `inputs/` or `outputs/` item and purpose named by the user | Directory enumeration and unrelated data |

## Validated representative profiles

| Profile | Complete read set | Allowed write set | Explicit exclusions |
|---|---|---|---|
| `resume_current_work` | `AGENTS.md`, `PROJECT_RULES.md`, `SESSION_HANDOFF.md` | None for reporting; handoff only if verified state changes | Plans, contracts, and reports |
| `change_document_route` | Startup, `docs/agent/DOCUMENT_REGISTRY.md`, and affected active documents | Registry, router, and affected authorities only | Unrelated documents, user data, and migration sources |
| `handle_video_task_state` | Startup, `docs/agent/FILE_DATA_CONTRACT.md`, and the exact designated `state.json` | Designated state through the approved I/O path; contract only for an approved schema change | Other tasks, rebuild documents, migration sources, and reports |

## Write-back routing

| Information changed | Write to |
|---|---|
| Project-wide rule | `PROJECT_RULES.md` |
| Current stage, blocker, active failure, verification, or next action | `SESSION_HANDOFF.md` |
| Document classification or reference relationship | `docs/agent/DOCUMENT_REGISTRY.md` |
| Rebuild principle or stop condition | `docs/agent/REBUILD_PRINCIPLES.md` |
| Layer scope, deliverable, verification, rollback, or gate | `docs/agent/REBUILD_PLAN.md` |
| File-state schema or lifecycle behavior | `docs/agent/FILE_DATA_CONTRACT.md` and its schema/tests |
| Capability reconstruction, deferral, or exclusion decision | `docs/agent/RECONSTRUCTION_MAP.md` |
| Workflow foundation requirement | `docs/agent/WORKFLOW_FOUNDATION.md` |
| Editing-quality requirement | `docs/agent/EDITING_QUALITY_RULES.md` |
| Reusable tool requirement | `docs/agent/TOOL_REQUIREMENTS.md` |
| Workflow skill requirement | `docs/agent/SKILL_REQUIREMENTS.md` |
| Current user-facing milestone | `docs/user/PROJECT_STATUS.md` |
| Point-in-time analysis | A Korean file in `docs/reports/`, marked historical or superseded |

Do not duplicate a durable rule, state, plan, classification, or decision. Link to its authority instead.
