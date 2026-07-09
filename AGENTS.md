# AGENTS.md

Codex instruction entry point.

## Mandatory Bootstrap Load Gate

Before doing anything else, read `PROJECT_BOOTSTRAP.md` in this directory from
the first line to the last line and use it as the startup instruction source for
this project.

Do not rely on memory, summaries, prior session handoffs, or partial excerpts of
`PROJECT_BOOTSTRAP.md`. If the file cannot be read, stop and report that the
mandatory bootstrap source is unavailable.

After `PROJECT_BOOTSTRAP.md` is fully read, follow `docs/INDEX.md` routing
rules and load `PROJECT_RULES.md` only when the bootstrap trigger conditions
require the full rule source. Do not add rules here; edit
`PROJECT_BOOTSTRAP.md` or `PROJECT_RULES.md` instead.
