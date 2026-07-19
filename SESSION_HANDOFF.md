# Session Handoff

- Purpose: Let the next agent resume from verified current project state without chat history.
- Scope: Current goal, verified result, active blocker or risk, important artifacts, and first next action only.
- Audience and language: Agents; English.
- Read when: Before continuing, changing, or verifying project work.
- Write when: Current state, approval, verification, blocker, artifact status, or first next action changes.
- Authority: This is the sole current-state source. Global rules are in `PROJECT_RULES.md`; durable rebuild scope is in `docs/agent/REBUILD_PLAN.md`.

## Current state

- Date: 2026-07-19.
- Current goal: Await explicit approval to execute the newly planned L3.1 Graphify + Obsidian knowledge-navigation pilot; L5 must wait for an L3.1 `promote` or explicit `defer` decision.
- Rebuild position: L0-L4 and the backup-independence correction are synthetic-tool-validated.
- Authorization: The user approved adding the staged integration to the rebuild plan, not installing products, enabling hooks or MCP, moving documents, or changing tool metadata.
- Data boundary: No real `inputs/` or `outputs/` item is designated; do not enumerate or read user data.

## Resume checkpoint

- `docs/agent/REBUILD_PLAN.md` now contains one shared knowledge-navigation integration contract, an L3.1 no-move baseline and pilot, and explicit Graphify + Obsidian work, verification, rollback, and gates in L5-L8 and the archive-retirement audit.
- The planned role split is normative Markdown as source, Obsidian as the local human/agent navigation client, Graphify as a derived query graph, and the verified L3 router as the direct fallback.
- L3.1 requires a protected-path allowlist, external runtime outputs, three-task before/after measurements, provenance checks, Obsidian application validation, and a `promote`, `revise`, or `defer` user gate.
- `inputs/`, `outputs/`, `backup/`, `.git/`, `.agents/`, and `.codex/` must never enter the graph. Graphify-generated Obsidian vaults, community plugins, Sync, Publish, strict mode, hooks, MCP, servers, and work memory are not part of the pilot.
- No product installation, graph generation, vault configuration, document move, metadata migration, or routing implementation has been performed.

## Verification state

| Target | Level | Evidence |
|---|---|---|
| Obsidian adoption report | structure-validated | Korean governance metadata, expected sections, source links, registry entry, UTF-8/NUL, and local-link checks pass. |
| Staged rebuild plan | tool-validated | Required L3.1 and L5-L8 sections, UTF-8/NUL, local links, context budgets, and thirty-three `unittest` document, routing, state, and schema tests pass. |
| Graphify, Obsidian, and proposed node architecture | unimplemented | Plan and research are validated as documents only; product behavior in this workspace remains unverified. |
| Real video-task operation | unverified | No user-designated sample or application validation. |

## Failure ledger

| Objective | Attempt | Result / cause | Consecutive count | Next condition |
|---|---|---|---:|---|
| Stage Graphify + Obsidian across the rebuild plan | Current request | Completed with L3.1, L5-L8, rollback, and archive-gate placement; all document tests pass | 0 | Await L3.1 execution approval |
| Integrated validation | `pytest` attempts 1-2 | Shell Python was unavailable, then bundled Python lacked `pytest`; resolved by bundled Python `unittest discover` with 33/33 passing | 0 after success | Use bundled Python with `unittest discover` unless pytest is explicitly installed |

## Active blockers and risks

- L3.1 cannot start without explicit approval for both installers, the external Graphify runtime-output location, the allowed source manifest, and the document semantic-analysis backend.
- If Graphify cannot keep pilot caches and runtime artifacts outside the repository or cannot prove zero protected-path nodes, stop L3.1 rather than weakening the boundary by inference.
- Automatic installer edits to `AGENTS.md` or `.codex`, hooks, strict mode, MCP, servers, Obsidian community plugins, Sync, Publish, and generated work memory remain separately gated.
- L5-L8 implementation, document migration, real user-data reads, and archive deletion remain separately gated.

## Important artifacts

| Path | Status | Role |
|---|---|---|
| `docs/agent/REBUILD_PLAN.md` | active tool-validated authority | Controls the staged L3.1 and L5-L8 integration sequence |
| `docs/reports/2026-07-19_옵시디언_도입_타당성_분석.md` | structure-validated evidence | Current adoption analysis and bounded-pilot recommendation |
| `docs/reports/2026-07-19_문서_노드_구조_개선_분석.md` | historical structure-validated evidence | Prior L3 node and context-budget proposal |

## First next action

1. Ask whether the user approves L3.1 execution and obtain the four pending choices listed in the L3.1 plan gate.
2. If approved, read only the L3.1 section, its shared integration contract, the applicable rebuild principles, and the relevant reconstruction-map row before installation.
3. Establish the direct-routing baseline before installing or generating anything, then execute only the bounded no-move pilot.
4. Do not start L5, index or read user data, activate always-on integration, or delete the migration archive by inference.

## Next-session start prompt

```text
Read PROJECT_RULES.md and SESSION_HANDOFF.md.
The rebuild plan now stages Graphify + Obsidian through L3.1 and L5-L8, but installation and execution remain unapproved.
Wait for L3.1 approval; if approved, read its plan section, shared integration contract, applicable principles, and relevant reconstruction decision before making changes.
```
