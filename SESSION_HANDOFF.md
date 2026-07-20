# Session Handoff

- Purpose: Preserve the single verified checkpoint after R-2B completion without relying on chat memory.
- Use when: Read after the boot kernel at every session start; resume only an explicitly user-approved next stage.
- Owner: The finishing project agent verifies and updates this file; the user controls every stage approval.
- Language: English.
- Location: Project root. Governed by [PROJECT_RULES.md](PROJECT_RULES.md), routed through [DOCUMENT_MAP.md](docs/agent/DOCUMENT_MAP.md), and executed through [WORKFLOW.md](docs/agent/WORKFLOW.md).

## Read order

1. Read [AGENTS.md](AGENTS.md) and every applicable `PROJECT_RULES.md`, with the root eight-rule kernel controlling this project.
2. Read this handoff as the only current-state source.
3. Read [DOCUMENT_MAP.md](docs/agent/DOCUMENT_MAP.md).
4. If the user approves R-3, resolve a new task request and read only the exact R-3 boundary from the accepted [R-1.1 design](docs/reports/2026-07-20_R-1.1_지식_시스템_설계_보정.md).
5. Use the [R-2B result](docs/reports/2026-07-21_R-2B_기존_지식_코퍼스_이관_결과.md) only for an exact implementation audit.

Do not load superseded reports, `reports/history/`, the final cross-validation report, or `backup/` by default. Historical records are evidence, never current instructions.

## Current goal and approval state

- R-2A and R-2B are implemented and closed at structural plus automated validation level.
- R-3 is not authorized. Stop and wait for explicit user approval before generalizing writers or record lifecycle/recovery behavior.
- No commit, push, publication, or external mutation was authorized or performed.

## Key terms

- Corpus record: A schema-backed decision, knowledge item, case, source, or relation with a stable ID.
- Record projection: `catalog/records.jsonl`, rebuilt from canonical decisions, knowledge items, and case JSON blocks; it is not authority.
- Source trace: A registered source ID plus an exact path, Git object, official URL, or historical locator.
- Active relation: A verified, retrieval-eligible typed edge expanded at most one hop. A pending candidate is never active context.
- Historical candidate: Evidence that may appear through an exact trace but cannot become an active instruction.

## Source inputs and resume checkpoint

- Accepted scope source: `docs/reports/2026-07-20_R-1.1_지식_시스템_설계_보정.md` §10.2, §11, and §12.2.
- Implementation evidence: `docs/reports/2026-07-21_R-2B_기존_지식_코퍼스_이관_결과.md`, the canonical `knowledge/` stores, and the two R-2B work contexts.
- Current checkpoint: R-2B is closed; no implementation task is in progress. The first unstarted action is to create an exact R-3 request only after explicit user approval.
- Blocker: R-3 authorization is absent. This is an approval boundary, not an implementation failure.

## Verified checkpoint

- Rules: 8 kernel plus 21 conditional records in 7 Markdown packs; historical sources selected as active instructions: 0.
- Corpus: 17 accepted decisions, 4 verified knowledge items, 1 resolved case, 7 sources, and 6 typed relations.
- Decision gate: D-01 through D-17 each have an independent ID, accepted status, rationale, approval actor/date/evidence, and source locator.
- Provenance gate: verified knowledge traces to registered local or official sources; local document source hashes are validated.
- Case gate: `case.project.document-authority-duplication` separates confirmed symptom evidence from resolved solution evidence.
- Retrieval gate: two R-2B exact-record fixtures pass with verified one-hop relations and source manifests.
- Automated tests: 10 passed. Integrated validation passes with orphan files 0.

## Completed R-2B artifacts

