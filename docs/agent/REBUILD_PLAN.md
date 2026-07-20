# Incremental Rebuild Plan

- Purpose: Define the ordered rebuild layers, each layer's deliverables, verification, rollback, and user gate.
- Scope: Work plan only; global rules, rebuild principles, current state, asset decisions, and user reports live in their own documents.
- Audience and language: Agents; English.
- Read when: Rebuild work is approved. Read only the current layer section unless the user requests a plan review.
- Write when: A layer scope, dependency, deliverable, verification, rollback, or gate changes.
- Authority: This is the sole rebuild work-plan source. Use `docs/agent/REBUILD_PRINCIPLES.md` for decisions, `docs/agent/RECONSTRUCTION_MAP.md` for capability ownership, and `SESSION_HANDOFF.md` for current state.

## Current plan state

- Approved sequence: L0 through L8, with a user gate after every layer; the plan now inserts an L3.1
  knowledge-navigation refinement before L5.
- Completed: L0 through L4.
- Current gate: The user cancelled Graphify adoption after the semantic path failed the token-and-accuracy comparison and the promoted typed path was found not to call Graphify.
- Active layer: L3.1 complete and rolled back — direct `AGENTS.md` routing and the independent Obsidian client remain active; Graphify navigation is excluded.
- L5 remains unapproved and requires a separate user gate.
- User-directed document reorganization after L1 supplied the initial L3 routing structure; L3 then measured and regression-tested three representative profiles.
- The post-L4 supplement separated agent, user, and report documents; added a document registry and governance checks; and hardened schema, input identity, output promotion, validation scope, and approval scope.
- Required migration-source knowledge has been reconstructed into active workflow, editing-quality, tool, and skill requirement documents. Active execution must not depend on the temporary migration archive.
- The later document-node analysis justified a bounded navigation evaluation. Its durable document classification,
  naming, split/merge, and direct index rules remain; the Graphify-specific implementation was removed after failure.
- L2 through L4 and navigation verification used framework documents and synthetic exact-item paths only. No real
  user-data mapping or L5 implementation is authorized.

## Backup independence rule

`backup/` is a temporary migration input and will be retired after the rebuild. It is not a permanent evidence
store, active authority, runtime dependency, or normal agent read path.

The following requirements apply to every layer:

1. Before a retained behavior is used, reconstruct it in an active document, implementation, or test and
   register its destination in `docs/agent/RECONSTRUCTION_MAP.md`.
2. Link active documents only to active project authorities. Do not link instructions, plans, commands, code,
   or tests back to `backup/` for normal execution.
3. A layer is incomplete while any required rule, contract, example, algorithm, or validation behavior exists
   only in `backup/`.
4. Verify the layer with archive access unavailable in principle: its documented read set, implementation,
   tests, and user handoff must resolve entirely through active paths.
5. Intentionally omitted behavior must be marked `deferred` or `excluded` with a reconsideration condition or
   reason; omission must not be hidden behind an archive reference.
6. Do not delete `backup/` during a rebuild layer. After L8, run the archive-retirement gate below and obtain a
   separate explicit user request before deletion.

## Sources and dependencies

| Need | Source |
|---|---|
| Project-wide rules | `PROJECT_RULES.md` |
| Rebuild decision principles and stop conditions | `docs/agent/REBUILD_PRINCIPLES.md` |
| Current stage, verified state, failures, and next action | `SESSION_HANDOFF.md` |
| Capability reconstruction decisions | `docs/agent/RECONSTRUCTION_MAP.md` |
| Workflow routes and planning requirements | `docs/agent/WORKFLOW_FOUNDATION.md` |
| Editing-quality requirements | `docs/agent/EDITING_QUALITY_RULES.md` |
| Reusable tool requirements | `docs/agent/TOOL_REQUIREMENTS.md` |
| Workflow skill requirements | `docs/agent/SKILL_REQUIREMENTS.md` |
| User-facing current summary | `docs/user/PROJECT_STATUS.md` |
| Historical structure analysis | `docs/reports/PROJECT_STRUCTURE_ANALYSIS.md` |
| Superseded first implementation proposal | `docs/reports/REBUILD_EXECUTION_REPORT.md` |
| Document-node optimization evidence | `docs/reports/2026-07-19_문서_노드_구조_개선_분석.md` |
| Obsidian and navigation-pilot evidence | `docs/reports/2026-07-19_옵시디언_도입_타당성_분석.md` |
| Graphify cancellation and failure analysis | `docs/reports/2026-07-20_그래피파이_도입_실패_분석.md` |

Historical reports are evidence only and are not execution inputs unless explicitly requested.

## Document-navigation integration contract

This contract applies to L3.1 and to document-navigation work declared in L5-L8.

