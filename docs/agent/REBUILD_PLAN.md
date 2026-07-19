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
- Current gate: The typed-route comparison is complete. It selects exact authorities but adds 13, 30, and 22 tokens over direct routing for the three profiles, so direct routing remains default; the typed graph is optional validation and semantic traversal remains deferred.
- Active layer: L3.1 complete — direct task routing is default, the typed route graph is an optional derived validator, and no Graphify path selects authorities by default.
- L5 remains unapproved and requires a separate user gate.
- User-directed document reorganization after L1 supplied the initial L3 routing structure; L3 then measured and regression-tested three representative profiles.
- The post-L4 supplement separated agent, user, and report documents; added a document registry and governance checks; and hardened schema, input identity, output promotion, validation scope, and approval scope.
- Required migration-source knowledge has been reconstructed into active workflow, editing-quality, tool, and skill requirement documents. Active execution must not depend on the temporary migration archive.
- The later document-node analysis found that mandatory startup and future L5 context remain costly and that
  semantic duplication and registry double-entry remain unresolved; those observed costs justify a bounded
  navigation pilot under the rebuild principles.
- L2 through L4 and navigation verification use framework documents and synthetic exact-item paths only. No real
  user-data mapping, plugin or hook activation, semantic Graphify promotion, or L5 implementation is authorized.

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
| Graphify and Obsidian adoption evidence | `docs/reports/2026-07-19_옵시디언_도입_타당성_분석.md` |

Historical reports are evidence only and are not execution inputs unless explicitly requested.

## Knowledge-navigation integration contract

This contract applies to L3.1 and to the Graphify or Obsidian work explicitly declared in L5-L8.

1. The existing active Markdown files remain the only document content sources of truth. Obsidian is a local
   human and agent navigation client; Graphify is a derived relationship index and query layer.
2. Graphify `EXTRACTED`, `INFERRED`, or `AMBIGUOUS` edges are retrieval evidence, not authority decisions.
   Every normative answer or change must resolve to an active source file before use.
3. Task-time authority selection uses a generated typed route graph derived only from `AGENTS.md` and
   `docs/agent/DOCUMENT_REGISTRY.md`. It resolves an explicit route ID and traverses one whitelisted edge;
   document-node expansion and generic semantic relationships are prohibited.
4. Do not generate a second Obsidian vault or duplicate project notes from Graphify. Open the approved original
   Markdown scope in place and keep generated views or graphs non-authoritative.
5. Never index, enumerate, copy, or expose `inputs/`, `outputs/`, `backup/`, `.git/`, `.agents/`, or `.codex/`.
   Use an allowlist-oriented `.graphifyignore` or an equivalent bounded source manifest and verify the resulting
   graph contains zero protected-path nodes.
6. Keep Graphify caches, costs, converted files, and runtime output outside the repository during the pilot.
   If the tool cannot satisfy that boundary, stop the layer and request a scoped design decision; do not create
   `graphify-out/` in the repository by inference.
7. The L3 router and direct Markdown read path remain the fallback when Obsidian, Graphify, their caches, or their
   model backend are unavailable or stale.
8. Community plugins, Obsidian Sync or Publish, Graphify strict mode, automatic hooks, MCP, shared servers, and
   generated work-memory or reflection files require their own measured need and explicit approval.

## Layer sequence

| Layer | Outcome | Dependency | Status |
|---:|---|---|---|
| L0 | Canonical documents, historical labels, and baseline | None | Complete |
| L1 | Project-wide file, path, authorization, and failure rules | L0 | Complete |
| L2 | File-based work state and safe I/O | L1 | Complete |
| L3 | Task-specific document routing and efficient read/write profiles | L2 | Complete |
| L4 | Minimal file lifecycle, version, current, and approval rules | L2 and L3 | Complete |
| L3.1 | Bounded Graphify + Obsidian baseline, typed-route redesign, and promotion decision | L3 and L4 | Complete; typed route implemented, semantic traversal deferred |
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

## L3.1 — Graphify + Obsidian Knowledge-Navigation Pilot

- Objective: Establish a no-move baseline and determine whether Graphify plus Obsidian materially reduce agent
  document discovery and user review cost before L5-L8 create more documents.
- Read: The knowledge-navigation integration contract above, current L3 router and registry, the two named
  decision-evidence reports, and only the representative active source documents selected for each benchmark.
- Preflight: Classify the navigation capability in the relevant `docs/agent/RECONSTRUCTION_MAP.md` row before
  installation; confirm approved installers, an external runtime-output location, an allowed document manifest,
  the document semantic-analysis backend, and a rollback command. Do not read protected paths to build the list.
