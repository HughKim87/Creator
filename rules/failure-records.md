# Failure-Record Work Rules

- Purpose: preserve resolved failures as reusable cross-stage knowledge and keep active failure state separate from durable knowledge.
- Read when: before closing a numbered stage, or before recording, diagnosing, resolving, reviewing, or reusing a failure.
- Owner: user-approved policy; project agents maintain accepted wording.
- Authority: task-specific; `PROJECT_RULES.md` remains higher authority.

## Rules

- Keep unresolved attempts, the current consecutive count, the immediate risk, and the restart condition in `SESSION_HANDOFF.md` while work is active.
- A failure becomes durable knowledge only after its cause and resolution are confirmed by a successful verification. Do not label a workaround or an unverified guess as resolved.
- Store resolved failure knowledge under `failures/`. The originating stage or task is provenance, not the owner of the knowledge.
- Search `failures/README.md` and the relevant case titles before creating a file. When the same root cause recurs, update the existing case with the new occurrence and verification instead of creating a duplicate.
- Each case must state the symptom, context, failed attempts and peak consecutive count when known, confirmed cause, resolution, verification level and evidence, prevention or reuse rule, recurrence history, and safe source references.
- Do not copy secrets, protected `inputs/` or `outputs/` content, user originals, or unnecessary raw output into a failure case. Record only the minimum safe evidence needed to reproduce the reasoning.
- At stage closure, reconcile every failure encountered during that stage. Every resolved failure must create or update a durable case; every unresolved failure must remain an active blocker in `SESSION_HANDOFF.md`.
- If a stage had no failures, record that fact in the stage's final review; do not create an empty case file.
- A stage cannot receive `완료 준비` while a resolved failure is omitted, a duplicate root-cause case is knowingly created, or an unresolved failure is described as solved.
- After reconciliation, update the navigation index in `failures/README.md`, verify local links and strict UTF-8, and link the stage closure evidence to the index rather than copying case bodies into stage documents.
