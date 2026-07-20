# Session Handoff

- Purpose: Let the next agent resume from verified current project state without chat history.
- Scope: Current goal, verified result, active blocker or risk, important artifacts, and first next action only.
- Audience and language: Agents; English.
- Read when: Before continuing, changing, or verifying project work.
- Write when: Current state, approval, verification, blocker, artifact status, or first next action changes.
- Authority: This is the sole current-state source. Global rules are in `PROJECT_RULES.md`; durable rebuild scope is in `docs/agent/REBUILD_PLAN.md`.

## Current state

- Date: 2026-07-20. The user cancelled Graphify adoption; L3.1 is complete and rolled back to direct document routing.
- Authorization: Direct `AGENTS.md` routing and stable local Obsidian settings remain approved. Graphify is excluded and its package, repository implementation, and project cache were removed. Ollama remains installed but is inactive for document routing; removing it requires a separate request. L5 and other integrations remain unapproved.
- Data boundary: No real `inputs/` or `outputs/` item was designated, enumerated, or read during the pilot or rollback.
- Next gate: L5 workflow-rule implementation requires separate explicit approval.

## Resume checkpoint

- `AGENTS.md#selection-protocol` selects stable route IDs directly, requires affected/named/designated selectors, prohibits relationship-driven expansion, and stops and reports ambiguity or protected-path conflicts.
- The registry defines two orthogonal indexes only: task-time routing in `AGENTS.md` and document classification in the registry; no third hand-maintained catalog is allowed.
- New documents must have one durable purpose, six header fields, one registry row, correct audience/lifecycle folder, stable ID/name, typed relationships, and same-change route/link/test updates.
- Split when authority, audience/language, lifecycle, read trigger, write owner, or repeated task context differs; merge only duplicate ownership with the same attributes.
- Actual semantic Graphify selected 8 and 5 wrong documents in two profiles and added 21,054, 14,197, and 40 estimated tokens over direct across the three profiles.
- The later typed helper was exact at +13/+30/+22 tokens but did not call Graphify on its active route. Calling it Graphify-first was a material reporting failure.
- The Korean failure report records the measurements, root causes, impact, rollback scope, and reopening conditions. It is historical evidence, not an execution authority.
- Obsidian 1.12.7 remains configured on the original vault with standard links, no Sync/Publish, and zero community plugins. Ollama 0.32.1 and its local model were not removed.

## Verification state

| Target | Level | Evidence |
|---|---|---|
| Document architecture | tool-validated | Stable task/write/document IDs, metadata and naming rules, two-index navigation, explicit selectors, and split/merge lifecycle rules remain covered by routing/governance tests. |
| Direct routing | tool-validated | Representative routes read only their declared delta and report missing selectors, ambiguity, or protected boundaries instead of invoking a generated graph. |
| Graphify rollback | tool-validated | Dedicated files are absent, `graphifyy` is uninstalled, the project cache is absent, the capability is `excluded`, and the failure report is registered. |
| Integrated framework | tool-validated | The independent Python runtime passes 35/35 tests; UTF-8/NUL, links, 69-line handoff, Graphify artifact absence, and retained Obsidian configuration checks pass. |

## Failure ledger

| Objective | Attempt/version | Result / cause | Consecutive count | Next condition |
|---|---|---|---:|---|
| Semantic Graphify benefit | Comparisons v1-v3 | Generic depth-2 traversal selected excess context or added overhead in every profile | 3; stopped and excluded | Separate approval, real scale evidence, and a new product-backed design only |
| Product-use classification | Typed helper review | Active route parsed local tables and JSON but did not call Graphify; it was incorrectly reported as Graphify-first | 1; corrected and rolled back | Require an actual product-call proof before any future adoption claim |
| Typed helper benefit | `typed-comparison-v2` | Exact authorities, but +13/+30/+22 tokens and about 133-164 ms versus direct selection near 0.010 ms | 1; removed | Direct routing remains authoritative |

## Active blockers and risks

- L5 is not approved. Do not infer workflow-rule implementation from the completed rollback.
- Do not recreate or reinstall Graphify, a compatible-format route graph, or a semantic router without a separate user decision and the report's evidence conditions.
- Obsidian exclusions are navigation hints, not access control. Protected paths remain unavailable without an exact user-named item and purpose.
- Ollama is installed but has no active project role. Do not infer either its use or removal.

## Important artifacts

| Path | Status | Role |
|---|---|---|
| `AGENTS.md` | active authority | Task/read/write routing and deterministic selection protocol |
| `docs/agent/DOCUMENT_REGISTRY.md` | active authority | Document contract, classification, placement, naming, lifecycle, relationship, and navigation index |
| `docs/reports/2026-07-20_그래피파이_도입_실패_분석.md` | historical evidence | Measured failure, reporting analysis, rollback, and future reopening conditions |
| `.obsidian/` | retained local configuration | Original-vault review settings; not an access-control or routing authority |

## First next action

1. Ask for separate L5 approval. If approved, use direct route `design_l5_workflow`; do not reactivate Graphify or read user data by inference.

## Next-session start prompt

```text
Read PROJECT_RULES.md and SESSION_HANDOFF.md. Graphify was cancelled and rolled back; direct routing and Obsidian remain. Ask for separate L5 approval.
```