- Work:
  1. Record a fresh direct-routing baseline for resume, document-architecture, and designated state-contract
     tasks: source files selected, document tokens, query time, wrong-authority selections, and unresolved links.
  2. Install Obsidian and Graphify only after the L3.1 user gate. Do not run Graphify's Codex installer, strict
     mode, hooks, MCP, Sync, Publish, or community plugins during the bounded pilot.
  3. Open the original repository Markdown in Obsidian without moving or duplicating files; use standard Markdown
     links, core features, Restricted Mode, deletion confirmation, and explicit UI exclusions.
  4. Build a Graphify graph from the explicit active-framework allowlist only. Store all runtime output outside
     the repository and retain provenance labels for every returned edge.
  5. Run the same three representative tasks through Graphify query/path selection, then open only the returned
     active Markdown sources. Bound graph-query output and total document context separately.
  6. Compare the new results with the direct-routing baseline and test the direct fallback with Graphify and
     Obsidian unavailable.
  7. After the semantic design failed three comparisons, generate a separate metadata-only route graph from the
     router and registry, use stable route/write IDs, and restrict task selection to one whitelisted hop.
- Modify: Only an approved stable metadata schema, source allowlist or `.graphifyignore`, bounded navigation
  helper, tests, and selected stable Obsidian configuration. Do not let an installer overwrite `AGENTS.md` or
  directly edit `.codex` during this layer.
- Preserve: Existing active paths, document authority, L3 routing profiles, Git history, user data, migration
  sources, and the rule that reports are not execution inputs.
- Complete when:
  1. All three tasks return the correct active authority with zero protected-path nodes or reads.
  2. Typed-route results equal the direct minimum set, load zero graph document bodies, perform zero document-node
     expansion, and remain unchanged when unrelated registered documents are present.
  3. Each normative result is traceable to a source path and Graphify confidence is visibly distinguished from
     source-validated fact.
  4. Obsidian opens the original Markdown, resolves standard links, displays Korean and English metadata, and
     creates no duplicate source hierarchy.
  5. Direct routing still completes the same tasks when both products are unavailable or the graph is stale.
  6. A Graphify path becomes default only when its compact query payload plus selected source context is lower
     than the same direct route without a wrong-authority increase.
- Verify: UTF-8/NUL and link checks, graph protected-path audit, exact authority hashes, one-hop edge whitelist,
  missing-selector and stale-graph rejection, three-task exact-selection checks, Obsidian application checks,
  direct fallback, and the integrated document-routing suite.
- Rollback: Uninstall only the pilot tools and stable pilot configuration, remove only current-layer external
  outputs, and retain the verified direct router and original Markdown unchanged.
- Next gate: L3.1 is complete. L5 may start only after separate explicit approval and must use the direct router
  by default; the typed graph is on-demand validation and semantic Graphify traversal cannot select authorities.
- Status: Direct routing wins the final token gate. On the historical corpus the typed graph estimates 5,188,
  8,878, and 8,208 tokens versus direct 5,175, 8,848, and 8,186; current deltas remain +13, +30, and +22.
  The typed graph stays implemented but optional, while the earlier semantic content graph remains deferred.

## L5 — Workflow Rules

- Objective: Convert the reconstructed production foundation into concise human-readable inputs, outputs, completion criteria, and user decisions.
- Read: The knowledge-navigation integration contract; `docs/agent/WORKFLOW_FOUNDATION.md`,
  `docs/agent/EDITING_QUALITY_RULES.md`, the L4 state contract, and only this L5 section. Select them through
  the direct route `design_l5_workflow`; use the typed graph only for ambiguity validation and do not use
  semantic Graphify relationships.
- Work: Create `docs/agent/WORKFLOW_RULES.md` with pre-shoot and recorded-footage routes, one to three completion criteria per stage, user decision points, validation levels, stable node metadata, and standard Markdown relationships visible in Obsidian and Graphify.
- Preserve: Stage numbering, analysis-before-planning order (`6 -> 5` for recorded footage), 7A-7D judgment knowledge, evidence scope, and user creative authority.
- Complete when: One active document identifies the required input, output, completion, and next user decision for each stage, its complete read path contains no `backup/` dependency, and the typed route selects the same authorities as the direct fallback.
- Verify: Walk through both workflow routes, reject missing stages or an incorrect `5 -> 6` order, check Obsidian links and metadata, compare typed-route selection with the direct fallback, and reject semantic edges used as authority.
- Rollback: Remove only the new active workflow rule; keep the reconstructed foundation unchanged.
- Next gate: User confirms the simplification and decision points.
- Status: Not started.

## L6 — Workflow Structure

