# Version-Control Work Rules

- Purpose: govern staging, commits, branches, pushes, recovery, and framework backup decisions.
- Read when: before any Git write, recovery action, or decision to create a backup copy.
- Owner: user-approved policy; project agents maintain accepted wording.
- Authority: task-specific; `PROJECT_RULES.md` remains higher authority.

## Rules

- Obtain traceable user approval for Git writes. Approval may be one exact action or a standing policy that identifies the boundary, included scope, and exclusions.
- Current standing policy: starting with Stage 03, after every numbered stage passes its success gate and final score, commit all verified non-protected framework changes accumulated through that stage before beginning the next stage.
- The first Stage 03 boundary commit may include still-uncommitted Stage 01, Stage 01.5, and Stage 02 changes. Stage 04 onward uses one boundary commit per stage.
- This standing commit approval does not approve push, branch creation, destructive recovery, backup copies, protected data, secrets, or unrelated user changes.
- Query branch, worktree, and remote state at execution time; do not preserve dynamic Git facts as long-lived project state.
- Preserve unrelated changes. Review the exact diff and stage only the approved framework paths.
- Never stage or commit any path containing an `inputs` or `outputs` segment or any secret-bearing file.
- Do not use destructive reset or restore operations on user changes without explicit authorization.
- Do not create ad hoc duplicate backup files. Use version history unless the user explicitly approves another backup method.
- After a Git write, verify the resulting status, object, and affected paths before reporting success.
- If the required boundary commit fails, keep the next stage unstarted, record the failure, fix it within the approved scope, and retry the commit gate.
