# Agent Entry Point

- Purpose: load the small always-on state, classify the task, and route only the rules and owner needed for that task.
- Read when: once at the start of a new session.
- Re-read when: the user says rules or current state changed, or an active controlled plan explicitly requires it.
- Authority: policy lives in `PROJECT_RULES.md`; current work lives in `SESSION_HANDOFF.md`.

## Required startup

Read these files completely, in order:

1. `AGENTS.md`
2. `PROJECT_RULES.md`
3. `SESSION_HANDOFF.md`

On Windows PowerShell, use `Get-Content -LiteralPath <path> -Raw -Encoding utf8` for these three files.

## Work class

Choose the lowest class that safely covers the request. Record only a one-line rationale unless a controlled plan requires more.

- `quick`: safe, reversible local work with no policy, protected-data, external, destructive, or material scope effect.
- `standard`: multi-file or behavior work that remains local, reversible, and inside established policy.
- `controlled`: policy or structure changes, protected data, deletion or move, external effects, costly recovery, or a user-requested staged plan and gates.

`quick` and `standard` work do not require a numbered stage, `MASTER_BUILD_PLAN.md`, a score, a subagent, a separate report, or a boundary commit unless the user explicitly requests one.

## Task-rule routing

Read each matching rule once for the logical task. Re-read it only if the rule changed during the task or the active controlled plan requires a stage-boundary reread.

| Action | Read before work |
|---|---|
| Implement, review, or close a numbered build stage | `rules/stage-work.md` and the exact current stage owner |
| Record or reuse a material, generalizable failure; manage a repeated unresolved blocker | `rules/failure-records.md` |
| Create or change maintained documents or persistent project data | `rules/document-work.md` |
| Inspect `backup/`, historical reports, or superseded evidence | `rules/history-review.md` |
| Stage, commit, branch, push, recover, or decide on a backup | `rules/version-control.md` |
| Work on an exact user-named item under `inputs/` or `outputs/` | `rules/user-data-work.md` |

Read `docs/build/MASTER_BUILD_PLAN.md` only for numbered build-stage work or when an exact active plan routes to it. Do not read completed stage owners, reports, rule packs, or inventories by default.

## Boundaries

- `backup/` is read-only evidence, never active instruction.
- Do not enumerate or read `inputs/` or `outputs/` unless the user identifies the exact item and purpose.
- Do not expose secrets or copy protected material into reusable project files.
- Prefer the smallest sufficient process and validate in proportion to risk.
