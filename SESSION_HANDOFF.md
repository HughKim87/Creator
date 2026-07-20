# Session Handoff

- Purpose: Preserve the single verified current checkpoint so a later agent can resume without chat memory.
- Use when: Read after startup rules at every session start; update after material work and before a stage report.
- Owner: The agent finishing the active stage verifies and updates this file; the user controls approval and next-stage scope.
- Language: English.
- Location: Project root. Read after [PROJECT_RULES.md](PROJECT_RULES.md); use [DOCUMENT_MAP.md](docs/agent/DOCUMENT_MAP.md) for further routing and link completed evidence rather than copying it.

## Read order

1. Follow [AGENTS.md](AGENTS.md) and read all applicable project rules completely.
2. Read this file for current state and the first unstarted action.
3. Open only the task-specific authorities selected through [DOCUMENT_MAP.md](docs/agent/DOCUMENT_MAP.md).

## Current goal and scope

- Goal: Rebuild a minimal active project foundation and then, only after separate approval, implement a local provenance-preserving knowledge and RAG system.
- Current stage: Command 3, project foundation implementation.
- Scope completed in this stage: root router, common rules, document ownership and language boundaries, common workflow, knowledge/retrieval/maintenance contracts, Korean user guide, report metadata reconciliation, and this handoff.
- Explicitly excluded: structured records, schemas, writers, SQLite, FTS5, context package generation, vectors, graph databases, Obsidian configuration, and migration of video-production functions.

## Key terms

- Active project: Files outside `backup/` that are governed by the root project rules.
- Historical source: Read-only material under `backup/`; never an active runtime dependency.
- Canonical file: Human-reviewable Markdown, JSONL, or future JSON Schema that owns a datum.
- Projection: A rebuildable index, view, summary, or context package; never source of truth.
- Stage 4-A: The first proposed knowledge implementation slice: separated record directories, schemas, templates, append-only event/history handling, and validators.

## Source inputs and decisions

- [Existing project analysis](docs/reports/2026-07-20_기존_프로젝트_분석.md) — active report, user-approved on 2026-07-20; historical evidence and migration classification.
- [Foundation and knowledge system design](docs/reports/2026-07-20_프로젝트_기반_및_지식_시스템_설계.md) — active report, user-approved on 2026-07-20; owns decisions D-01 through D-11 and phase boundaries.
- User instruction — `backup/` immutable; Korean user reports; English agent documents; separate fact/inference/decision with sources; stop for approval after each stage.
- User approval — “진행해” after the Command 2 report authorized Command 3 only.

## Resume checkpoint

- Last completed action: Created the Command 3 foundation documents and reconciled the two approved reports' stale “approval pending” metadata.
- Current verification point: Final structural and repository-scope validation passed for all 13 active foundation documents, including this handoff and the Command 3 report.
- First unstarted action: Report Command 3 in Korean and wait for explicit user approval.
- First implementation action after approval: Execute Stage 4-A only, beginning with exact schemas and separated canonical record types; do not create a search database yet.

## Implemented foundation

| Artifact | Status | Role |
|---|---|---|
| `AGENTS.md` | Active, implemented | Startup and document router |
| `PROJECT_RULES.md` | Active, implemented | Always-applicable policy only |
| `README.md` | Active, implemented | Korean user entrypoint |
| `SESSION_HANDOFF.md` | Active, implemented and structurally verified | Single current state source |
| `docs/agent/DOCUMENT_MAP.md` | Active, implemented | Document authority and placement map |
| `docs/agent/WORKFLOW.md` | Active, implemented | Common execution, validation, and closure procedure |
| `docs/agent/KNOWLEDGE_SYSTEM.md` | Active contract, implementation pending | Canonical categories, provenance, lifecycle, data flow |
| `docs/agent/CONTEXT_RETRIEVAL.md` | Active contract, implementation pending | Direct routing, future retrieval, context boundaries |
| `docs/agent/KNOWLEDGE_MAINTENANCE.md` | Active contract, implementation pending | Review, conflict, supersession, and refresh behavior |
| `docs/user/GUIDE.md` | Active, implemented | Korean operating and approval guide |
| `docs/reports/*.md` | Active point-in-time evidence | Korean analysis and design reports; not policy |

## Verification state

- Final document check: Passed for 13 active files with zero reported issues.
- Checks completed: strict UTF-8, NUL absence, trailing whitespace, balanced fenced blocks, required document metadata, Korean user-document presence, declared English agent-document language, required rule and handoff sections, approved report statuses, and local Markdown link resolution.
- Final link result: 148 Markdown links parsed: 128 local and 20 external. All local targets resolved; external URLs were counted but not network-revalidated in Command 3.
- Repository check: `backup/` has no Git status changes.
- Git state: New active foundation files are untracked; no commit or publication was requested or performed.
- Scope check: Stage 4 implementation paths and a duplicate current-state document are absent.
- Application or user content validation: Not applicable to this documentation-only stage.

## Failure ledger

| Objective | Attempt/version | Result or confirmed cause | Consecutive count | Next condition |
|---|---|---|---:|---|
| Inspect Git status | Initial Stage 3 diagnostic | Failed because the sandbox account did not match repository ownership; resolved by per-command read-only `-c safe.directory=<workspace>` | 0 after confirmed success | Keep using the scoped per-command override; do not change global Git config |
| Validate Stage 2 report links | Initial design-report check | Two historical source paths used incorrect filenames; corrected and all seven local links then resolved | 0 after confirmed success | Re-run link validation whenever reports or sources move |

No active repeated failure has reached a stop threshold.

## Active blockers and risks

- Blocker: Stage 4 is not authorized until the user approves the Command 3 report.
- Risk: Knowledge-system documents describe future contracts. Do not claim structured logging, RAG, SQLite search, automatic freshness review, or generated context packages are operational.
- Risk: Foundation files are not committed. Preserve them as user-owned workspace changes unless the user requests Git actions.
- Risk: `backup/` contains obsolete procedures with their own rule files. Read them for history and access safety only; the root active rules control new work.

## Backup and deduplication

- No backup file was created: `SESSION_HANDOFF.md` did not previously exist, `backup/` is immutable, and active project rules prohibit ad hoc duplicate backups in favor of version history.
- No `NEXT_SESSION_TASK.md` or second current-state document exists. This file is the sole current checkpoint.
- General rules and technical details are linked to their owners rather than duplicated here.

## Next actions

1. Report Command 3 completion in Korean and wait for explicit approval.
2. After approval, implement Stage 4-A only and report before Stage 4-B.

## Next-session start prompt

Read every applicable `PROJECT_RULES.md` as required by `AGENTS.md`, then read `SESSION_HANDOFF.md`. Confirm whether the user approved the Command 3 foundation report. If approval is absent, do not implement Stage 4. If approval is present, read the approved design and knowledge contracts, execute Stage 4-A only, verify source traceability and protected-path exclusion, update this handoff, report in Korean, and stop for approval.