1. Existing active Markdown files remain the only document content sources of truth. Obsidian is a local review
   client and does not select agent read scope.
2. Task-time authority selection uses the stable route table in `AGENTS.md` directly. The document registry
   classifies documents but relationships and nearby files never expand a route automatically.
3. Resolve every affected, named, or designated selector before opening a document. On ambiguity, a missing
   selector, or a protected-path conflict, stop the unresolved part and report it instead of guessing.
4. Open the original Markdown scope in Obsidian without moving or duplicating files. Standard Markdown links and
   stable headings must remain usable without Obsidian.
5. Never enumerate, copy, or expose `inputs/`, `outputs/`, `backup/`, `.git/`, `.agents/`, or `.codex/` without the
   exact user-named item, purpose, and applicable authorization.
6. Graphify and its compatible-format helper are excluded from active routing. Reopening them requires a separate
   user decision and the evidence conditions in the cancellation report.
7. Community plugins, Obsidian Sync or Publish, automatic hooks, MCP, shared servers, and generated work-memory or
   reflection files require their own measured need and explicit approval.

## Layer sequence

| Layer | Outcome | Dependency | Status |
|---:|---|---|---|
| L0 | Canonical documents, historical labels, and baseline | None | Complete |
| L1 | Project-wide file, path, authorization, and failure rules | L0 | Complete |
| L2 | File-based work state and safe I/O | L1 | Complete |
| L3 | Task-specific document routing and efficient read/write profiles | L2 | Complete |
| L4 | Minimal file lifecycle, version, current, and approval rules | L2 and L3 | Complete |
| L3.1 | Obsidian baseline, Graphify evaluation, and direct-route rollback | L3 and L4 | Complete; Obsidian retained, Graphify excluded |
| L5 | Human-readable YouTube production workflow rules | L3.1 and L4 | Not started |
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
- Preserve: Migration sources, Git history, reports, and user data during reconstruction.
- Complete when: Rules, current state, plan, and reconstruction decisions each have one active source; historical documents cannot be mistaken for active instructions.
- Verify: Startup simulation, local links, UTF-8/NUL, and Git tracked-file baseline.
- Rollback: Revert L0 document changes only.
- Next gate: User approval for L1.
- Status: Complete.

## L1 — Project-Wide Rules

- Objective: Make file access, ownership, writing, Git inclusion, deletion, naming, and failure reporting decidable from one global rules document.
- Read: Current project rules, `.gitignore`, `.gitattributes`, and active reconstruction decisions.
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
- Read: L1 boundaries, relevant rows in `docs/agent/RECONSTRUCTION_MAP.md`, active state requirements, and only the user-approved sample mapping.
- Work: Define `docs/agent/FILE_DATA_CONTRACT.md`, a minimal `state.json` schema, atomic read/write/validate behavior, and an optional generated `STATE.md` view.
- Minimum inherited fields: current stage, reference input, current outputs, next action, blocker, user decision, validation level, stable source reference, and current/superseded relationship only where consumed.
- Modify: New contract, minimal state module and tests, and only the approved sample path.
- Preserve: Existing JSON, handoffs, outputs, source references, original coordinates, and previous versions.
- Complete when: A valid sample round-trips; invalid types, missing required fields, or interrupted writes do not damage the previous state; the state contract and implementation require no migration source.
- Verify: Unit, atomic-failure, path-boundary, and one user-approved real or synthetic mapping test.
- Rollback: Remove only new L2 files; do not modify existing user data.
- Required user decisions: The user approved L2; a synthetic sample was selected because no real sample was designated.
- Result: Added the version-1 contract, strict atomic JSON I/O, and eight synthetic normal/failure tests without reading or writing user data.
- Next gate: User approval for L3.
- Status: Complete on 2026-07-18.

## L3 — Document and File Read/Write Optimization

- Objective: Read only documents needed for each task and write durable decisions to the correct source.
- Read: L2 contract, current router, and three representative user tasks with current effort measurements.
- Work: Validate read profiles and write-back routes; add one document registry or at most one or two helper commands only if measured routing remains costly.
- Modify: `AGENTS.md`, `docs/agent/DOCUMENT_REGISTRY.md` when classification requires it, and validated helpers/tests.
- Preserve: `PROJECT_RULES.md` as always-read global policy, `SESSION_HANDOFF.md` as state source, and Korean reports as non-execution documents.
- Complete when: Resume, structure-change, and video-task scenarios select the correct minimum documents and write target.
- Verify: Compare files read, context size, resume time, and wrong-document selections across three tasks.
- Rollback: Remove only L3 routing/helper changes.
- Result: Added three exact profiles to `AGENTS.md`, a classified document registry, audience/status folders, and routing/governance regression tests. The original profile measurement selected three or four documents, reduced document context by 46-64%, reduced cached local read time by 46-60%, and selected zero unrelated documents.
- Post-completion refinement: L3.1 tests whether a derived knowledge graph and Obsidian navigation reduce the
  remaining measured context and discovery costs without replacing this verified router.
