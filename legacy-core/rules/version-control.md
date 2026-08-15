# Version-Control Work Rules

- Purpose: govern Git writes, recovery, and backup decisions.
- Read when: before staging, committing, branching, pushing, recovering, or creating a backup copy.
- Authority: task-specific; `PROJECT_RULES.md` remains higher authority.

## Rules

- Git writes require traceable user approval for the exact action or a standing sequence with scope, exclusions, and boundaries.
- A commit is required only when the user or active controlled plan defines that boundary. Do not invent micro-commits for `quick` work.
- Query branch and worktree at execution time. Preserve unrelated changes and review the exact diff before staging.
- Before restore, clean, or overwrite touches another session's uncommitted change, resolve the exact target, inspect its diff, verify a usable recovery copy, and confirm current user approval for that destructive action. If any condition is missing, leave the change untouched.
- Stage only approved paths. Never stage or commit `inputs`, `outputs`, secrets, or unrelated user changes.
- Do not branch, push, publish, destructively restore, or overwrite user work without explicit authority for that action.
- Use Git history instead of duplicate backup files unless the user requests another backup.
- On Windows, pass a repository `safe.directory` override as one quoted `key=value` argument when the absolute path contains spaces; do not split that path across command arguments.
- After a Git write, verify the object, affected paths, protected-path count, and resulting status.
- If a required commit fails, do not cross the boundary; fix it inside the approved scope or report the blocker.

## Requested backup completion

- Classify the request as a copy, move, or recovery snapshot before acting. These outcomes are not interchangeable.
- Resolve the exact source set and destination. Place a requested file backup outside the active repository; an in-repository backup snapshot is prohibited by higher policy.
- Verify the backup with source and destination counts plus size or hashes appropriate to the data.
- A copy is not completion when the user requested the active paths to be moved or cleared. After exact approval for that destructive step, verify the intended active paths are absent and recheck repository status.
- Maintained files, rules, and runtime behavior must not depend on the backup. Removing the backup later must not break the improved project.
