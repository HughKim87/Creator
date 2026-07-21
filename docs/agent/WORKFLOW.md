# Common Work Workflow

- Purpose: Define the common procedure for scoping, executing, validating, reporting, and handing off project work.
- Use when: For every project task after startup routing; combine it with the task-specific contract selected through the document map.
- Owner: Project agents maintain the procedure; stage gates and user authority remain controlled by the user and project rules.
- Language: English.
- Location: `docs/agent/WORKFLOW.md`. Governed by [PROJECT_RULES.md](../../PROJECT_RULES.md), routed through [DOCUMENT_MAP.md](DOCUMENT_MAP.md), and closed through [SESSION_HANDOFF.md](../../SESSION_HANDOFF.md).

## 1. Start and route

1. Complete the startup sequence in [AGENTS.md](../../AGENTS.md).
2. Read the current handoff and identify the first unstarted action.
3. Use [DOCUMENT_MAP.md](DOCUMENT_MAP.md) to open only the task-specific authorities required.
4. Separate the user's requested outcome, authorized actions, exclusions, approval boundaries, and validation expectation.
5. Confirm that protected paths are excluded before any inventory or search.

## 2. Establish the evidence state

Before changing files, distinguish:

- confirmed current facts from repository or primary output;
- historical claims that have not been rerun;
- inferences that need supporting facts;
- proposed decisions that still need approval;
- accepted decisions that control implementation.

Prefer read-only checks and direct file routes. Do not broaden a search merely to collect context.

## 3. Plan the smallest complete change

1. Identify the authoritative file for each intended change.
2. Preserve unrelated user changes and historical material.
3. Define a validation method before implementation.
4. For staged work, mark the current stage boundary and do not include later-stage implementation.
5. Use reversible local edits. External or destructive actions require explicit authority.

### Document creation gate

Before creating any maintained document, all of the following must pass:

1. Search the document map for an existing owner and current proposal for the same subject.
2. If either exists, update it in place; a stage number, agent name, review pass, or rewritten wording is not a distinct purpose.
3. If a new file is still necessary, state its unique purpose, authority class, preservation state, default-context behavior, and why no existing owner can hold it.
4. Register the file in the document map in the same change.
5. For a point-in-time report, include only the unique delta, evidence, validation, unresolved risk, and approval boundary. Link to owned rules, designs, and procedures without restating them.

The gate fails if another current proposal for the subject exists, if the new file repeats an existing owner's content, or if preservation can be satisfied by Git history and a short marker.

## 4. Execute and record

- Modify active project files only within the approved scope.
- Keep policies, procedures, technical contracts, current state, and reports in their owning documents.
- Update an existing owner or current proposal in place when the subject is unchanged. A new stage label alone does not justify a new document.
- Create a new report only for unique point-in-time evidence. Keep it to the stage delta, sources, actual validation, unresolved risk, and approval boundary; link to owners instead of repeating full rules, procedures, or designs.
- Allow only one current proposal per subject. Mark a replaced proposal as superseded evidence and exclude it from default context; use verified Git commit, blob, and content hashes to preserve duplicate full text.
- Record material commands, changed artifacts, failures, and verification results in the available project evidence surface.
- Context operations use the structured request → resolver → work context/write contract → transactional writer path in `tools/context/context_system.py`. The writer supports registered text, code, config, binary, move, and delete targets, verifies before-file and before-unit hashes, restores touched paths on partial failure, and updates catalog, unit, and event evidence. Exact protected namespaces use a task-local manifest and explicit closure event, never global discovery. Knowledge candidates, reviews, revisions, conflict links, and supersession use the dedicated lifecycle operation; source hash checks create review transitions. Decision and case lifecycle writers remain unimplemented and must not be claimed.
- Every context-system CLI command holds the repository-local cross-process lock for its full operation. Nested catalog rebuilds reuse that lock, atomic-write temporary files and the lock file are excluded from discovery, and a missing active file is reported by validation instead of crashing projection rebuild. Do not bypass the lock with direct catalog edits.
- When a repeated failure affects continuation, preserve the objective, attempt, confirmed cause, consecutive count, and next condition.

### Python runtime entrypoint

Project Python commands must not depend on a bare `python` or `python3` name being present on `PATH`. Invoke Python through `tools/runtime/run_python.cmd`; the CMD entrypoint calls the internal PowerShell implementation with `ExecutionPolicy Bypass`, and that implementation requires Python 3.11 or newer and verifies that `tomllib` imports before use. Runtime candidates are resolved in this order: explicit `PROJECT_PYTHON`, project `.venv`, bundled Codex runtimes, then validated system launchers. An invalid, older, or capability-incomplete explicit override fails immediately instead of silently selecting another interpreter.

When a workspace dependency provider is available, its exact Python executable may bootstrap the launcher or be assigned to `PROJECT_PYTHON`; do not persist the returned personal absolute path in project files. If no runtime validates, stop and report the launcher's diagnostic instead of retrying a bare command. Do not call `run_python.ps1` directly because local PowerShell execution policy may reject it.

PowerShell examples:

```powershell
& .\tools\runtime\run_python.cmd tools/context/context_system.py validate
& .\tools\runtime\run_python.cmd -m unittest discover -s tests/context -p 'test_*.py'
```

## 5. Validate

Use the strongest applicable level and name it accurately.

| Level | Meaning |
|---|---|
| Structural | Encoding, schema, syntax, path, link, or static contract checks passed. |
| Automated | Relevant automated tests or commands passed. |
| Application-validated | Output was exercised in the target application or runtime. |
| User-approved | The user explicitly accepted the result. |

Validation at one level does not imply a higher level. Inspect changed files again after writing, check source links and protected-path status, and report any unresolved failure.

For document changes, also verify that every active document is registered, no subject has more than one current proposal, every new file passed the creation gate, and superseded duplicate text has a recoverable Git commit, blob, and content hash before compaction.

## 6. Close and hand off

1. Lead the user report with the achieved outcome.
2. List created or changed active files and the actual validation performed.
3. State exclusions, unimplemented work, risks, and approval status.
4. Update [SESSION_HANDOFF.md](../../SESSION_HANDOFF.md) with verified current state, evidence paths, active failures, and the first unstarted action.
5. If the stage requires approval, stop after the report and wait.

For an R-2A registered Markdown write, the closure update must be authorized by the same work context and its before hashes. A direct manual edit is permitted only during the recorded initial bootstrap before the live writer fixture.

A stage report may be delivered in the user response when no durable point-in-time artifact is required. Do not create another file merely to restate the same closure information.

Detailed record schemas, retrieval behavior, and freshness review are owned by the linked knowledge documents rather than this common workflow.
