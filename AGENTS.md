# Agent Entry Point

- Purpose: load the minimum startup state, classify the task, and route only the matching rule.
- Read when: once at the start of a new session.
- Authority: policy lives in `PROJECT_RULES.md`; current work lives in `SESSION_HANDOFF.md`.

## Startup

Read completely, once, in this order:

1. `AGENTS.md`
2. `PROJECT_RULES.md`
3. `SESSION_HANDOFF.md`

On Windows PowerShell, use `Get-Content -LiteralPath <path> -Raw -Encoding utf8`.

## Classify

Choose the lowest sufficient class:

- `quick`: safe, reversible local work with no policy, protected-data, external, destructive, or material scope effect.
- `standard`: multi-file or behavior work that remains local, reversible, and inside established policy.
- `controlled`: policy or structure changes, protected data, deletion or move, external effects, costly recovery, or user-requested gates.

Do not add a numbered plan, score, subagent, separate report, or commit to `quick` or `standard` work unless the user requests it.

## Route

Read each matching rule once per logical task:

| Action | Read before work |
|---|---|
| Create or change maintained documents or persistent project data | `rules/document-work.md` |
| Record or reuse a material, generalizable failure | `rules/failure-records.md` |
| Git stage, commit, branch, push, or recover | `rules/version-control.md` |
| Work on an exact user-named item under `inputs/` or `outputs/` | `rules/user-data-work.md` |

Detailed completed history is available through Git. Do not load old commits by default.