- Next gate: The user's instruction authorized continuous execution through L4; no separate L3 pause was required.
- Status: Complete on 2026-07-19.

## L4 — File Lifecycle Rules

- Objective: Define minimal filename, version, current, approval, retention, and validation semantics.
- Read: L2 schema, actual consumer fields, and active lifecycle requirements.
- Work: Decide minimum fields, current/superseded behavior, approval-state reduction, integrity checks, and cleanup authorization.
- Modify: `docs/agent/FILE_DATA_CONTRACT.md` and its tests.
- Preserve: Existing filenames and metadata; never delete prior or failed versions automatically.
- Complete when: `state.json` alone identifies each output's role, source, currency, validation, and next-use eligibility without a migration-source lookup.
- Verify: Missing paths, wrong source IDs, current conflicts, integrity mismatch, and preserved superseded versions.
- Rollback: Remove only L4 fields and checks, retaining the verified L2 state core.
- Result: Activated schema version 3 with output version, current/superseded/failed status, lineage, SHA-256 integrity, approval purpose, and explicit next-use eligibility. A formal JSON Schema is synchronized with the runtime validator. Draft saves cannot persist eligible outputs; promotion saves first verify the exact reference input and bounded promotion files. Synthetic tests preserve prior and failed files.
- Next gate: User confirmation of approval and retention semantics before L5.
- Status: Complete on 2026-07-19.

## L3.1 — Obsidian Baseline and Graphify Evaluation

- Objective: Evaluate local document-navigation tools without moving source files and keep only capabilities that
  improve the direct L3 route.
- Read: The document-navigation contract above, current L3 router and registry, and only the exact evidence report
  named for a historical review.
- Completed work:
  1. Measured direct routing for resume, document-architecture, and designated state-contract profiles.
  2. Opened the original repository Markdown in Obsidian with stable local settings, standard links, no Sync or
     Publish, and no community plugins.
  3. Evaluated Graphify 0.9.20 with a local Ollama backend against an explicit 12-document framework allowlist.
  4. Sanitized the raw graph and ran three same-corpus benefit comparisons.
  5. Built a metadata-only typed helper after semantic comparison failed, then later confirmed its active route
     did not call Graphify and added 13, 30, and 22 estimated tokens over direct routing.
  6. On user cancellation, removed Graphify-specific repository files, external caches, package installation, and
     active references while retaining direct routing, Obsidian, and independent document-governance rules.
- Result: Semantic Graphify selected 8 and 5 wrong documents in two profiles and provided no token benefit in the
  third. The typed helper was exact but duplicated the direct route and was incorrectly represented as Graphify.
- Preserve: Original Markdown, stable Obsidian settings, document classification and lifecycle rules, direct route
  IDs and selectors, Git history, user data, migration sources, and historical evidence.
- Verify: Direct-route regressions, report registration, absence of Graphify-specific repository/runtime artifacts,
  UTF-8/NUL and local-link checks, Obsidian configuration, and the integrated project suite.
- Rollback: Already executed under the user's 2026-07-20 cancellation request. Do not recreate a helper, cache, or
  compatibility file. Version control is the recovery mechanism; no duplicate backup is required.
- Next gate: L5 still requires separate explicit approval and uses direct document routing only.
- Status: Complete and rolled back. Graphify is `excluded`; Obsidian remains `implemented`. See
  `docs/reports/2026-07-20_그래피파이_도입_실패_분석.md` for measured evidence and reporting failures.

## L5 — Workflow Rules

- Objective: Convert the reconstructed production foundation into concise human-readable inputs, outputs, completion criteria, and user decisions.
- Read: The document-navigation integration contract; `docs/agent/WORKFLOW_FOUNDATION.md`,
  `docs/agent/EDITING_QUALITY_RULES.md`, the L4 state contract, and only this L5 section through direct route
  `design_l5_workflow`.
- Work: Create `docs/agent/WORKFLOW_RULES.md` with pre-shoot and recorded-footage routes, one to three completion criteria per stage, user decision points, validation levels, stable metadata, and standard Markdown relationships visible in Obsidian.
- Preserve: Stage numbering, analysis-before-planning order (`6 -> 5` for recorded footage), 7A-7D judgment knowledge, evidence scope, and user creative authority.
- Complete when: One active document identifies the required input, output, completion, and next user decision for each stage, and its complete direct read path contains no `backup/` dependency.
- Verify: Walk through both workflow routes, reject missing stages or an incorrect `5 -> 6` order, and check direct-route selection, Obsidian links, and metadata.
- Rollback: Remove only the new active workflow rule; keep the reconstructed foundation unchanged.
- Next gate: User confirms the simplification and decision points.
- Status: Not started.

