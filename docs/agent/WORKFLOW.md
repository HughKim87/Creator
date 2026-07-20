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

## 4. Execute and record

- Modify active project files only within the approved scope.
- Keep policies, procedures, technical contracts, current state, and reports in their owning documents.
- Record material commands, changed artifacts, failures, and verification results in the available project evidence surface.
- Until the knowledge record system is implemented, the authoritative evidence surfaces are repository changes, Korean stage reports, and the current handoff. Do not claim that structured work-event logging exists.
- When a repeated failure affects continuation, preserve the objective, attempt, confirmed cause, consecutive count, and next condition.

## 5. Validate

Use the strongest applicable level and name it accurately.

| Level | Meaning |
|---|---|
| Structural | Encoding, schema, syntax, path, link, or static contract checks passed. |
| Automated | Relevant automated tests or commands passed. |
| Application-validated | Output was exercised in the target application or runtime. |
| User-approved | The user explicitly accepted the result. |

Validation at one level does not imply a higher level. Inspect changed files again after writing, check source links and protected-path status, and report any unresolved failure.

## 6. Close and hand off

1. Lead the user report with the achieved outcome.
2. List created or changed active files and the actual validation performed.
3. State exclusions, unimplemented work, risks, and approval status.
4. Update [SESSION_HANDOFF.md](../../SESSION_HANDOFF.md) with verified current state, evidence paths, active failures, and the first unstarted action.
5. If the stage requires approval, stop after the report and wait.

Detailed record schemas, retrieval behavior, and freshness review are owned by the linked knowledge documents rather than this common workflow.
