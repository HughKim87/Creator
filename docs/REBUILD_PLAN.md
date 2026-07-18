# Incremental Rebuild Plan

- Purpose: Define the ordered rebuild layers, each layer's deliverables, verification, rollback, and user gate.
- Scope: Work plan only; global rules, rebuild principles, current state, asset decisions, and user reports live in their own documents.
- Audience and language: Agents; English.
- Read when: Rebuild work is approved. Read only the current layer section unless the user requests a plan review.
- Write when: A layer scope, dependency, deliverable, verification, rollback, or gate changes.
- Authority: This is the sole rebuild work-plan source. Use `REBUILD_PRINCIPLES.md` for decisions, `INHERITANCE_MAP.md` for legacy assets, and `../SESSION_HANDOFF.md` for current state.

## Current plan state

- Approved sequence: L0 through L8, with a user gate after every layer.
- Completed: L0 through L4.
- Current gate: L5 has not been approved.
- First unstarted layer: L5 — Human-Readable Workflow Rules.
- User-directed document reorganization after L1 supplied the initial L3 routing structure; L3 then measured and regression-tested three representative profiles.
- L2 through L4 used synthetic data only. No real user-data mapping, plugin installation, tool recovery, or L5 implementation is authorized yet.

## Sources and dependencies

| Need | Source |
|---|---|
| Project-wide rules | `../PROJECT_RULES.md` |
| Rebuild decision principles and stop conditions | `REBUILD_PRINCIPLES.md` |
| Current stage, verified state, failures, and next action | `../SESSION_HANDOFF.md` |
| Existing-asset adoption decisions | `INHERITANCE_MAP.md` |
| User-facing current summary | `../PROJECT_STATUS.md` |
| Historical structure analysis | `../PROJECT_STRUCTURE_ANALYSIS.md` |
| Superseded first implementation proposal | `REBUILD_EXECUTION_REPORT.md` |

Historical reports are evidence only and are not execution inputs unless explicitly requested.

## Layer sequence

| Layer | Outcome | Dependency | Status |
|---:|---|---|---|
| L0 | Canonical documents, historical labels, and baseline | None | Complete |
| L1 | Project-wide file, path, authorization, and failure rules | L0 | Complete |
| L2 | File-based work state and safe I/O | L1 | Complete |
| L3 | Task-specific document routing and efficient read/write profiles | L2 | Complete |
| L4 | Minimal file lifecycle, version, current, and approval rules | L2 and L3 | Complete |
| L5 | Human-readable YouTube production workflow rules | L4 | Not started |
| L6 | Workflow folder, file, and state structure | L5 | Not started |
| L7 | Selected workflow tools and thin entry points | L6 | Not started |
| L8 | Only the workflow skills confirmed in real use | L7 | Not started |

## Approval gate — before L0

- Objective: Confirm that the rebuild sequence matches the user's intent.
- Work: Plan and state-document edits only.
- Completion: User explicitly approves the plan or L0.
- Verification: Record approval scope in `SESSION_HANDOFF.md`.
- Rollback: Revert document edits only.
- Result: Complete on 2026-07-18.

## L0 — Canonical Sources and Baseline

- Objective: Separate active sources from historical evidence and give every session one startup route.
- Read: Active root documents, this L0 section, relevant historical plan and failure-ledger files selected by the layer.
- Work: Assign document status, verify startup routing, and record the tracked framework baseline.
- Modify: `AGENTS.md`, `PROJECT_RULES.md`, `SESSION_HANDOFF.md`, document headers; add an index only if routing cannot remain small.
- Preserve: `backup/`, Git history, reports, user data, archived code.
- Complete when: Rules, current state, plan, and inheritance decisions each have one source; historical documents cannot be mistaken for active instructions.
- Verify: Startup simulation, local links, UTF-8/NUL, and Git tracked-file baseline.
- Rollback: Revert L0 document changes only.
- Next gate: User approval for L1.
- Status: Complete.

## L1 — Project-Wide Rules