| Artifact | Status | Role |
|---|---|---|
| `schemas/{decision,knowledge,case,source,relation}.schema.json` | Active contracts | Minimum R-2B record contracts |
| `knowledge/decisions.jsonl` | Canonical | D-01 through D-17 independent records |
| `knowledge/items.jsonl` | Canonical | Four verified reusable knowledge records |
| `knowledge/cases/case.project.document-authority-duplication.md` | Canonical | Existing stable case plus formal JSON record |
| `knowledge/sources.jsonl` | Canonical | Project document, Git, official URL, and historical-candidate sources |
| `knowledge/relations.jsonl` | Canonical | Five active verified edges plus one inactive candidate |
| `catalog/records.jsonl` | Derived | Rebuildable decision, knowledge, and case projection |
| `context/*/r2b_decision_evidence.json` | Retained fixture | Accepted decision to knowledge to source trace |
| `context/*/r2b_case_resolution.json` | Retained fixture | Confirmed symptom and resolved solution trace |
| `docs/reports/2026-07-21_R-2B_기존_지식_코퍼스_이관_결과.md` | Retained evidence | Korean R-2B delta and validation report |

R-2A artifacts remain active and were regression-tested; they are not duplicated here.

## Validation state

- Structural: passed for UTF-8, NUL, JSON/JSONL parsing, required record fields, rule mapping, catalogs, deterministic units, event chain, source hashes, relation endpoints, protected exclusions, and local links.
- Automated: 10 `unittest` checks passed, including both R-2B corpus fixtures and inactive-candidate gating.
- Application-validated: not applicable to this local data/CLI stage and not claimed.
- User-approved: R-2B execution was explicitly approved; the completed result now awaits user review.

## Failure ledger

| Objective | Attempt | Result or confirmed cause | Consecutive count | Next condition |
|---|---|---|---:|---|
| Parse Markdown units | Attempt 1 | Headings inside fenced examples were treated as real units; fence-aware scanning fixed the parser and validation passed | 0 after success | Keep regression coverage for fenced headings |
| Resolve R-2B start context | Attempt 1 | CP949 stdout could not print an em dash after artifacts were written; UTF-8 stdout fixed CLI reporting and validation passed | 0 after success | Keep CLI output UTF-8 |
| Validate decision approval | Attempt 1 | Validator over-required an invented approval state; aligned the contract to actor/date/source/locator and all 17 passed | 0 after success | Do not add lifecycle fields without an approved requirement |
| Audit knowledge metadata | Attempt 1 | Final contract comparison found missing language/time/author/scope/check/revision fields; schema and all four records were completed and revalidated | 0 after success | Compare canonical records with the full owning contract before closure |

No active repeated failure reached the stop threshold.

## Active risks and exclusions

- The working tree contains uncommitted R-2A/R-2B work plus user-provided history reports. Preserve all unrelated and concurrent state; do not commit unless explicitly requested.
- The writer remains Markdown-only. General code/config/test/binary writers and lifecycle recovery belong to R-3.
- Automated stale transitions, review queues, revision-history writers, and relation maintenance commands remain unimplemented.
- SQLite FTS5, vector retrieval, a graph database, and Obsidian remain excluded.
- Protected user data and `backup/` remain outside global traversal and registration.
- `reports/history/` is registered as point-in-time evidence but stays out of startup/default context and active instruction selection.

## Next actions

1. Wait for the user to review the R-2B result.
2. If and only if the user explicitly approves R-3, create a new bounded request for the R-3 section of R-1.1.
3. R-3 may generalize registered file writers and lifecycle/failure recovery; do not pull R-4 search-index work forward.
4. Stop after the approved R-3 boundary and report before any later stage.

## Backup and deduplication

No backup was created: project rules use version history and prohibit ad hoc duplicates; `backup/` is immutable. No `NEXT_SESSION_TASK.md` exists. This file remains the sole current checkpoint.

## Next-session start prompt

Read the boot kernel, this handoff, and the document map. R-2A and R-2B are complete; do not rerun them or start R-3 without explicit user approval. If R-3 is approved, resolve the exact R-3 boundary, preserve the canonical corpus and protected exclusions, verify failure recovery without adding R-4 search infrastructure, update this handoff through a valid write contract, and stop at the next approval boundary.
