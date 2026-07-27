# Document-Based Data Work Rules

- Purpose: govern maintained documents and persistent project data without turning documentation into the work product.
- Read when: creating or changing maintained Markdown, root controls, records, events, snapshots, or indexes.
- Authority: task-specific; `PROJECT_RULES.md` remains higher authority.

## Rules

- Before writing, define the exact artifact budget: owner, path, purpose, reader, and number of files.
- A request for only a report authorizes only that report. Analysis does not authorize implementation, rule or skill changes, sidecar proposals, or additional persistent artifacts.
- Before writing, identify the canonical owner. Update it instead of creating a file unless a distinct durable purpose or reader requires one.
- Keep one plan·execution·report owner per initiative unless the user requests a separate artifact.
- Update `SESSION_HANDOFF.md` only when current work, a material blocker, verified state, or the first next action changes. Remove completed task detail from the startup path.
- For a maintained machine artifact, identify its document owner, rebuild command, and verification. Do not write it if that relationship is missing.
- Link to policy, procedure, and current state instead of copying them. User-facing guides and approval summaries use Korean; concise agent-only routing may use English.
- Plans and reports retain decisions, authorized scope, success gates, unresolved risks, and the next executable action. Do not copy source narratives, file-by-file implementation detail, or completed history that Git already preserves.
- Before completion, compress text that does not change a future action, resumability, verification, or audit decision.
- Validate a logical batch at its completion checkpoint: strict UTF-8, NUL 0, relevant structure and links, trailing whitespace, and the scoped diff.
- Run full maintenance only for controlled structural work or when the active plan requires it; otherwise use the smallest direct document checks that cover the change.
- Generated or structure-valid does not mean user-approved.
