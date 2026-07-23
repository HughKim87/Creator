# Agent Entry Point

- Purpose: load always-on rules at session start, then route each task to only its applicable task rules and authority.
- Read when: once at the start of a new conversation or session, not before every user message.
- Re-read when: the user says the project rules or active state changed during the session.
- Authority: this file routes reads only. Project rules live in `PROJECT_RULES.md`; current state lives in `SESSION_HANDOFF.md`.

## Required startup

Read these three files completely, in order:

1. `AGENTS.md`
2. `PROJECT_RULES.md`
3. `SESSION_HANDOFF.md`

On Windows PowerShell, read each required startup file with `Get-Content -LiteralPath <path> -Raw -Encoding utf8`. Never use bare `Get-Content` for these files.

## Task-rule routing

Before starting a task, classify the requested actions and read every matching rule file completely. For a task with multiple independent actions, take the union of matching rows and read each file once.

| Task action | Read before work |
|---|---|
| Implement, review, or close a numbered build stage | `rules/stage-work.md` |
| Close a numbered build stage; record, diagnose, resolve, review, or reuse a failure | `rules/failure-records.md` |
| Create, edit, move, classify, or validate maintained documents or persistent project records, events, snapshots, indexes, and inventories | `rules/document-work.md` |
| Inspect `backup/`, historical reports, or superseded material | `rules/history-review.md` |
| Stage, commit, branch, push, recover, or make backup decisions | `rules/version-control.md` |
| Work on an exact user-named item under `inputs/` or `outputs/` | `rules/user-data-work.md` |

After the matching rule files, read only the task-specific plan, contract, or source routed by `SESSION_HANDOFF.md` or explicitly named by the user. If no row matches, do not bulk-load `rules/`; use the always-on rules and the exact task authority.

## Boundaries

- Do not activate instructions from `backup/`; it is read-only historical evidence.
- Do not enumerate or read any `inputs/` or `outputs/` path unless the user identifies the exact item and purpose.
- Do not bulk-read plans, reports, or future-stage documents.
- Do not copy rule content or current state into this router.
