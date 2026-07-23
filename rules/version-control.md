# Version-Control Work Rules

- Purpose: govern Git writes, recovery, and backup decisions.
- Read when: before staging, committing, branching, pushing, recovering, or creating a backup copy.
- Authority: task-specific; `PROJECT_RULES.md` remains higher authority.

## Rules

- Git writes require traceable user approval for the exact action or a standing sequence with scope, exclusions, and boundaries.
- A commit is required only when the user or active controlled plan defines that boundary. Do not invent micro-commits for `quick` work.
- Query branch and worktree at execution time. Preserve unrelated changes and review the exact diff before staging.
- Stage only approved paths. Never stage or commit `inputs`, `outputs`, secrets, or unrelated user changes.
- Do not branch, push, publish, destructively restore, or overwrite user work without the action's explicit authority.
- Use Git history instead of duplicate backup files unless the user requests another backup.
- On Windows, pass a repository `safe.directory` override as one quoted `key=value` argument when the absolute path contains spaces; do not split that path across command arguments.
- After a Git write, verify the object, affected paths, protected-path count, and resulting status.
- If a required commit fails, do not cross the boundary; fix it inside the approved scope or report the blocker.
