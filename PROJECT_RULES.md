# Always-On Project Rules

- Purpose: define only the minimum cross-task rules that always apply in this project.
- Read when: once at the start of every new conversation or session, immediately after `AGENTS.md`.
- Change authority: the user approves policy changes; project agents may maintain wording within an approved change.
- Priority: security > user-data protection > accuracy > efficiency.

## Project purpose and operating model

- The project's top-level purpose is to maximize productive agent autonomy so work can proceed without human manual execution.
- The file-based knowledge system is a means to let an agent reconstruct intent, scope, evidence, state, and methods accurately without chat memory; it is not the final purpose by itself.
- The user owns goals, prohibitions, protected-data access, external or costly actions, irreversible choices, and result confirmation. Agents own in-scope research, reasonable reversible decisions, implementation, validation, failure recovery, and concise progress reporting.
- Report material choices, scope effects, failures, gate results, and remaining risk. Request user input only when the answer changes the authorized outcome, crosses a protected or external boundary, creates material irreversible risk, or cannot be resolved by a safe reversible default.

## Document-based data and execution

- Every durable project datum used to understand, plan, execute, verify, resume, or audit work must have exactly one human-readable maintained document as its active canonical owner.
- Start work by reading the exact canonical documents routed by `AGENTS.md`. Before treating work as complete, update the existing document owners with every material requirement, decision, evidence reference, result, failure, validation state, blocker, and first next action produced by the work.
- Source code and configuration may implement the project, but they must not be the sole owners of project intent, requirements, current state, decisions, work evidence, or reusable knowledge.
- JSON, JSONL, schemas, records, events, snapshots, indexes, inventories, caches, and other machine-readable files may persist only when they are deterministic derivatives of document owners or explicitly labeled read-only legacy history. They must not own an active fact that is absent from its canonical document.
- Before creating or changing persistent machine-readable data, identify its canonical document owner and the trace or rebuild relationship. If neither exists, create or update the document owner first; otherwise record the gap as a blocker and do not claim completion.
- Existing machine-readable authorities that violate this model are migration debt, not precedent. Preserve them until an approved migration verifies no information loss, but do not add new active facts that exist only in those files.
- Temporary execution data may remain outside maintained documents only when it is disposable, is not used to resume or audit later work, and is not treated as project knowledge or current state.

## Rule classification

- Always-on rules live only in this `PROJECT_RULES.md` and are read once at session start.
- Task rules live in `rules/*.md` and are never part of the default startup set.
- Before a task begins, use the direct routing table in `AGENTS.md` and read every rule file whose task action matches. Read each selected file completely and once per task.
- A task rule may narrow execution but cannot weaken an always-on safety, authority, or protected-data boundary.
- Do not copy the same rule into both classes. Keep it in the narrowest class that still applies every time it is needed.

## Authority and scope

- Follow the user's latest explicit instruction first, then this file, then `SESSION_HANDOFF.md`, then the task-specific authority it routes to.
- Work only within the user's requested outcome and approved stage. Do not infer authority for a later stage or materially broader change.
- Ask before delete, move, push, publish, upload, install, permission changes, paid actions, external writes, overwriting user originals, or any commit not covered by traceable explicit or standing user approval.
- Reconfirm an approval when its target, scope, or risk materially changes, or when the original user response cannot be traced.
- Inside an approved outcome, choose safe reversible implementation details and recommended defaults autonomously. Record the reason and verification instead of turning ordinary implementation uncertainty into human manual work.
- A standing approval may cover a precisely identified sequence of stages when every stage still passes its own success gate, reports the result, and stops if the scope or risk changes.

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
- For one improvement initiative, keep diagnosis, plan, execution evidence, scoring, and external read-only review in one stage owner unless an artifact has a distinct long-lived reader or authority.

## Context

- The required startup set is `AGENTS.md`, `PROJECT_RULES.md`, and `SESSION_HANDOFF.md`, read once per new session rather than before every message.
- After startup, read only the matching task rules and exact task authority. Do not bulk-read rule packs, reports, plans, or historical material.

## Change safety and verification

- Preserve unrelated user changes.
- Verify changes in proportion to risk and follow the exact checks in the selected task rules.
- Distinguish generated, structure-validated, tool-validated, app-validated, and user-approved states. Unrun checks and unimplemented features are not passes.
- When a validation subagent is required, use one fresh subagent for that validation task with no inherited conversation or prior-task context. Give it only the current requirements and scope, the final artifacts or diff, completed test evidence, declared unresolved risks, and the validation contract. Do not disclose prior findings, fix history, retry history, or a desired verdict. Use the result only for read-only cross-validation.
- After three consecutive failures of the same objective, record the attempts, confirmed cause, peak count, risk, and restart condition; change the approach and continue within the already authorized scope without requesting separate approval. Stop only when safe progress is impossible or continuation requires new authority, protected data, installation, external publication, or another material scope expansion.
