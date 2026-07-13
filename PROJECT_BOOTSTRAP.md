# PROJECT_BOOTSTRAP.md

- Always load this file, then `docs/INDEX.md`.
- Full rules live in `PROJECT_RULES.md` and are loaded only when needed.
- Keep startup context small; use the index to select task documents.
- Goal: reusable AI-agent video workflow for many videos, not one-off notes.
- Optimize for context economy, repeatable stages, verified outputs, and fewer
  repeated mistakes.

## Startup

- Read selected instruction documents to the end.
- Do not rely on memory, summaries, or partial excerpts for controlling docs.
- If a required rule file cannot be read, stop and report the missing file.

## Load Full Rules When

Open `PROJECT_RULES.md` before work involving:

- rules, entrypoints, document structure, skills, or tools
- deletion, movement, overwrite, commit, external write, permission, or security
- secrets, auth, browser/session data, API keys, tokens, cookies
- repeated failure, Stop Rule, verification, backup, or conflicting instructions
- uncertainty about whether a rule applies

## Hard Rules

- Work inside the assigned project scope.
- Never read, expose, copy, or summarize secrets.
- Ask before irreversible actions: delete, overwrite, external write, upload,
  publish, commit, permission change, or paid action.
- Reversible edits and local validation are allowed; report what changed.
- After writing a file, verify NUL bytes and expected content. Restore corrupt
  files from Git before continuing.
- Korean is the default report language.

## Stop Rule

If the same objective fails 3 times in a row, stop. Report the last confirmed
cause, the risk of continuing, and what to re-research. Then wait.

## Route

| Situation | Read |
|---|---|
| Continuing work | `SESSION_HANDOFF.md`, then `outputs/SESSION_HANDOFF.md` when present |
| Project docs/rules/tools change | `PROJECT_RULES.md`, `docs/AGENT_MAINTENANCE.md` |
| Workflow decision | `01_youtube_production_workflow.md` |
| Stage work | relevant `skills/*/SKILL.md` or stage document |
| Tool use | `tools/README.md`, then specific tool help |
| Research/background | only the relevant indexed report |

## Finish Check

For document, skill, tool, or structure changes, run `tools\run_doccheck.bat`
and `git diff --check`, then report verification gaps.
