# Agent Entry Router

- Purpose: Route agents to the minimum project documents required for the current task.
- Scope: Document selection and write-back routing only; this file contains no project policy or task state.
- Audience and language: Agents; English.
- Read when: At the start of any task that reads or changes this workspace.
- Write when: Only when document roles or routing rules change.
- Authority: `PROJECT_RULES.md` is the sole source of project-wide rules; `SESSION_HANDOFF.md` is the sole source of current state.

## Required startup

1. Read `PROJECT_RULES.md` completely.
2. Read `SESSION_HANDOFF.md` when continuing, changing, or verifying project work.
3. Read only the additional documents selected by the routing table below.
4. Do not bulk-read `docs/`, `backup/`, `inputs/`, or `outputs/`.

## Task routing

| Task | Read in addition to startup | Do not read by default |
|---|---|---|
| Resume or report current work | No additional document | Plans, analyses, and backup files |
| Execute a rebuild layer | Only the current layer in `docs/REBUILD_PLAN.md` | Other layers and historical reports |
| Read, write, validate, or migrate video-task state | `docs/FILE_DATA_CONTRACT.md` and only the designated task state | Other task directories and legacy state contracts |
| Change rebuild direction, scope, or exceptions | Relevant section of `docs/REBUILD_PRINCIPLES.md` and the affected plan section | Unrelated plan sections |
| Add, replace, remove, or recover an existing asset | Relevant row in `docs/INHERITANCE_MAP.md`, then only the source files named by that row | Unlisted backup files |
| Change document architecture | Affected active documents only | Historical reports unless a conflict must be checked |
| Investigate project history or structure | The specifically requested Korean report | Other reports and execution plans |
| Work on user data | Only the exact `inputs/` or `outputs/` item and purpose named by the user | Directory-wide enumeration or unrelated data |

`PROJECT_STRUCTURE_ANALYSIS.md`, `PROJECT_STATUS.md`, and
`docs/REBUILD_EXECUTION_REPORT.md` are user-facing reports. They are not execution inputs unless the user
explicitly requests analysis of those reports.

## Validated representative profiles

These L3 profiles make the minimum read and write sets explicit. `AGENTS.md` is the router in every profile.
Do not merge profiles automatically; add another document only when a separate part of the request triggers
its row in the task-routing table.

| Profile | Representative request | Complete read set | Allowed write set | Explicit exclusions |
|---|---|---|---|---|
| `resume_current_work` | Report the current stage and next action | `AGENTS.md`, `PROJECT_RULES.md`, `SESSION_HANDOFF.md` | None for reporting; `SESSION_HANDOFF.md` only if verified state changes | Plans, contracts, inheritance sources, backup files, and Korean reports |
| `change_document_route` | Change which active documents a task reads or updates | `AGENTS.md`, `PROJECT_RULES.md`, `SESSION_HANDOFF.md`, and only the affected active documents | `AGENTS.md` and only affected authority documents; `SESSION_HANDOFF.md` if current state changes | Historical reports, unrelated active documents, user data, and backup files |
| `handle_video_task_state` | Read, validate, or save one designated task state | `AGENTS.md`, `PROJECT_RULES.md`, `SESSION_HANDOFF.md`, `docs/FILE_DATA_CONTRACT.md`, and the exact designated `state.json` | The designated task state; the contract only for an approved schema change; handoff only for project-state changes | Other task directories, rebuild plans, inheritance sources, backup files, and Korean reports |

Profile completion checks:

- `resume_current_work`: Report only facts present in `SESSION_HANDOFF.md`; make no project changes.
- `change_document_route`: Each durable fact has one authority and every affected route resolves to it.
- `handle_video_task_state`: Contract validation passes for the exact state; no sibling task is enumerated.

## Write-back routing

| Information changed | Write to |
|---|---|
| Project-wide rule that always applies | `PROJECT_RULES.md` |
| Current stage, verified state, blocker, failure, or next action | `SESSION_HANDOFF.md` |
| Rebuild decision principle or stop condition | `docs/REBUILD_PRINCIPLES.md` |
| Layer scope, deliverable, verification, rollback, or gate | `docs/REBUILD_PLAN.md` |
| File-based video-task state schema or I/O behavior | `docs/FILE_DATA_CONTRACT.md` |
| Existing-asset adoption decision | `docs/INHERITANCE_MAP.md` |
| User-facing current summary | `PROJECT_STATUS.md` |
| Historical analysis result | The relevant Korean report, clearly marked historical or supporting |

Do not copy the same rule or state into multiple authoritative documents. Link to the source instead.
