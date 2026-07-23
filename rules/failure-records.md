# Failure-Record Work Rules

- Purpose: preserve resolved failures as reusable cross-stage knowledge and keep active failure state separate from durable knowledge.
- Read when: before closing a numbered stage, or before recording, diagnosing, resolving, reviewing, or reusing a failure.
- Owner: user-approved policy; project agents maintain accepted wording.
- Authority: task-specific; `PROJECT_RULES.md` remains higher authority.

## Rules

- Keep unresolved attempts, the current consecutive count, the immediate risk, and the restart condition in `SESSION_HANDOFF.md` while work is active.
- When the same objective reaches three consecutive failures, preserve the peak count and failure evidence, change the method based on the confirmed cause, and resume without a separate approval when the work remains inside the user's already authorized scope.
- A failure becomes durable knowledge only after its cause and resolution are confirmed by a successful verification. Do not label a workaround or an unverified guess as resolved.
- Store resolved failure knowledge under `failures/`. The originating stage or task is provenance, not the owner of the knowledge.
- Keep each `failures/*.md` case as the human-readable and machine-parsed canonical body. Runtime validation and context retrieval parse this owner directly and must not require a per-case source, projection, or lifecycle file.
- Existing Stage 05 `failure_knowledge` records and related source/lifecycle data are legacy history. Preserve them for compatible direct reads, but do not create or refresh them for canonical failure maintenance.
- Search `failures/README.md` and the relevant case titles before creating a file. When the same root cause recurs, update the existing case with the new occurrence and verification instead of creating a duplicate.
- A failure event, recurrence, or verified resolution triggers recording; the number of corrective changes or modified files does not. Before reporting completion, classify every failure encountered in scope as unresolved, a recurrence of an existing root cause, or a newly confirmed root cause.
- Reconcile failure knowledge in the same task after successful verification and before reporting completion: unresolved failures remain in `SESSION_HANDOFF.md`, recurrences update their existing case, and newly confirmed causes create a case. The case, link-only index, and direct parser/maintenance validation are completion evidence.
- Each case must state the symptom, context, failed attempts and peak consecutive count when known, confirmed cause, resolution, verification level and evidence, prevention or reuse rule, recurrence history, and safe source references.
- Do not copy secrets, protected `inputs/` or `outputs/` content, user originals, or unnecessary raw output into a failure case. Record only the minimum safe evidence needed to reproduce the reasoning.
- At stage closure, reconcile every failure encountered during that stage. Every resolved failure must create or update a durable case; every unresolved failure must remain an active blocker in `SESSION_HANDOFF.md`.
- If a stage had no failures, record that fact in the stage's final review; do not create an empty case file.
- A stage cannot receive `완료 준비` while a resolved failure is omitted, a duplicate root-cause case is knowingly created, or an unresolved failure is described as solved.
- Repeated failure never waives safety or authority boundaries. Pause only when the next meaningful action needs new permission, protected data, installation, external publication, or a material scope change.
- After reconciliation, update the navigation index in `failures/README.md`, verify local links and strict UTF-8, and link the stage closure evidence to the index rather than copying case bodies into stage documents.
- When a failure Markdown file changes, validate the canonical document directly and confirm it is searchable without creating a per-case projection. Legacy projection drift is historical metadata and must not block the canonical owner.
