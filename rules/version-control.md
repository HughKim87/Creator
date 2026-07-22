# Version-Control Work Rules

- Purpose: govern staging, commits, branches, pushes, recovery, and framework backup decisions.
- Read when: before any Git write, recovery action, or decision to create a backup copy.
- Owner: user-approved policy; project agents maintain accepted wording.
- Authority: task-specific; `PROJECT_RULES.md` remains higher authority.

## Rules

- Obtain explicit user approval for the exact commit, push, branch, destructive recovery, or backup action before execution.
- Query branch, worktree, and remote state at execution time; do not preserve dynamic Git facts as long-lived project state.
- Preserve unrelated changes. Review the exact diff and stage only the approved framework paths.
- Never stage or commit any path containing an `inputs` or `outputs` segment or any secret-bearing file.
- Do not use destructive reset or restore operations on user changes without explicit authorization.
- Do not create ad hoc duplicate backup files. Use version history unless the user explicitly approves another backup method.
- After a Git write, verify the resulting status, object, and affected paths before reporting success.
