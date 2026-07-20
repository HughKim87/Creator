# Session Handoff

- Purpose: Let the next agent resume from verified current project state without chat history.
- Scope: Current goal, verified result, active failure, risks, and first next action only.
- Audience and language: Agents; English.
- Read when: Before continuing, changing, or verifying project work.
- Write when: Current state, approval, verification, blocker, artifact status, or first next action changes.
- Authority: Sole current-state source; global rules are in `PROJECT_RULES.md` and rebuild scope is in `docs/agent/rebuild/REBUILD_PLAN.md`.

## Current state

- L3.3 is complete: active notes use Obsidian Properties, domain folders, atomic contracts, and the derived `docs/agent/navigation/AGENT_DOCUMENTS.base` index.
- Known routes remain direct; unknown authority discovery uses one bounded Base/domain query, candidate properties, and one atomic note.
- `PROJECT_RULES.md#requirement-compatibility-and-implementation-identity` now separates named-method requirements from outcome requirements and forbids relabeling a substitute as the requested product.
- Graphify remains excluded. Local semantic analysis, including Ollama-backed options, is deferred under the evidence conditions in `docs/agent/rebuild/RECONSTRUCTION_MAP.md`; it is not an active route.
- Active issue: Obsidian's backend responds, but its GUI has no main window. Local vault JSON and registration were valid; a process reset completed, yet this handoff check again found four responding Obsidian processes with `MainWindowHandle=0`. Visible relaunch is unverified.
- No `inputs/`, `outputs/`, migration source, or other protected item was enumerated or read.
- L5 workflow rules remain separately unapproved.

## Resume checkpoint

- Resolve the visible Obsidian window before L5. Do not reset `.obsidian` files or treat CLI success as proof that a GUI window exists.
- Do not start Obsidian with a hidden window. For GUI recovery, use the installed `Obsidian.exe` visibly; use `Obsidian.com` only for later CLI validation through its confirmed approved boundary.
- The last process reset terminated all four old instances; the current four zero-handle instances are a new unresolved state. Determine what relaunched them before another termination/relaunch cycle.
- All six vault-root JSON settings parsed, the current vault matched one global registration with `open=true`, the workspace active leaf existed, and Properties/Bases were enabled. Configuration corruption is not currently supported by evidence.
- Known task routing, Base candidate selection, and report-only discovery failure behavior remain unchanged.

## Verification state

| Target | Level | Evidence |
|---|---|---|
| Obsidian architecture | app-validated | Base views previously returned 11 active agent notes, 2 Navigation notes, 2 State notes, and 7 historical reports. |
| Obsidian configuration | tool-validated | Six local JSON files valid; one matching global vault registration; workspace active leaf valid; official CLI `1.12.7` responded. |
| Visible Obsidian GUI | unverified / active failure | Four responding processes currently have no main window handle or title after one completed process reset. |
| Routing efficiency | tool-validated | Direct, unchanged-note Obsidian, and optimized-note totals are recorded in the Korean comparison report. |
| Framework | tool-validated | Latest integrated run passed 38/38 tests; document format and diff checks passed. |

## Failure ledger

| Objective | Attempt | Result / cause | Count | Next condition |
|---|---|---|---:|---|
| Semantic Graphify benefit | Three comparisons | Excess context or overhead; excluded | 3 | Separate approval plus new measured design only |
| Product-use classification | Typed helper | Custom parsing was misreported as Graphify-first; removed and global identity rules added | 0 after correction | Require proof of the active product entry point |
| CLI execution boundary | Python wrapper | Repeated known sandbox failure because wrappers do not inherit child approval; removed | 1 | Use the exact direct boundary only |
| Visible Obsidian GUI | Process reset v1 | Four zero-handle processes were terminated; four new responding zero-handle processes later appeared, relaunch source unknown | 1; unresolved | Inspect window/global app state and launch path without modifying the vault |

## Risks and important artifacts

- Preserve the pre-existing user change in `.obsidian/core-plugins.json`; do not reset the valid vault configuration without new evidence and approval.
- `PROJECT_RULES.md` is the active authority for requirement conflicts and product identity.
- `docs/agent/rebuild/RECONSTRUCTION_MAP.md` is the active authority for Graphify exclusion and deferred semantic analysis.
- `docs/reports/2026-07-20_그래피파이_도입_실패_분석.md` is historical evidence, not an execution source.
- `docs/reports/2026-07-20_옵시디언_전면_도입_토큰_비교.md` contains the normalized 23,490 / 21,627 / 17,835 comparison.

## First next action

Continue the visible-window diagnosis from the current four zero-handle Obsidian processes. Identify the relaunch path and global Electron/window state before changing files or repeating the reset. After visible GUI confirmation, return to the separate L5 approval gate.

## Next-session start prompt

```text
Read PROJECT_RULES.md and SESSION_HANDOFF.md. Continue the unresolved Obsidian visible-window diagnosis; do not reset valid vault settings or use CLI success as GUI proof. Graphify is excluded, semantic analysis is deferred, and L5 is unapproved.
```