## L6 — Workflow Structure

- Objective: Make L5 rules visible in per-video folders, files, and state without pre-creating unused directories.
- Read: The document-navigation integration contract, L3.1 result, L2 state, L5 workflow rules, and active output conventions in the state and workflow foundations.
- Work: Define lazy folder creation, new-project initialization, output registration, one existing-project mapping plan, and Obsidian vault boundaries for the resulting structure.
- Modify: Structure document, minimal initialization code, direct-route updates, and tests; no user data without a designated sample.
- Preserve: Existing paths and references; do not create empty stage folders by default, index task/user data by default, or treat an Obsidian exclusion as an access-control boundary.
- Complete when: A synthetic project initializes once, reruns safely, matches the documented structure, and resolves every path and contract through active files.
- Verify: Creation, rerun, partial failure, rollback, direct-route boundary check, Obsidian boundary check, and a separately approved real sample.
- Rollback: Remove only the new sample and initializer.
- Next gate: User confirms fit with real work before L7.
- Status: Not started.

## L7 — Workflow Tools and Plugins

- Objective: Connect only frequently used state, transition, media, and validated knowledge-navigation operations through trustworthy thin entry points.
- Read: The document-navigation integration contract, L6 structure, measured task frequency, the selected capability in `docs/agent/TOOL_REQUIREMENTS.md`, and its active consumer contract.
- Work: Classify tools, activate at most two selected workflow commands, and repair exit codes, timeouts, parsing, reuse, and error messages.
- Preserve: Unselected capabilities as `specified`, `deferred`, or `excluded`; do not claim Premiere or media validation before real tests, reactivate Graphify by inference, or enable hooks, MCP, shared HTTP, work memory, or Obsidian community plugins by inference.
- Complete when: Each selected operation has predictable success, failure, and rerun behavior through one active entry point, with active tests and no archive import, command, fixture, or documentation dependency.
- Verify: Selected regressions, reproduced failures, installer change review, uninstall rollback, one user-approved real file, and application/A/V validation where applicable.
- Rollback: Remove the thin integration and tool changes only.
- Next gate: Only tools with measured time or error reduction proceed to L8.
- Status: Not started.

## L8 — Workflow Skill Alignment

- Objective: Align only confirmed-use skills with the L2-L7 state, paths, tools, completion rules, and direct navigation route.
- Read: The document-navigation integration contract, the selected responsibility in `docs/agent/SKILL_REQUIREMENTS.md`, L5 rules, L6 paths, L7 active tools, and user-confirmed use.
- Work: Classify responsibilities as implement, defer, or exclude; create each selected active skill with input, output, stop, user decision, handoff, direct-route selection, and source-validation contracts.
- Preserve: Unselected responsibilities as documented decisions; do not implement every skill or introduce a derived graph as an instruction path.
- Complete when: A selected active skill completes one representative stage without a routing, handoff, or archive dependency through the direct navigation route.
- Verify: Representative execution, direct-route selection, source-file confirmation, protected-path exclusion, output registration, stop condition, user decision transfer, and next-stage resume.
- Rollback: Revert only the affected skill changes.
- Final gate: Run the archive-retirement gate, then the user chooses whether to retire the migration archive, address another observed bottleneck, or begin real production.
- Status: Not started.

## Archive-retirement gate — after L8

- Objective: Prove the rebuilt project is complete and self-contained before `backup/` deletion.
- Read: `docs/agent/RECONSTRUCTION_MAP.md`, `docs/agent/DOCUMENT_REGISTRY.md`, active source references, and integrated-test results only.
- Check: Every retained capability is implemented or fully specified in an active destination; active documents,
  code, tests, fixtures, commands, and Obsidian configuration have no operational `backup/` reference; all active
  tests and direct navigation pass without archive access; deferred and excluded items have explicit rationale.
  Use the deterministic active-reference scan as the authority.
- Report: Produce a Korean readiness report listing any remaining dependency. Do not delete anything while a
  dependency remains.
- Delete authority: Only a separate explicit user request after a clean readiness report authorizes deleting `backup/`.
- After deletion: Remove transitional archive rules and rerun document, path, state, and workflow validation.
- Status: Not started; deletion is not authorized by this plan alone.

## Pending user decisions

| Layer | Decision required before work |
|---:|---|
| L5 | Approval to build the active workflow rule from reconstructed requirements through direct document routing |
| L6 | One exact real or synthetic structure sample |
| L7 | Selected frequent tools and the current Premiere/OS environment; hooks and MCP remain separate decisions |
| L8 | Which reconstructed skill responsibilities are actually used |
