# Always-On Project Rules

- Purpose: define the minimum policy that applies to every task.
- Change authority: the user approves policy changes; agents maintain approved wording.
- Priority: security > protected-data safety > accuracy > user outcome > efficiency.

## Outcome and authority

- The project exists to reduce manual production work and let agents act autonomously inside approved goals and safety boundaries.
- Within project-local instructions, authority is: latest user instruction > this policy > the exact active task owner. The task owner is the current user request unless an approved plan is explicitly named.
- `SESSION_HANDOFF.md` reports current state; it is not a policy or authority source.
- Agents own in-scope research, safe defaults, reversible implementation, proportionate validation, and failure recovery.
- Work only toward the requested outcome. Do not add materially broader changes.
- Ask only when the answer changes the authorized outcome, crosses a protected or external boundary, or creates material irreversible risk.

## Approval and recovery

- The user owns goals, prohibitions, protected-data access, external or costly actions, irreversible choices, and result confirmation.
- Ask before deletion or move unless the exact targets are approved; always ask before push, publish, upload, install, permission changes, paid actions, external writes, overwriting originals, or unapproved commits.
- Preserve unrelated user changes.

## Core immutability

- `core/` is the immutable agent foundation. Reading and executing approved core interfaces is allowed; creating, editing, deleting, moving, renaming, regenerating, or indirectly changing any path under `core/` is a controlled core change.
- A core change requires explicit user approval in the current conversation after the exact reason and target scope are known. A standing goal, prior approval, plan, inferred benefit, or approval to change `extension/` does not authorize a core change.
- After approval, change only the minimum named core scope and run the consolidated core and extension verification gate.
- An automatic, scheduled, background, delegated, or otherwise unattended task must never request, infer, or wait for core-change approval. If completing that task would require a core change, it must leave `core/` untouched, record a `core_change_required` failure in `extension/work/CORE_CHANGE_FAILURES.md`, return a non-success result, and stop that objective.
- A denied core change is an expected safety stop, not reusable resolved-failure knowledge. Do not add it to `core/failures/` unless a separate verified and generalizable defect meets the durable failure threshold.
- `core/rules/core-change-control.md` owns the exact procedure and verification command. This policy is higher authority.

## Protected data and history

- A path segment named `inputs` or `outputs` is protected. Do not access it without the user's exact item and purpose. Never stage or commit protected data.
- Never read or expose secrets, credentials, tokens, cookies, browser profiles, passwords, or private keys.
- Use Git commits for completed history and recovery. Do not create repository-local backup snapshots or duplicate historical reports.

## Information ownership

- Preserve only facts needed to resume, operate, audit, or reuse work.
- Each material active fact has one human-readable owner. Link to it instead of copying it.
- `PROJECT_RULES.md` owns always-on policy; `core/rules/*.md` owns foundation procedures.
- `SESSION_HANDOFF.md` owns only current work, blockers, verified state, and first next action.
- `core/docs/` owns foundation contracts and the concise project history; `core/failures/` owns reusable resolved-failure knowledge.
- `extension/` owns YouTube, video, production, skill, task, runtime, example, report, and other work-specific data. New domain work must not be added to `core/`.
- `extension/work/CORE_CHANGE_FAILURES.md` owns automatic-task failures caused by the immutable core boundary.
- Machine-readable maintained data must be a deterministic document derivative. Runtime and temporary data remain disposable and untracked.
- Create a maintained document only when no existing owner can serve its distinct durable purpose.
- Completed detail belongs to Git, not the active document tree.

## Verification and failures

- Validate in proportion to risk at a logical change checkpoint.
- `quick` work uses direct checks; `standard` work uses relevant tests; `controlled` work uses an explicit plan and consolidated gate.
- Unrun checks are not passes.
- Treat a corrected one-off typo, quoting error, wrong option, or transient tool issue as transient unless it reveals a reusable risk or materially blocks work.
- After three consecutive failures of the same objective, preserve the blocker, change the method, and continue inside authorized scope.
