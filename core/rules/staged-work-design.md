# Staged Work Design

- Purpose: make multi-stage controlled work resumable and verifiable without turning one active plan into an unreadable history.
- Read when: designing, executing, resuming, or transitioning controlled work with dependent stages, multiple sessions, or stage-specific success gates.
- Authority: `PROJECT_RULES.md` is higher authority; the user approves material scope, protected or external actions, and exact Core changes.

## Condition and owner topology

- Use staged design when work has at least two dependent stages, cannot be safely completed in one execution checkpoint, or requires different approvals or success gates by stage.
- Keep one short `overall-design`, at most one active `phase-design`, and the current-state document selected by `PROJECT_RULES.md`.
- A file-producing active phase may have exactly one task-rule owner under the document-work lifecycle. Prefer a section in the phase owner; if separate, the phase links that one file and owns its lifecycle state.
- The overall design owns stable direction and the stage map. The active phase design owns exact execution and gate definitions for that stage. The selected current-state document owns verified progress, blockers, gate results, and the first next action.
- Long analysis and historical evidence are optional `reference-evidence`; they never become a required link in the startup chain.

## Overall design

- State the final outcome, invariants, prohibited expansion, ordered stages, dependencies, and one-line success outcome for each stage.
- Link only the active phase design in detail. Future stages remain summaries until their entry conditions are satisfied.
- Do not copy current Git state, active blockers, detailed commands, completed checkpoints, or phase-level gate procedures.
- Keep the document within the `overall-design` read budget defined by `document-work.md`.

## Phase design

- Create a detailed phase design only when that phase is current or is the immediate candidate for activation.
- State the phase ID and lifecycle state: `draft`, `ready`, `in_progress`, `blocked`, `passed`, `invalidated`, or `superseded`.
- Define the phase outcome, entry gate, exact included and excluded scope, decisions, ordered execution slices, slice verification, exit gate, recovery or stop conditions, evidence owner, and transition condition.
- Use stable gate IDs inside the phase. The overall design keeps only the one-line stage outcome; the current-state document records only gate status and evidence pointers.
- Keep the document within the `phase-design` read budget defined by `document-work.md`.

## Gate and transition rules

1. `entry gate`: confirm the prior phase outcome, required approvals, inputs, and active design before mutation.
2. `slice gate`: verify one coherent mutation slice before starting the next; do not treat unrun checks as passes.
3. `exit gate`: require every exact acceptance item and evidence owner for the current phase.
4. `commit checkpoint`: when a phase changes maintained project files or produces a persistent result, define the phase exit as a Git commit boundary. After the exit gate passes and before transition, commit only the approved task-owned paths; do not create a commit boundary for each slice unless the phase design explicitly requires it. The `version-control` rule still governs approval, protected paths, unrelated baseline changes, and post-write verification.
5. `transition gate`: self-review scope growth, document count, read budget, remaining risk, and whether the next phase is still necessary.

Before an exit gate can pass, freeze and absorb the active task-rule, clean its approved scratch root, and retire the task-rule owner. A phase may remain resumable with an `active` task-rule, but it may not become `passed` while that owner or scratch residue remains active.

- Only one phase may be `ready` or `in_progress` as the active execution target.
- Do not create detailed documents for all future phases in advance.
- Do not activate the next phase merely because the previous implementation ended; first pass its exit gate, update the selected current-state document, and satisfy the next entry gate.
- A user correction that changes the desired outcome, scope, or gate invalidates the active phase design. Stop queued mutation, mark the phase `invalidated`, revise the design, and obtain any newly required approval.
- A blocked phase keeps its exact blocker and first restart action in the selected current-state document; raw attempts and completed detail do not accumulate in the phase design.

## Delegated execution and handoff

- Condition: apply this section before another agent, session, worktree, or unattended run becomes responsible for active staged work.
- The active document set must preserve the user's desired outcome and non-negotiable intent, not only the requested edits. It must also identify the current phase, first unstarted action, exact included and excluded scope, authority and approval state, success gates, stop or recovery conditions, and material decisions or rejected alternatives whose reasons constrain later work.
- Declare every persistent artifact's exact path, owner, reader, role, and retention or expiry before creating it. When gate evidence cannot fit the phase read budget, use one exact optional `reference-evidence` owner for that phase; it must not enter the startup-required route and must state when it becomes historical.
- Declare the handoff mode as `same-workspace` or `portable`. A handoff that depends on uncommitted or local-only files is `same-workspace`; do not claim that a fresh clone, new worktree, or other machine can resume it until every required artifact is retrievable from an exact committed or otherwise immutable reference.
- Freeze the working-tree baseline by exact path, Git status, ownership label, and a content or diff anchor where practical. Exit gates compare task-owned changes and confirm unrelated baseline changes are unchanged; they must not require a globally clean tree when the entry baseline was dirty.
- Record checks that are expected to fail because of the entry baseline, including the exact failure and restart condition. A delegated agent must not reinterpret a known baseline failure as a new task failure or bypass it with broader permission.
- User or Core approval from another conversation does not transfer by summary or implication. Record what was approved and require the receiving agent to obtain current-conversation approval whenever the applicable rule requires it.
- Provide a compact next-session start prompt containing the read order, active phase, first action, exact prohibitions, and approval boundary. It is a resume aid, not a second current-state owner.

### Delegation gate

Before handing off, verify that all required paths exist, design budgets and single-owner rules pass, the handoff mode is truthful, baseline ownership is exact, expected failures are labeled, and a new agent can restate the objective, intent, next action, prohibitions, and gates without relying on chat history.

## Required reading route

For an active staged task, read in this order:

1. `PROJECT_RULES.md` and the current-state document it selects;
2. the short overall design;
3. the one active phase design;
4. the one task-rule owner when the phase declares one;
5. only the conditional rules matched by the phase's next action;
6. exact reference evidence only when a named decision cannot be resolved from the active documents.

Do not follow a phase document into every future phase or historical report.

## Verification

- Confirm one routed overall design and zero or one routed active phase design.
- Confirm that the current-state document names the same active phase and records a first next action.
- Confirm the overall and phase documents satisfy their separate content roles and read budgets.
- Confirm each active phase has entry, slice, exit, and transition gates with no duplicated exact gate owner.
- Confirm future phases are summaries, optional evidence is not startup-required, and completed detail is recoverable through Git.
- Confirm delegated work passes the delegation gate and does not claim portability or approval that its recorded artifacts cannot prove.
- Confirm a passed or completed phase has zero active task-rule owners and zero current-task scratch residue, while an interrupted phase links exactly one resumable task-rule owner when it has one.
- Before closeout, run the verification required by every changed rule and the approved Core gate when Core files changed.
