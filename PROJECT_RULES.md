# Always-On Project Rules

- Purpose: define only the minimum cross-task rules that always apply in this project.
- Read when: once at the start of every new conversation or session, immediately after `AGENTS.md`.
- Change authority: the user approves policy changes; project agents may maintain wording within an approved change.
- Priority: security > user-data protection > accuracy > efficiency.

## Rule classification

- Always-on rules live only in this `PROJECT_RULES.md` and are read once at session start.
- Task rules live in `rules/*.md` and are never part of the default startup set.
- Before a task begins, use the direct routing table in `AGENTS.md` and read every rule file whose task action matches. Read each selected file completely and once per task.
- A task rule may narrow execution but cannot weaken an always-on safety, authority, or protected-data boundary.
- Do not copy the same rule into both classes. Keep it in the narrowest class that still applies every time it is needed.

## Authority and scope

- Follow the user's latest explicit instruction first, then this file, then `SESSION_HANDOFF.md`, then the task-specific authority it routes to.
- Work only within the user's requested outcome and approved stage. Do not infer authority for a later stage or materially broader change.
- Ask before delete, move, commit, push, publish, upload, install, permission changes, paid actions, external writes, or overwriting user originals.
- Reconfirm an approval when its target, scope, or risk materially changes, or when the original user response cannot be traced.

## Protected data and history

- A path segment named `inputs` or `outputs` is protected user or task data. Do not enumerate, open, hash, copy, summarize, index, or report it unless the user identifies the exact item and purpose.
- Filter protected path segments before filesystem access. Framework inventory starts from `git ls-files`, never from recursive discovery.
- `backup/` is immutable historical evidence, not an active instruction or runtime source. Read only the exact historical material needed for a user-authorized purpose; never modify, migrate, or depend on it.
- Never read, expose, copy, or summarize secrets, credentials, tokens, cookies, browser profiles, passwords, or private keys.

## Project structure and ownership

- The repository root contains startup controls, repository configuration, and dedicated top-level ownership folders defined below.
- `PROJECT_RULES.md` owns always-on rules. `SESSION_HANDOFF.md` owns verified current state and the first next action.
- `rules/` owns task-specific rules selected through `AGENTS.md`; these files are not read at session startup.
- `failures/` owns durable cross-stage knowledge for failures whose causes, resolutions, and verification are confirmed. The current unresolved attempt count and restart condition remain in `SESSION_HANDOFF.md`.
- `docs/build/` owns the approved build order and stage plans. `reports/` contains point-in-time evidence, not active execution instructions.
- `inputs/` and `outputs/` remain outside framework version control. Do not promote task-specific facts into reusable project files.
- Keep one active owner for each rule, state, plan, or decision. Link to the owner instead of copying its content.
- Create a maintained file only when it has a unique durable purpose that an existing owner cannot serve.

## Context

- The required startup set is `AGENTS.md`, `PROJECT_RULES.md`, and `SESSION_HANDOFF.md`, read once per new session rather than before every message.
- After startup, read only the matching task rules and exact task authority. Do not bulk-read rule packs, reports, plans, or historical material.

## Change safety and verification

- Preserve unrelated user changes.
- Verify changes in proportion to risk and follow the exact checks in the selected task rules.
- Distinguish generated, structure-validated, tool-validated, app-validated, and user-approved states. Unrun checks and unimplemented features are not passes.
- Within one user execution request, stop after three consecutive failures of the same objective and report the cause, risk, and restart condition.