- Objective: Make L5 rules visible in per-video folders, files, and state without pre-creating unused directories.
- Read: The knowledge-navigation integration contract, L3.1 result, L2 state, L5 workflow rules, and active output conventions in the state and workflow foundations.
- Work: Define lazy folder creation, new-project initialization, output registration, one existing-project mapping plan, Obsidian vault boundaries, and Graphify source/output boundaries for the resulting structure.
- Modify: Structure document, minimal initialization code, deterministic navigation allowlist generation, and tests; no user data without a designated sample.
- Preserve: Existing paths and references; do not create empty stage folders by default, index task/user data by default, or treat an Obsidian exclusion as an access-control boundary.
- Complete when: A synthetic project initializes once, reruns safely, matches the documented structure, resolves every path and contract through active files, and remains outside the Graphify active-framework graph unless specifically designated and approved.
- Verify: Creation, rerun, partial failure, rollback, protected-path graph audit, Obsidian boundary check, and a separately approved real sample.
- Rollback: Remove only the new sample and initializer.
- Next gate: User confirms fit with real work before L7.
- Status: Not started.

## L7 — Workflow Tools and Plugins

- Objective: Connect only frequently used state, transition, media, and validated knowledge-navigation operations through trustworthy thin entry points.
- Read: The knowledge-navigation integration contract, L3.1 measurements, L6 structure, measured task frequency, the selected capability in `docs/agent/TOOL_REQUIREMENTS.md`, and its active consumer contract.
- Work: Classify tools, activate at most two selected workflow commands, and repair exit codes, timeouts, parsing, reuse, and error messages. Keep the typed route helper bounded by source hashes, one-hop edges, selectors, and direct fallback; consider always-on integration only after repeated navigation cost is measured.
- Preserve: Unselected capabilities as `specified`, `deferred`, or `excluded`; do not claim Premiere or media validation before real tests, and do not enable Graphify hooks, strict mode, MCP, shared HTTP, work memory, or Obsidian community plugins by inference.
- Complete when: Each selected operation has predictable success, failure, and rerun behavior through one active entry point, with active tests and no archive import, command, fixture, or documentation dependency; an active navigation entry point must also fail closed on protected scope and fail over to direct routing when unavailable.
- Verify: Selected regressions, reproduced failures, graph refresh and stale-cache failures, installer change review, uninstall rollback, one user-approved real file, and application/A/V validation where applicable.
- Rollback: Remove the thin integration and tool changes only.
- Next gate: Only tools with measured time or error reduction proceed to L8.
- Status: Not started.

## L8 — Workflow Skill Alignment

- Objective: Align only confirmed-use skills with the L2-L7 state, paths, tools, completion rules, and validated navigation route.
- Read: The knowledge-navigation integration contract, the selected responsibility in `docs/agent/SKILL_REQUIREMENTS.md`, L5 rules, L6 paths, L7 active tools, and user-confirmed use.
- Work: Classify responsibilities as implement, defer, or exclude; create each selected active skill with input, output, stop, user decision, handoff, typed-route selection when a route exists, source validation, and direct-fallback contracts.
- Preserve: Unselected responsibilities as documented decisions; do not implement every skill or make a derived graph the only path to required instructions.
- Complete when: A selected active skill completes one representative stage without a routing, handoff, or archive dependency through both the typed navigation route and the direct fallback.
- Verify: Representative execution, bounded graph retrieval, source-file confirmation, protected-path exclusion, output registration, stop condition, user decision transfer, graph-unavailable fallback, and next-stage resume.
- Rollback: Revert only the affected skill changes.
- Final gate: Run the archive-retirement gate, then the user chooses whether to retire the migration archive, address another observed bottleneck, or begin real production.
- Status: Not started.

## Archive-retirement gate — after L8

- Objective: Prove the rebuilt project is complete and self-contained before `backup/` deletion.
- Read: `docs/agent/RECONSTRUCTION_MAP.md`, `docs/agent/DOCUMENT_REGISTRY.md`, active source references, and integrated-test results only.
- Check: Every retained capability is implemented or fully specified in an active destination; active documents,
  code, tests, fixtures, commands, Obsidian configuration, and Graphify source manifests have no operational
  `backup/` reference; all active tests and the direct navigation fallback pass without archive access; deferred
  and excluded items have explicit rationale. Regenerate the typed route graph from its two active authorities
  and verify it contains no archive or protected-path node. Treat graph results as advisory to the deterministic
  active-reference scan.
- Report: Produce a Korean readiness report listing any remaining dependency. Do not delete anything while a
  dependency remains.
- Delete authority: Only a separate explicit user request after a clean readiness report authorizes deleting `backup/`.
- After deletion: Remove transitional archive rules and rerun document, path, state, and workflow validation.
- Status: Not started; deletion is not authorized by this plan alone.

## Pending user decisions

| Layer | Decision required before work |
|---:|---|
| L5 | Approval to build the active workflow rule from reconstructed requirements; typed routes are available and semantic Graphify authority selection is deferred |
| L6 | One exact real or synthetic structure sample |
| L7 | Selected frequent tools, current Premiere/OS environment, and whether measured navigation benefit justifies any always-on Graphify integration; hooks and MCP remain separate decisions |
| L8 | Which reconstructed skill responsibilities are actually used |
