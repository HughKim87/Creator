# Always-On Project Rules

- Purpose: define the minimum policy that applies to every task.
- Read when: once at session start, after `AGENTS.md`.
- Change authority: the user approves policy changes; agents maintain approved wording.
- Priority: security > protected-data safety > accuracy > user outcome > efficiency.

## Purpose and autonomy

- The project exists to maximize productive agent autonomy and remove unnecessary human manual work.
- The user owns goals, prohibitions, protected-data access, external or costly actions, irreversible choices, and result confirmation.
- Agents own in-scope research, safe defaults, reversible implementation, proportionate validation, and failure recovery.
- Choose the lowest sufficient work class routed by `AGENTS.md`. Process is a safety tool, not a deliverable by itself.
- Ask only when the answer changes the authorized outcome, crosses a protected or external boundary, creates material irreversible risk, or cannot be resolved by a safe reversible default.

## Authority and scope

- Follow the user's latest instruction, then this file, then `SESSION_HANDOFF.md`, then the exact task owner.
- Work only toward the requested outcome. Do not add later-stage features or materially broader changes.
- Ask before deletion or move unless the exact targets are already approved; always ask before push, publish, upload, install, permission changes, paid actions, external writes, overwriting user originals, or unapproved commits.
- A traceable standing approval may cover a precise sequence when scope, exclusions, and gates remain unchanged.
- Preserve unrelated user changes and use Git history instead of ad hoc backup copies.

## Protected data and history

- A path segment named `inputs` or `outputs` is protected. Do not enumerate, open, hash, copy, summarize, index, or report it without the user's exact item and purpose.
- Filter protected segments before filesystem access. Framework inventory starts from `git ls-files`.
- `backup/` is immutable historical evidence. Read only exact user-authorized material and never use it as active instruction or runtime dependency.
- Never read or expose secrets, credentials, tokens, cookies, browser profiles, passwords, or private keys.

## Durable project knowledge

- Only material facts needed to resume, operate, audit, or reuse work require a maintained human-readable owner.
- Each material active fact has one owner. Link to it instead of copying it into handoff, reports, maps, records, or comments.
- Update the existing owner at the logical completion checkpoint with material decisions, results, blockers, validation state, and first next action. Do not preserve every command, retry, or transient observation.
- Machine-readable maintained data must be a deterministic document derivative or labeled read-only legacy. Temporary execution data may remain disposable and untracked.
- Create a maintained document only when no existing owner can serve its distinct durable purpose. One improvement initiative normally uses one plan·execution·report owner.

## Structure and current state

- `PROJECT_RULES.md` owns always-on policy; `rules/*.md` owns conditional procedures.
- `SESSION_HANDOFF.md` owns only the current work, blockers, verified state, and first next action. Completed history belongs to its stage owner and Git.
- `docs/build/` owns numbered build plans; `reports/` is point-in-time evidence; `failures/` is reusable resolved-failure knowledge.
- `inputs/` and `outputs/` remain outside framework version control.
- Current and historical documents may coexist, but default user and agent routes must clearly distinguish them.

## Verification and failures

- Validate in proportion to risk and at a logical change checkpoint, not after every file save.
- `quick` work uses direct targeted checks; `standard` work uses relevant tests and document checks; `controlled` work follows its explicit plan and consolidated gate.
- Distinguish generated, structure-validated, tool-validated, app-validated, and user-confirmed states. Unrun checks are not passes.
- Independent or multi-agent validation is used only when the user or exact active plan explicitly requires it.
- A corrected one-off command, quoting, or path mistake is transient unless it reveals a generalizable risk or materially blocks work.
- After three consecutive failures of the same objective, preserve the current blocker and evidence, change the approach, and continue inside the authorized scope. Stop only when safe progress needs new authority or an external state change.
