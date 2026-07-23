# Failure-Record Work Rules

- Purpose: preserve only material, reusable failure knowledge and keep active blockers separate.
- Read when: recording or reusing a generalizable failure, or managing a repeated unresolved blocker.
- Authority: task-specific; `PROJECT_RULES.md` remains higher authority.

## Durable threshold

Create or update `failures/*.md` only when the cause and resolution are verified and at least one is true:

- the same root cause recurred;
- it can plausibly affect future correctness, safety, protected data, or recovery;
- the fix is non-obvious and reusable;
- the failure materially blocked the task or required a changed approach.

A corrected one-off typo, quoting error, wrong option, path assumption, expected negative test, or transient tool issue does not require a durable record unless it meets that threshold. Mention it in the active task owner only when it affected the result or schedule.

## Rules

- Keep a currently blocking failure, consecutive count, immediate risk, and restart condition in `SESSION_HANDOFF.md`; remove it when the blocker is verified resolved.
- At three consecutive failures of the same objective, preserve the peak evidence, change the method, and continue within the authorized scope.
- Search `failures/README.md` before creating a case. Merge a recurrence into the same root-cause owner only when it adds useful prevention or material recurrence evidence.
- A durable case states the symptom, confirmed cause, material failed attempts, resolution, verification, prevention, and safe references. Do not copy raw logs, secrets, or protected/user-original content.
- Existing legacy failure records remain read-only history. Canonical cases are Markdown and must not create per-case projections.
- Before controlled-task completion, ensure unresolved material blockers are not called solved and durable failures that meet the threshold are not omitted.
- When a failure Markdown changes, validate that document and its links. Update `failures/README.md` only when a case is added, removed, or renamed.
