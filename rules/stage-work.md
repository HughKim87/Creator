# Stage Work Rules

- Purpose: govern controlled work on a numbered build stage.
- Read when: before implementing, reviewing, or closing an exact stage in `docs/build/`.
- Authority: task-specific; `PROJECT_RULES.md` remains higher authority.

## Rules

- Read `docs/build/MASTER_BUILD_PLAN.md`, the exact current stage owner, and no completed or future stage owner unless a specific dependency requires it.
- Confirm prior boundary, current outcome, scope, exclusions, protected inputs, unresolved decisions, and transition authority.
- The stage owner defines its concrete success gate. Use one consolidated completion checkpoint rather than repeating unchanged full checks after every edit.
- Resolve safe reversible details autonomously. Ask only when the outcome, protection boundary, external effect, irreversible cost, or material risk changes.
- Implement only the current stage and report the planned change and exclusion boundary before writing.
- At completion, compare the actual diff and representative operation with the user outcome, safety boundary, current state, and relevant past failure prevention.
- A score, independent validator, separate report, or boundary commit is required only when the user, master plan, or exact stage owner explicitly requires it.
- If independent validation is required, finish local work first and follow the exact validator contract in the active plan. Do not infer a validator requirement from past stages.
- Reconcile only failures that meet `rules/failure-records.md`'s durable threshold; unresolved material blockers remain in `SESSION_HANDOFF.md`.
- Do not start the next stage until the current explicit gate and any approved boundary commit pass.
