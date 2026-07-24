# Document-Based Data Work Rules

- Purpose: govern maintained documents and persistent project data without turning documentation into the work product.
- Read when: creating or changing maintained Markdown, root controls, records, events, snapshots, or indexes.
- Authority: task-specific; `PROJECT_RULES.md` remains higher authority.

## Rules

- Identify the existing canonical owner before a logical change. Record the owner decision in the task owner only when it is not obvious from the router.
- Create a document only for a distinct durable purpose that no existing owner serves. Keep one plan·execution·report owner for one initiative unless the user requests a separate artifact or a distinct long-lived reader requires it.
- Update `SESSION_HANDOFF.md` only when current work, a material blocker, verified state, or the first next action changes.
- For a maintained machine artifact, identify its document owner, rebuild command, and verification. Do not write it if that relationship is missing.
- Link to policy, procedure, and current state instead of copying them. User-facing guides and approval summaries use Korean; concise agent-only routing may use English.
- Validate a logical batch at its completion checkpoint: strict UTF-8, NUL 0, relevant structure and links, trailing whitespace, and the scoped diff.
- Run full maintenance only for controlled structural work or when the active plan requires it; otherwise use the smallest direct document checks that cover the change.
- Generated or structure-valid does not mean user-approved.
