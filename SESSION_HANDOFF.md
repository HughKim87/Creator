# Session Handoff

- Purpose: Preserve the single verified checkpoint after R-2A completion without relying on chat memory.
- Use when: Read after the boot kernel at every session start; resume only an explicitly user-approved next stage.
- Owner: The finishing project agent verifies and updates this file; the user controls every stage approval.
- Language: English.
- Location: Project root. Governed by [PROJECT_RULES.md](PROJECT_RULES.md), routed through [DOCUMENT_MAP.md](docs/agent/DOCUMENT_MAP.md), and executed through [WORKFLOW.md](docs/agent/WORKFLOW.md).

## Read order

1. Read [AGENTS.md](AGENTS.md) and the eight-rule [PROJECT_RULES.md](PROJECT_RULES.md).
2. Read this handoff as the only current-state source.
3. Read [DOCUMENT_MAP.md](docs/agent/DOCUMENT_MAP.md).
4. If the user approves R-2B, resolve a new structured task request through `tools/context/context_system.py` and read only the selected authorities and conditional rules.
5. Read the accepted [R-1.1 design](docs/reports/2026-07-20_R-1.1_지식_시스템_설계_보정.md) only for the exact R-2B boundary or later-stage provenance.

Do not load superseded reports, the final cross-validation report, or `backup/` by default. The closed session record remains historical evidence, not current state.

## Current goal and approval state

- R-2A is implemented and closed at structural plus automated validation level.
- R-2B is not authorized. Stop and wait for explicit user approval before migrating decisions, knowledge, cases, sources, or relations.
- No commit, push, publication, or external mutation was authorized or performed.

## Key terms

- Boot kernel: the eight always-loaded rule headings in `PROJECT_RULES.md`.
- Conditional rule: one stable JSON rule record inside a Markdown pack, selected by a verified predicate.
- File catalog: `catalog/files.jsonl`, the canonical project-governed file registry.
- Artifact unit: a deterministic addressable heading, JSON pointer, JSONL record, or whole-file fallback in `catalog/units.jsonl`.
- Work context: one immutable request resolution containing authority, read manifest, exclusions, and an optional write contract.

## Verified checkpoint

- Active governed files: 48; planned files: 0; orphan files: 0.
- Rules: 8 kernel plus 21 conditional records in 7 Markdown packs; all 29 source mappings are unique and complete.
- Minimum schemas: rule, file, unit, task request, work context, write contract, and event.
- Unit extraction: Markdown heading, JSON pointer, JSONL stable record ID, and explicit whole-file fallback.
- Resolver: exact file/unit, predicate rule selection, one-hop declared file dependencies, and explicit selected/excluded reasons.
- Writer: Markdown only, exact contract targets, before-file hashes, UTF-8/NUL/fence checks, catalog/unit/event write-back.
- Event evidence: 5 chained events through the live R-2A writer fixture.
- Automated tests: 6 passed. Integrated structural validator passed with protected-path pre-filter and local-link checks.

## Completed implementation

| Artifact | Status | Role |
|---|---|---|
| `PROJECT_RULES.md` | Active | Eight-rule boot kernel |
| `rules/*.md` | Active | Seven authoritative conditional-rule packs |
| `schemas/*.json` | Active | Seven minimum R-2A contracts |
| `catalog/bootstrap.json` | Retained evidence | Pre-migration 19-file and 29-rule mapping |
| `catalog/files.jsonl` | Canonical | Universal file registry with owners, conditions, validators, relations, strategies, and hashes |
| `catalog/rules.jsonl` | Derived | Rebuildable rule projection |
| `catalog/units.jsonl` | Derived | Rebuildable artifact-unit projection |
| `records/work/events.jsonl` | Canonical | Append-only R-2A event hash chain |
| `tools/context/context_system.py` | Active implementation | Bootstrap, sync, resolve, validate, plan, and Markdown write commands |
| `tests/context/test_context_system.py` | Active test | Six automated R-2A contract checks |
| `context/requests/r2a_read.json` and `context/work/r2a_read.json` | Retained fixture | Exact-heading read-only proof |
| `context/requests/r2a_write.json`, `context/work/r2a_write.json`, and `context/payloads/r2a_write.json` | Retained fixture | Contract-gated report, registry, and handoff write proof |
| `docs/reports/2026-07-20_R-2A_컨텍스트_시스템_구현_결과.md` | Retained evidence | Concise Korean R-2A delta and validation report |

## Validation state

- Structural: passed for UTF-8, NUL, JSON/JSONL parsing, schema-required fields, rule mapping, catalog/hash consistency, deterministic units, event chain, protected exclusions, local Markdown links, and `git diff --check`.
- Automated: six `unittest` checks passed, including contract rejection without mutation.
- Application-validated: not applicable to this local data/CLI thin slice and not claimed.
- User-approved: R-1.1 design and R-2A execution were approved; the R-2A content/result itself awaits the user's review.

## Failure ledger

| Objective | Attempt | Result or confirmed cause | Consecutive count | Next condition |
|---|---|---|---:|---|
| Execute Python checks | Attempt 1 | System `python` was absent from PATH; exact bundled runtime then compiled and ran successfully | 0 after success | Continue using the bundled executable path |
| Bootstrap catalog | Attempt 1 | Dotfile normalization removed the leading dot from `.gitattributes`; fixed and bootstrap succeeded | 0 after success | Retain dotfiles as governed project settings |
| Validate file/unit integrity | Attempt 1 | Non-ASCII report paths collided after ASCII normalization; path-hash suffix fixed IDs and validation passed | 0 after success | Keep file IDs stable and collision-free |

No active repeated failure reached the stop threshold.

## Active risks and exclusions

- The working tree contains the uncommitted R-2A implementation. Preserve unrelated state; do not commit unless explicitly requested.
- R-2A is a Markdown-centered thin slice. General code/config/test/binary writers and lifecycle recovery belong to R-3.
- The manual case and closed session record have catalog nodes and units but are not migrated into formal R-2B knowledge/source/relation schemas.
- SQLite, FTS5, vector retrieval, a graph database, and Obsidian remain excluded.
- Protected user data and `backup/` remain outside global traversal and registration.

## Next actions

1. Wait for the user to review the R-2A result.
2. If and only if the user explicitly approves R-2B, create a new task request and use the resolver to select the accepted R-2B design boundary.
3. The first R-2B implementation action is to migrate D-01 through D-17 as independent decision records with approval and source fields, then add existing knowledge, case, source, and relation records one kind at a time through the live loop.
4. Stop after the R-2B Korean result report and wait for R-3 approval.

## Backup and deduplication

No backup was created: project rules use version history and prohibit ad hoc duplicates; `backup/` is immutable. No `NEXT_SESSION_TASK.md` exists. This file remains the sole current checkpoint.

## Next-session start prompt

Read the boot kernel, this handoff, and the document map. R-2A is complete; do not rerun it or start R-2B without explicit user approval. If R-2B is approved, resolve a new bounded task request, migrate the accepted decisions and existing corpus one real record kind at a time, preserve protected exclusions, write the Korean R-2B result through the contract-gated loop, update this handoff, and stop before R-3.
