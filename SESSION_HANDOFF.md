# Session Handoff

- Purpose: Let the next agent resume from the verified current project state without relying on chat history.
- Scope: Current goal, approvals, completed work, verification, failures, blockers, and first next action only.
- Audience and language: Agents; English.
- Read when: Before continuing, changing, or verifying project work.
- Write when: Current state, approval gate, implementation, verification, failure count, blocker, or next action changes.
- Authority: This is the sole current-state source. Global rules, rebuild principles, layer plans, and user reports are linked rather than duplicated.

## Current state

- Date: 2026-07-19.
- Branch: `feature/refactoring_simple`, one commit ahead of its remote; the working tree contains uncommitted document and L2-L4 framework changes.
- Last user-created L0 commit: `c56226a`.
- Rebuild position: L0 through L4 are complete. L5 is not approved.
- Current request: Execute the plan through L4 and report the result.
- Current result: L3 minimum document profiles and L4 output-lifecycle schema version 2 passed 15 integrated synthetic tests and document-boundary checks.
- First unstarted rebuild work: L5 — Human-Readable Workflow Rules.
- Execution limit: Do not start L5 or map real user data without explicit approval and designation.

## Active document architecture

| Path | Purpose | Language | Status | Read condition |
|---|---|---|---|---|
| `AGENTS.md` | Minimum-read and write-back router | English | active | Start of workspace work |
| `PROJECT_RULES.md` | Project-wide rules that always apply | English | active, sole global-rule source | Always before workspace work |
| `SESSION_HANDOFF.md` | Current verified state and next action | English | active, sole state source | Continue/change/verify project work |
| `docs/REBUILD_PRINCIPLES.md` | Rebuild direction, limits, and stop conditions | English | active | Rebuild scope or exception decisions |
| `docs/REBUILD_PLAN.md` | Layer deliverables, verification, rollback, and gates | English | active, sole work-plan source | Approved rebuild work; current layer only |
| `docs/INHERITANCE_MAP.md` | Existing-asset adoption decisions | English | active, sole adoption source | Existing feature changes; relevant row only |
| `docs/FILE_DATA_CONTRACT.md` | Minimum video-task state, output lifecycle, and safe file I/O contract | English | active, sole L2-L4 state/lifecycle contract | Read/write/validate/migrate designated task state |
| `PROJECT_STATUS.md` | Korean user-facing current summary | Korean | active derivative, not an execution source | User review or milestone report |
| `PROJECT_STRUCTURE_ANALYSIS.md` | Korean structure-analysis snapshot | Korean | historical/supporting | Explicit historical or structure review |
| `docs/REBUILD_EXECUTION_REPORT.md` | Korean superseded first implementation report | Korean | historical/superseded | Explicit report review only |

Documents under `backup/` are read-only historical evidence. Their internal `active` labels reflect their
archived point in time and do not override this registry.

## Completed work

### L0

- Established one startup route and one source each for rules, state, plan, and inheritance decisions.
- Classified the first execution report as historical/superseded.
- Recorded and verified the initial nine-file tracked framework baseline.
- User committed the L0 result as `c56226a`.

### L1

- Added path ownership/read/write/Git/delete boundaries, original/derivative/temp separation, portable internal naming, and fail-closed reporting.
- Preserved the Korean project path and existing user filenames; only new internal identifiers use portable lowercase ASCII.
- Verified ignore behavior, trackability, text/binary attributes, and nine policy scenarios.
- L1 changes were not committed before the current documentation request.

### Document architecture reorganization

- Audited all seven active Markdown documents outside `backup/`, `inputs/`, and `outputs/`.
- Rewrote all agent execution sources in English.
- Kept user-facing analysis and report documents in Korean.
- Moved rebuild-only principles out of `PROJECT_RULES.md` into `docs/REBUILD_PRINCIPLES.md`.
- Reduced `docs/REBUILD_PLAN.md` to the ordered layer plan and moved current state back to this handoff.
- Reduced `docs/INHERITANCE_MAP.md` to asset decisions; L2 schema details remained in the plan until the contract was created.
- Added `PROJECT_STATUS.md` as a Korean derivative so user reporting does not turn agent state into a mixed-language second source.
- Added top-level purpose, scope, audience/language, read condition, write condition, and authority metadata to every active execution document.
- Added equivalent Korean purpose/scope metadata to every user-facing report.
- Did not read or modify user data or `backup/` during this reorganization.

### L2

- User approval to proceed was interpreted as L2 approval; a synthetic sample was selected because no real sample was designated.
- Added `docs/FILE_DATA_CONTRACT.md` as the sole schema and I/O contract for `outputs/<project_id>/state.json`.
- Added `tools/state_io.py` with strict version, field, identifier, fingerprint, source-reference, validation-level, and path-boundary checks.
- Writes use a same-directory temporary file, flush and sync it, and atomically replace the target; failed replacement preserves the prior state and removes the temporary file.
- Added eight standard-library unit tests using temporary directories and synthetic content only.
- Read only selected preserved state and serialization contracts; did not enumerate or modify user data.

### L3

- Added exact `resume_current_work`, `change_document_route`, and `handle_video_task_state` profiles to `AGENTS.md`.
- Added three routing regression tests; profile read sets, write targets, and explicit exclusions passed.
- Compared each profile with the seven-document active execution set after L4 integration. Resume selects three documents; document-route and video-state work select four.
- UTF-8 document context fell from 54,676 bytes to 19,826 bytes for resume and 29,769 bytes for the other profiles, a 64% and 46% reduction.
- Median cached local file-read time fell from 0.5271 ms to 0.2086-0.2829 ms, a 46-60% reduction. This measures file loading only, not model reasoning time.
- Unrelated document selections fell from four, three, and three to zero. No `docs/INDEX.md` or helper command was needed.

