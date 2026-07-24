# Always-On Project Rules

- Purpose: define the minimum policy that applies to every task.
- Change authority: the user approves policy changes; agents maintain approved wording.
- Priority: security > protected-data safety > accuracy > user outcome > efficiency.

## Purpose and autonomy

- The project exists to reduce manual production work and let agents act autonomously inside approved goals and safety boundaries.
- The user owns goals, prohibitions, protected-data access, external or costly actions, irreversible choices, and result confirmation.
- Agents own in-scope research, safe defaults, reversible implementation, proportionate validation, and failure recovery.
- Ask only when the answer changes the authorized outcome, crosses a protected or external boundary, or creates material irreversible risk.

## Authority and scope

- Follow the user's latest instruction, then this file, then `SESSION_HANDOFF.md`, then the exact task owner.
- Work only toward the requested outcome. Do not add materially broader changes.
- Ask before deletion or move unless the exact targets are approved; always ask before push, publish, upload, install, permission changes, paid actions, external writes, overwriting originals, or unapproved commits.
- Preserve unrelated user changes.

## Protected data and history

- A path segment named `inputs` or `outputs` is protected. Do not access it without the user's exact item and purpose.
- Never read or expose secrets, credentials, tokens, cookies, browser profiles, passwords, or private keys.
- Use Git commits for completed history and recovery. Do not create repository-local backup snapshots or duplicate historical reports.

## Durable project knowledge

- Preserve only facts needed to resume, operate, audit, or reuse work.
- Each material active fact has one human-readable owner. Link to it instead of copying it.
- Update the owner at a logical completion checkpoint with material decisions, results, blockers, verification state, and first next action.
- Machine-readable maintained data must be a deterministic document derivative. Runtime and temporary data remain disposable and untracked.
- Create a maintained document only when no existing owner can serve its distinct durable purpose.

## Structure and current state

- `PROJECT_RULES.md` owns always-on policy; `rules/*.md` owns conditional procedures.
- `SESSION_HANDOFF.md` owns only current work, blockers, verified state, and first next action.
- `docs/` owns active contracts and the concise project history.
- `failures/` owns reusable resolved-failure knowledge.
- `inputs/` and `outputs/` remain outside framework version control.
- Completed detail belongs to Git, not the active document tree.

## Verification and failures

- Validate in proportion to risk at a logical change checkpoint.
- `quick` work uses direct checks; `standard` work uses relevant tests; `controlled` work uses an explicit plan and consolidated gate.
- Unrun checks are not passes.
- A corrected one-off typo, quoting error, wrong option, or transient tool issue does not require a durable record.
- After three consecutive failures of the same objective, preserve the blocker, change the method, and continue inside authorized scope.
