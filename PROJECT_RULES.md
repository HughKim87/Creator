# Project-Wide Rules

- Purpose: Define the rules that always apply to every task in this project.
- Scope: Data protection, workspace boundaries, authorization, document governance, validation, and failure reporting.
- Audience and language: Agents; English.
- Read when: Before any task that reads or changes this workspace.
- Write when: Only when the user approves a project-wide rule change.
- Authority: This is the sole source of project-wide rules. Rebuild principles, work plans, workflow rules, and current state belong elsewhere.

## Priorities

1. Protect user data.
2. Preserve correctness and evidence.
3. Prefer the simplest adequate solution.
4. Optimize speed only after the first three priorities are satisfied.

## Document governance

- Read only the documents routed by `AGENTS.md` for the current task.
- Obey each document's top-level purpose, scope, read condition, and write condition.
- Agent execution documents are written in English. Documents created for user review or reporting are written in Korean.
- Every active document starts with its purpose and scope. Historical documents must say that they are not execution sources.
- Keep one authoritative source for each rule, state, plan, or decision. Other documents link to it rather than copying it.
- Do not create a document unless it prevents a repeated failure, preserves a durable decision, or reduces repeated work.
- Keep current task state in `SESSION_HANDOFF.md`. `PROJECT_STATUS.md` is a Korean user-facing derivative, not a second state source.

## Workspace and data boundaries

Do not enumerate, open, copy, summarize, hash, index, or report user data without a user-specified item and purpose.

| Path or asset | Owner | Default read | Default write | Git | Move or delete |
|---|---|---|---|---|---|
| `inputs/` | User originals | Only the item named by the user | Never overwrite originals; write derivatives to `outputs/` | Never | Only with an explicit user request |
| `outputs/` | User work results | Only the named task scope | Only derivatives and task state for the named work | Never | Only with an explicit user request |
| `backup/` | Preserved project history | Only files selected by the active task document | Never | Preserve existing tracking; do not create duplicate backups | Never during normal work |
| Root, `docs/`, future `tools/`, `skills/`, `tests/` | Reusable framework | Only task-relevant files | Input-independent assets within the approved task scope | Eligible; stage or commit only when requested | Only with an explicit user request |
| `.git/`, `.agents/`, `.codex/` | Tool metadata | Only settings needed for the task | No direct edits; use approved tool operations | Not applicable | No direct move or delete |
| Temporary files and caches | Current execution | Only when needed | Outside the repository or in an already ignored path | Never | Clean only items created by the current task |

- Keep originals and derivatives separate.
- Never store video-, channel-, person-, or episode-specific facts in reusable framework files.
- Reuse unchanged results. When inputs or decisions change, create a new version and preserve the prior result unless the user requests cleanup.
- Do not write temporary files or runtime caches into the repository.

## Naming and path handling

- Preserve the existing Korean project path and existing user filenames. Do not rename them retroactively.
- Use `lower_snake_case` and lowercase ASCII for new internal keys, code identifiers, and command names.
- When a tool-facing ID or filename needs a portable form, use `[a-z0-9][a-z0-9._-]*` and keep it separate from the user-facing display name.
- Do not force ASCII naming onto user-owned files or user-facing text.
- Pass existing Unicode and spaced paths as literal paths. Do not rebuild them through unsafe string concatenation.

## Authorization and change safety

- Delete, move, install, commit, push, publish, upload, send externally, or change permissions only within the user's explicit request.
- Preserve unrelated user changes in the working tree.
- Never overwrite user originals or automatically delete previous results.
- Use deterministic tools for repeatable extraction, transformation, and validation. Use AI for candidates, interpretation, and explanation.
- Tool completion is not equivalent to content quality, application validation, or user approval.
- The user makes final content, editing-direction, approval, upload, and external-release decisions.

## Validation and reporting

- Distinguish `generated`, `parsed`, `structure-validated`, `tool-validated`, `app-validated`, and `user-validated` states.
- After writing a file, verify UTF-8 validity, absence of NUL bytes, expected content, and relevant internal links.
- During implementation, run only necessary fast checks. Run one integrated validation at task or layer completion.
- Confirm both a command's exit code and its expected result. Non-zero exits, exceptions, missing dependencies, or partial output are failures.
- Wrappers preserve child-process failure codes. A completion message or file existence alone is not proof of success.
- Report unavailable checks as `unverified` and advisory-only results as `advisory`; neither is a pass.
- Do not promote partial output to current or approved status. Record the cause and restart condition.
- After three consecutive failures on the same objective, stop and report the cause, risk, and minimum next choices.