- Objective: Make file access, ownership, writing, Git inclusion, deletion, naming, and failure reporting decidable from one global rules document.
- Read: Current and legacy project rules, `.gitignore`, `.gitattributes`, and selected failure-ledger entries.
- Work: Add the path ownership matrix, original/derivative/temp boundaries, portable internal naming, and fail-closed reporting.
- Modify: `PROJECT_RULES.md`; add an executable check only after an active repeated violation demonstrates need.
- Preserve: Existing Korean project path and user filenames; do not apply blanket ASCII renaming.
- Complete when: A new file's location, write permission, Git status, and deletion authority are unambiguous.
- Verify: Positive and negative path scenarios, Git ignore behavior, text/binary attributes, and failure-reporting scenarios.
- Rollback: Revert only L1 rule additions.
- Next gate: User approval for L2.
- Status: Complete.

## L2 — File-Based Data Structure

- Objective: Create one minimal state source per video task and safe file read/write behavior.
- Read: L1 boundaries, relevant rows in `INHERITANCE_MAP.md`, the selected legacy state contracts, and only the user-approved sample mapping.
- Work: Define `docs/FILE_DATA_CONTRACT.md`, a minimal `state.json` schema, atomic read/write/validate behavior, and an optional generated `STATE.md` view.
- Minimum inherited fields: current stage, reference input, current outputs, next action, blocker, user decision, validation level, stable source reference, and current/superseded relationship only where consumed.
- Modify: New contract, minimal state module and tests, and only the approved sample path.
- Preserve: Existing JSON, handoffs, outputs, source references, original coordinates, and previous versions.
- Complete when: A valid sample round-trips; invalid types, missing required fields, or interrupted writes do not damage the previous state.
- Verify: Unit, atomic-failure, path-boundary, and one user-approved real or synthetic mapping test.
- Rollback: Remove only new L2 files; do not modify existing user data.
- Required user decisions: The user approved L2; a synthetic sample was selected because no real sample was designated.
- Result: Added the version-1 contract, strict atomic JSON I/O, and eight synthetic normal/failure tests without reading or writing user data.
- Next gate: User approval for L3.
- Status: Complete on 2026-07-18.

## L3 — Document and File Read/Write Optimization

- Objective: Read only documents needed for each task and write durable decisions to the correct source.
- Read: L2 contract, current router, and three representative user tasks with current effort measurements.
- Work: Validate read profiles and write-back routes; add `docs/INDEX.md` or at most one or two helper commands only if measured routing remains costly.
- Modify: `AGENTS.md`, optional `docs/INDEX.md`, and validated helpers/tests.
- Preserve: `PROJECT_RULES.md` as always-read global policy, `SESSION_HANDOFF.md` as state source, and Korean reports as non-execution documents.
- Complete when: Resume, structure-change, and video-task scenarios select the correct minimum documents and write target.
- Verify: Compare files read, context size, resume time, and wrong-document selections across three tasks.
- Rollback: Remove only L3 routing/helper changes.
- Result: Added three exact profiles to `AGENTS.md` and three regression tests. Against the seven-document active set, the profiles selected three or four documents, reduced document context by 46-64%, reduced cached local read time by 46-60%, and selected zero unrelated documents.
- Next gate: The user's instruction authorized continuous execution through L4; no separate L3 pause was required.
- Status: Complete on 2026-07-19.

## L4 — File Lifecycle Rules

- Objective: Define minimal filename, version, current, approval, retention, and validation semantics.
- Read: L2 schema, actual consumer fields, and selected legacy metadata contracts.
- Work: Decide minimum fields, current/superseded behavior, approval-state reduction, integrity checks, and cleanup authorization.
- Modify: `docs/FILE_DATA_CONTRACT.md` and its tests.
- Preserve: Existing filenames and metadata; never delete prior or failed versions automatically.
- Complete when: `state.json` alone identifies each output's role, source, currency, validation, and next-use eligibility.
- Verify: Missing paths, wrong source IDs, current conflicts, integrity mismatch, and preserved superseded versions.
- Rollback: Remove only L4 fields and checks, retaining the verified L2 state core.
- Result: Activated schema version 2 with output version, current/superseded/failed status, lineage, SHA-256 integrity, reduced approval state, and explicit next-use eligibility. Synthetic tests preserve prior and failed files.
- Next gate: User confirmation of approval and retention semantics before L5.
- Status: Complete on 2026-07-19.