### L4

- Advanced `docs/FILE_DATA_CONTRACT.md` and `tools/state_io.py` from schema version 1 to explicit version 2; version 1 is rejected rather than guessed.
- Added output version, `current`/`superseded`/`failed` status, same-source lineage, SHA-256 integrity, reduced approval state, and explicit next-use eligibility.
- Limited each role to one current output and made `state.json` the sole current pointer; no second `CURRENT.json` was added.
- Added exact-file integrity validation without directory enumeration or real user-data access.
- Preserved existing filenames; new internal version filenames are only a preference when no consumer requires a fixed name.
- Synthetic lifecycle tests confirmed that superseded and failed files remain after current-state promotion and persistence.

## Verification state

| Target | Level | Result |
|---|---|---|
| L0 document structure | Structure-validated | Previously passed UTF-8/NUL, status labels, routing, links, and Git baseline. |
| L1 boundaries | Tool- and structure-validated | Ignore 4, trackable 1, text/binary attributes, and policy 9 scenarios passed. |
| Document architecture reorganization | Structure-validated | Nine active documents passed top metadata, language separation, routing, authority uniqueness, local links, UTF-8/NUL, and `git diff --check`. |
| L2 file-state contract | Tool-validated with synthetic data | Eight tests passed: round-trip, UTF-8 path, required/unknown/type checks, boundaries, identity matching, invalid JSON, and interrupted replacement preservation. |
| L3 document profiles | Tool- and structure-validated | Three routing tests passed; three measured profiles reduced document context 46-64% and selected zero unrelated documents. |
| L4 output lifecycle | Tool-validated with synthetic files | Twelve state tests passed, including missing path, source mismatch, current conflict, integrity mismatch, eligibility, and preserved superseded/failed files. |
| `backup/` | Git boundary | Unchanged. |
| User media and Premiere | Unverified | Outside the current request; no user sample or app validation. |

## Failure ledger

| Objective | Attempt/version | Result or cause | Consecutive count | Next condition |
|---|---|---|---:|---|
| Reproduce archived snapshot tests in the current environment | 1: bundled Python | `pytest` unavailable | 1 | Use another runtime |
| Same objective | 2: snapshot venv | Package import path missing | 2 | Set explicit `PYTHONPATH` |
| Same objective | 3: venv + `PYTHONPATH` | 113 passed, 14 failed, 33 errors; Git safe-directory and pytest temp permissions affected results | 3 | Do not retry until ownership/temp path changes or a clean clone is provided |
| Check legacy tests in the current environment | 1: 74 unittest cases | 72 passed, 2 failed from Git safe-directory behavior | 1 | Recheck only in a Git-safe environment |
| Locate `CODEX_` analysis documents | Filesystem and full Git-name history | No such filename; recovered by content, date, and snapshot path | 1 | Compare again only if the user provides another path |
| L1 integrated validation | 1 -> 2 | First check had a bad expected marker and one stale plan status; second check passed | 0, reset by confirmed success | Complete |
| Run L2 tests with the system `python` command | 1 -> 2 | The command was unavailable; the bundled Python 3.12.13 runtime then passed all eight tests | 0, reset by confirmed success | Use the bundled runtime in this environment |
| Inspect the L2 Git diff | 1 -> 2 | The default Git ownership check rejected the sandbox user; command-scoped `safe.directory` then passed without changing global settings | 0, reset by confirmed success | Keep the command-scoped setting in this environment |
| Run final L2 document checks | 1 -> 2 | The first pass found Markdown hard-break spaces in a historical report; equivalent blank-line formatting removed them and the full check passed | 0, reset by confirmed success | Complete |
| Run L3 routing regression tests | 1 -> 2 | The first test function used a hyphen and caused a Python syntax error; the snake-case name then passed all three tests | 0, reset by confirmed success | Complete |
| Measure L3 profile costs | 1 -> 2 -> 3 | The first PowerShell result pipeline did not parse; the second produced invalid rounded timings; the corrected median measurement passed | 0, reset by confirmed success | Complete |
| Fix the final contract path reference | 1 -> 2 | The first patch wrapper had a JavaScript string syntax error and made no change; the direct one-line patch succeeded | 0, reset by confirmed success | Complete |

## Active blockers and risks

- L5 is blocked only by missing user approval and workflow-rule decisions.
- `inputs/` and `outputs/` were not enumerated or read; real state mapping, real output integrity, and application behavior remain unverified.
- Schema version 1 has no mapped real user state. If such a file is later designated, it needs an explicit reviewed migration rather than automatic guessing.
- `PROJECT_STATUS.md` must remain a derivative. Agents must not use it instead of this handoff.
- Historical Korean reports contain point-in-time or superseded recommendations and must not be used for execution.
- Recovering legacy tools can also recover child-exit, ffprobe-default, non-atomic-write, and fail-open defects.

## First next action

1. Wait for explicit L5 approval.
2. If L5 is approved, read only the L5 section of `docs/REBUILD_PLAN.md` and the L5 rows selected from `docs/INHERITANCE_MAP.md`.
3. Do not read user media until the user designates an exact item and purpose.

## Resume prompt

```text
Read PROJECT_RULES.md and SESSION_HANDOFF.md.
Do not start L5 unless the user has explicitly approved it.
If L5 is approved, read only the L5 section of docs/REBUILD_PLAN.md and the selected L5 rows in docs/INHERITANCE_MAP.md.
```
