# Document Work Rules

- Purpose: govern creation, editing, validation, and ownership of maintained project documents.
- Read when: before creating, editing, moving, classifying, or validating maintained Markdown or root control documents.
- Owner: user-approved policy; project agents maintain accepted wording.
- Authority: task-specific; `PROJECT_RULES.md` remains higher authority.

## Rules

- Identify the existing owner of each rule, state, plan, decision, or report before writing. Update that owner instead of creating a duplicate.
- Create a maintained document only when it has a unique durable purpose, a defined read condition, and no existing owner.
- Keep always-on rules in `PROJECT_RULES.md`, task rules in `rules/`, current state in `SESSION_HANDOFF.md`, durable resolved-failure knowledge in `failures/`, build plans in `docs/build/`, and point-in-time evidence in `reports/`.
- Write user-facing guides and approval summaries in Korean. Agent-facing rules and routing documents may use concise English.
- Link to an authority instead of copying its procedures or current state. Update `SESSION_HANDOFF.md` only when verified current state or the first next action changes.
- After every write, re-read the changed file and verify strict UTF-8, NUL 0, expected sections, relevant local links, trailing whitespace, and the final diff.
- Do not call a document user-approved merely because it was generated or structure-validated.