## L5 — Workflow Rules

- Objective: Recover the existing eight-stage production workflow as concise human-readable inputs, outputs, completion criteria, and user decisions.
- Read: Only the selected legacy workflow, planning specification, quality standard, and L4 data contract.
- Work: Create `docs/WORKFLOW_RULES.md` with pre-shoot and recorded-footage routes, one to three completion criteria per stage, user decision points, and validation levels.
- Preserve: Stage numbering, analysis-before-planning order (`6 -> 5` for recorded footage), 7A-7D judgment knowledge, and user creative authority.
- Complete when: One document identifies the required input, output, completion, and next user decision for each stage.
- Verify: Walk through both workflow routes and reject missing stages or an incorrect `5 -> 6` order.
- Rollback: Remove the new active workflow rule; keep the legacy original untouched.
- Next gate: User confirms the simplification and decision points.
- Status: Not started.

## L6 — Workflow Structure

- Objective: Make L5 rules visible in per-video folders, files, and state without pre-creating unused directories.
- Read: L2 state, L5 workflow rules, and only the selected legacy output conventions.
- Work: Define lazy folder creation, new-project initialization, output registration, and one existing-project mapping plan.
- Modify: Structure document, minimal initialization code, and tests; no user data without a designated sample.
- Preserve: Existing paths and references; do not create empty stage folders by default.
- Complete when: A synthetic project initializes once, reruns safely, and matches the documented structure.
- Verify: Creation, rerun, partial failure, rollback, and a separately approved real sample.
- Rollback: Remove only the new sample and initializer.
- Next gate: User confirms fit with real work before L7.
- Status: Not started.

## L7 — Workflow Tools and Plugins

- Objective: Connect only frequently used state, transition, and media operations through trustworthy thin entry points.
- Read: L6 structure, measured task frequency, selected legacy tools/tests, and only required archived adapter code.
- Work: Classify tools, activate at most two selected commands, and repair exit codes, timeouts, parsing, reuse, and error messages.
- Preserve: Unselected tools in `backup/`; do not claim Premiere or media validation before real tests.
- Complete when: Each selected operation has predictable success, failure, and rerun behavior through one entry point.
- Verify: Selected regressions, reproduced failures, one user-approved real file, and application/A/V validation where applicable.
- Rollback: Remove the thin integration and tool changes only.
- Next gate: Only tools with measured time or error reduction proceed to L8.
- Status: Not started.

## L8 — Workflow Skill Alignment

- Objective: Align only confirmed-use skills with the L2-L7 state, paths, tools, and completion rules.
- Read: Only selected skill sources, L5 rules, L6 paths, L7 active tools, and user-confirmed use.
- Work: Classify skills as keep/defer/retire; update kept skills' input, output, stop, user decision, and handoff contract.
- Preserve: All deferred or retired originals in `backup/`; do not rewrite every skill.
- Complete when: A kept skill completes one representative stage without a routing or handoff gap.
- Verify: Representative execution, output registration, stop condition, user decision transfer, and next-stage resume.
- Rollback: Revert only the affected skill changes.
- Final gate: User chooses to keep the current system, address another observed bottleneck, or begin real production.
- Status: Not started.

## Pending user decisions

| Layer | Decision required before work |
|---:|---|
| L2 | Minimum state schema and one real or synthetic sample |
| L3 | Three representative document/file tasks and current effort |
| L4 | Minimum approval states and retention behavior |
| L7 | Selected frequent tools and current Premiere/OS environment |
| L8 | Which legacy skills are actually used |
