# PROJECT_BOOTSTRAP.md

- Status: always-load kernel
- Purpose: keep session startup small while preserving the rules that can cause
  irreversible damage if missed.
- Full rule source: `PROJECT_RULES.md`
- Document router: `docs/INDEX.md`

## 1. Startup Load

Every agent session starts with this file, then `docs/INDEX.md`.

Do not load the whole project by default. Use `docs/INDEX.md` to choose only the
documents required for the current request.

Read any selected instruction document from the first line to the last line.
Do not rely on memory, summaries, prior handoffs, or partial excerpts when a
selected document controls the current task.

## 2. Full Rule Load Triggers

Read the full `PROJECT_RULES.md` before continuing when the task involves any of
the following:

- changing rules, standard entrypoints, document structure, skills, or tools
- deleting, moving, overwriting, or preserving important files
- commit, publish, upload, deploy, external write, permission, or credential risk
- security, secrets, browser/session data, API keys, tokens, cookies, or auth
- Stop Rule, repeated failure, verification level, or backup decisions
- conflict between documents, user instructions, tool output, or prior state
- uncertainty about whether a rule applies

If `PROJECT_RULES.md` is required but cannot be read completely, stop and report
that the mandatory full rule source is unavailable.

## 3. Hard Rules Kept In Startup Context

- Work only inside the assigned project scope unless the user explicitly asks
  otherwise.
- Never read, expose, copy, or summarize secrets.
- Do not perform external writes without explicit approval.
- Do not delete, move, or overwrite important files without explicit user intent.
- State the edit scope before modifying existing files.
- Prefer structured validation over assuming tool success means task success.
- Korean is the default report language.

## 4. Stop Rule

If the same objective fails 3 times in a row, stop. Report:

1. the last confirmed cause
2. the risk of continuing
3. what to re-research

Then wait for the user's decision.

Do not keep trying alternate commands, alternate implementations, or workaround
paths after this stop condition triggers.

## 5. Conditional Context

Use `docs/INDEX.md` to decide what to read next.

| Situation | Read next |
|---|---|
| Continuing existing work | `SESSION_HANDOFF.md`, then `CURRENT_TASK.md` |
| Current task details needed | `CURRENT_TASK.md` |
| Project structure or docs change | `PROJECT_RULES.md`, `docs/AGENT_MAINTENANCE.md` |
| Workflow-stage decision | `01_유튜브_제작_워크플로우.md` |
| Specific stage work | the relevant stage document or `skills/*/SKILL.md` |
| Tool execution | `tools/README.md`, then the specific tool help |
| Long research or diagnosis | only the relevant report listed in `docs/INDEX.md` |

## 6. End Check

Before reporting completion after document, skill, tool, or structure changes:

1. confirm the latest user request was actually answered
2. check that changed docs do not conflict with each other
3. run `tools\run_doccheck.bat`
4. run `git diff --check`
5. report what was verified and what was not

This file is a loader, not a replacement for `PROJECT_RULES.md`. Keep it short.
