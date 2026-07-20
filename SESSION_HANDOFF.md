# Session Handoff

- Purpose: Let the next agent resume from verified current project state without chat history.
- Scope: Current goal, verified result, failure history, risks, and first next action only.
- Audience and language: Agents; English.
- Read when: Before continuing, changing, or verifying project work.
- Write when: Current state, approval, verification, blocker, artifact status, or first next action changes.
- Authority: Sole current-state source; global rules are in `PROJECT_RULES.md` and rebuild scope is in `docs/agent/rebuild/REBUILD_PLAN.md`.

## Current state

- L3.3 is complete: active notes use Obsidian Properties, domain folders, atomic contracts, and the derived `docs/agent/navigation/AGENT_DOCUMENTS.base` index.
- Known task routes remain direct. Unknown classification uses one bounded Base domain view or domain-folder CLI search, then candidate properties and one atomic note.
- Graphify remains excluded. Ollama/QMD semantic routing, wrappers, MCP, hooks, and community plugins are inactive.
- No `inputs/`, `outputs/`, migration source, or other protected item was enumerated or read.
- The normalized three-condition token comparison is recorded in `docs/reports/2026-07-20_옵시디언_전면_도입_토큰_비교.md`.
- Next gate: L5 workflow rules remain separately unapproved.

## Resume checkpoint

- Use `AGENTS.md` direct routes first. For an unknown route, query the narrowest Base domain view or `docs/agent/<domain>` with at most three candidates.
- Compare `purpose` and `authority`; use `scope` and `read_when` only to resolve a tie; read one selected atomic note.
- Base views are generated indexes, never content authorities. YAML Properties own classification; Markdown bodies own rules and state contracts.
- Call `C:\Users\Hugh\AppData\Local\Programs\Obsidian\Obsidian.com` directly through its confirmed approved boundary. Do not wrap it or retry in the default sandbox.
- CLI failure, no result, malformed output, ambiguity, or protected-path risk is report-only. Do not silently fall back or switch engines.

## Verification state

| Target | Level | Evidence |
|---|---|---|
| Obsidian architecture | app-validated | Active, Navigation, State, and Historical Base views returned only their property-matched notes. |
| Candidate selection | app-validated | Placement and state-operation queries selected their exact atomic authorities through `purpose` and `authority`. |
| Routing efficiency | tool-validated | Same-profile direct, unchanged-note Obsidian, and optimized-note measurements are in the Korean comparison report. |
| Framework | tool-validated | Integrated tests cover properties, domain placement, Base bounds, routes, links, schema, Graphify exclusion, and context budgets. |

## Failure ledger

| Objective | Attempt | Result / cause | Count | Reuse condition |
|---|---|---|---:|---|
| Semantic Graphify benefit | Three comparisons | Excess context or overhead; excluded | 3 | Separate approval plus new measured design |
| Product-use classification | Typed helper | Local parsing was misreported as Graphify-first; removed | 1 | Require actual product-call proof |
| Official CLI startup | Direct version | Failed while app was stopped; one app start corrected it | 0 | Start once, retry once, then report |
| CLI execution boundary | Python wrapper | Repeated known sandbox failure because wrappers do not inherit child approval; removed | 1 | Use the exact direct boundary only |
| Obsidian optimization | Initial startup profile | Duplicate router guidance added context; removed before acceptance | 0 | Re-measure all three profiles after control-document edits |

## Risks and artifacts

- Obsidian must be running for CLI use; UI exclusions are navigation hints, not access control.
- `.obsidian/core-plugins.json` contains a pre-existing user change; preserve it.
- `docs/agent/navigation/DOCUMENT_PLACEMENT.md` owns placement; `DOCUMENT_REGISTRY.md` owns classification.
- `docs/agent/state/STATE_OPERATIONS.md` owns normal state I/O; `VIDEO_TASK_STATE.md` owns model/schema changes.
- Historical failure evidence: `docs/reports/2026-07-20_그래피파이_도입_실패_분석.md` and `docs/reports/2026-07-20_샌드박스_권한_반복_실패_분석.md`.

## First next action

Ask for separate L5 approval. If approved, use `design_l5_workflow`; use Obsidian discovery only for an unresolved authority.
