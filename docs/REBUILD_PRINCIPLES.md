# Rebuild Principles

- Purpose: Define the decision principles, cost limits, and stop conditions for the incremental rebuild.
- Scope: Rebuild direction and layer execution discipline only; no current state, layer checklist, or global workspace policy.
- Audience and language: Agents; English.
- Read when: A rebuild task changes scope, selects an approach, evaluates an exception, or risks exceeding a layer boundary.
- Write when: Only when the user changes the intended rebuild direction or approves a durable exception.
- Authority: This is the sole source of rebuild principles. Layer work belongs in `REBUILD_PLAN.md`; current state belongs in `../SESSION_HANDOFF.md`.

## Core principles

1. **Reinforce before replacing.** Treat the preserved legacy framework as an asset. Recover only what the current layer needs.
2. **Classify before implementing.** Mark an existing asset as `adopt`, `adopt_with_changes`, `defer`, or `exclude` in `INHERITANCE_MAP.md` before replacing it.
3. **Solve an observed problem.** Introduce the smallest change that fixes a concrete failure, repeated cost, or blocked workflow.
4. **Improve quality and productivity together.** A safer system that makes real work materially slower does not pass.
5. **Keep documents precise and implementation small.** The plan may be detailed, but one layer should normally fit within two to four hours.
6. **Validate one layer independently.** Do not begin the next layer until the current layer's completion criteria pass and the user approves the next gate.
7. **Do not build speculative infrastructure.** Add databases, state machines, external memory, parallel-agent coordination, or mandatory gates only after a simpler approach repeatedly fails.
8. **Preserve originals and history.** Do not bulk-delete, bulk-move, bulk-rename, or migrate user data without a separately approved scope.

## Layer preflight

Before implementation, record concise answers in `SESSION_HANDOFF.md` when they are not already evident:

1. What concrete inconvenience exists without this layer?
2. What becomes faster, less error-prone, or more consistent?
3. What existing asset already addresses the problem, and what is the actual delta?
4. Can the delta finish within two to four hours? If not, what is deferred?

## Layer execution protocol

1. Read `PROJECT_RULES.md`, `SESSION_HANDOFF.md`, and only the current section of `REBUILD_PLAN.md`.
2. Read this document only when a principle or scope decision is required.
3. If an existing feature changes, read only the relevant `INHERITANCE_MAP.md` row and the files named by it.
4. Implement only the current layer's declared delta.
5. Run necessary fast checks during work and one integrated validation at layer completion.
6. Update `SESSION_HANDOFF.md` with verified results, failures, blockers, rollback, and the next gate.
7. Update `PROJECT_STATUS.md` only when a Korean user-facing milestone report is useful.

## Prohibited rebuild patterns

- Restoring or rewriting the entire legacy framework at once.
- Recreating stage-by-stage evidence packages, independent QA/red-team roles, or long observation gates without demonstrated need.
- Activating the archived SQLite/domain/service/storage stack before file-based state fails on a real use case.
- Installing plugins, hooks, CI, external memory, or broad CLI wrappers before measuring a repeated problem they solve.
- Reading or migrating all user data to discover a representative sample.
- Activating every legacy tool or skill before actual use is confirmed.
- Creating a second source of truth for rules, state, plans, or approvals.

## Stop and rollback conditions

Stop the current layer and report the cause, risk, and minimum choices when any condition applies:

- The layer exceeds twice its expected size or time.
- Progress requires work outside the declared layer delta.
- The same objective fails three consecutive times.
- A protected legacy file or user original would need modification.
- A second state source or document hierarchy appears necessary.
- The productivity benefit cannot be stated or measured.
- A required user decision would have to be guessed.

Rollback only the files introduced or changed by the current layer. Preserve the last verified layer, historical reports, Git history, `backup/`, and user data.
