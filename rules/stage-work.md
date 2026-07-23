# Stage Work Rules

- Purpose: govern implementation, review, validation, and closure of a numbered build stage.
- Read when: before implementing, reviewing, or closing any stage in `docs/build/`.
- Owner: user-approved policy; project agents maintain accepted wording.
- Authority: task-specific; `PROJECT_RULES.md` remains higher authority.

## Rules

- Read `docs/build/MASTER_BUILD_PLAN.md` and only the current stage plan required for the task.
- Confirm the prior stage gate, current scope, exclusions, protected inputs, and unresolved user decisions before implementation.
- Resolve safe, reversible implementation details with the narrowest reasonable default and record the rationale. Ask the user only when a policy, technology, tool, or numerical value changes the authorized outcome, protection boundary, material risk, external effect, or irreversible cost.
- Implement only the current stage. Do not add a later-stage interface, dependency, data structure, or completion requirement early.
- Report the planned change and exclusion boundary before writing.
- Run the stage's consolidated verification at the completion checkpoint. If it fails, fix the cause and repeat the consolidated verification.
- Record evidence for user-purpose alignment, actual operation, future-stage exclusion, and past-failure prevention.
- At stage closure, also apply `rules/failure-records.md`: promote every verified resolved failure to the cross-stage `failures/` knowledge owner, retain unresolved failures as handoff blockers, and record a no-failure result when applicable.
- After those four checks and before the completion report, run the final self-review and scoring gate in `docs/build/MASTER_BUILD_PLAN.md#64-최종-자체-검토점수-게이트`.
- Inspect the complete stage diff, evidence, unresolved risks, and cross-document consistency. Score every rubric dimension, explain every deduction, and fix any in-scope correctable defect before reassessing.
- A score never overrides a critical defect, a failed required check, an unresolved deduction, or user approval. Report the score and readiness result explicitly.
- After `완료 준비`, apply the stage-boundary commit gate in `MASTER_BUILD_PLAN.md#65-단계-경계-커밋-게이트` and `rules/version-control.md`. A required commit must succeed and be verified before the next stage begins.
- Do not begin the next stage without traceable transition authority. A user-approved standing policy may cover a precise stage sequence when each success gate and boundary commit passes and no scope or risk changes.
