# PROJECT_RULES.md

- Role: current project operating rules and single source of truth.
- Read when: every session, immediately after `AGENTS.md`.
- Retention: permanent; change only when the user changes project policy.
- Priority: security > user data boundaries > accuracy > efficiency.

## Scope

- This Git repository stores reusable framework rules, code, contracts, tests, documentation, and
  verified rebuild stage records under `docs/rebuild/`.
- `backup/` is historical and read-only. Inspect only the routed framework file needed for the task.
- Do not create a second rule source. Stage documents link here and contain only stage-specific deltas.

## User Data Boundary

- Any path segment named `inputs` or `outputs` is user/task data, not framework material.
- Never enumerate, open, hash, copy, summarize, index, report, store, stage, or commit those trees or
  their per-file metadata. This includes paths, names, counts, sizes, hashes, previews, transcripts,
  and derived inventories under `backup/inputs` or `backup/outputs`.
- Framework inventory starts from `git ls-files`, then excludes forbidden path segments before any
  filesystem access. It never starts with recursive filesystem discovery.
- Per-video artifacts and reports remain outside framework version control. Verified framework rebuild
  reports are different: keep them under `docs/rebuild/stage-XX/` as tracked project history.
- Do not promote user artifacts by renaming or copying; extract only input-independent reusable logic
  into framework paths.
- An exception requires a new, explicit user request naming the exact material and purpose. General
  permission to proceed, diagnose, test, or rebuild is not an exception.

## Safety And Git

- Never read or expose secrets, credentials, tokens, cookies, browser profiles, or private keys.
- Do not modify `backup/` or original user material.
- Ask before delete, move, external write, upload, publish, install, permission change, commit, tag,
  push, worktree creation, or paid action unless the user explicitly authorized that exact action.
- Preserve unrelated user changes. Track verified `docs/rebuild/` stage records. Create validation
  worktrees and runtime temporary directories outside the repository and remove them after use.
- Build the actual project from the repository root (`pyproject.toml`, `src/`, `tests/`, hooks, CI),
  never inside a stage-document or ignored directory. Do not commit without explicit user approval.

## Document Read/Write

- Startup order: `AGENTS.md` -> `PROJECT_RULES.md` -> `SESSION_HANDOFF.md` ->
  `docs/improvement/LAYER_PLAN.md` -> the current layer section only.
- `docs/rebuild/` (9-stage rewrite plan and its stage documents) is deprecated history
  as of 2026-07-18. Do not route execution through it.
- Read only the routed documents. Do not bulk-read `backup/`, old reports, or unrelated stages.
- Keep one rule in one source; other documents link to it instead of copying it.
- Root handoff records only current state, first next action, blockers, and links. It does not duplicate
  procedures or historical narrative.
- New operational text must either prevent a repeated failure or reduce future reading/writing work.

## Test Execution Policy (user directive, 2026-07-17)

- Run the test suite once per stage as a single consolidated pass at the stage
  verification step, not repeatedly during development. Quick compile/import sanity
  checks while writing code are allowed; full `workflow check` runs are per-stage.
- Prioritize rebuild implementation speed over intermediate re-verification.
- Stage completion still requires that single consolidated run to pass; failures are
  fixed and the consolidated run is repeated, and never reported as success.

## Verification And Reporting

- After every write, re-read the changed file, verify UTF-8, NUL bytes, expected content, and links.
- For policy changes, search all active documents and generated evidence for stale conflicting text.
- Report generated, parsed, structure-validated, tool-validated, app-validated, and user-approved
  states separately. Unrun work is pending, not failed; pending work is not a blocker unless required.
- Stop after three consecutive failures of the same objective within one user execution request.
- Korean is the default user-facing language. Framework entry documents may use concise English.
