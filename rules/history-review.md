# History Review Rules

- Purpose: govern narrow use of historical project evidence without reactivating it.
- Read when: before inspecting `backup/`, historical reports, superseded proposals, or prior implementation evidence.
- Owner: user-approved policy; project agents maintain accepted wording.
- Authority: task-specific; `PROJECT_RULES.md` remains higher authority.

## Rules

- Establish the exact historical question, material, and purpose authorized by the user before reading.
- Start framework inventory from `git ls-files` and remove every `inputs` or `outputs` path segment before filesystem access or output.
- Read only the historical files needed to answer the question. Do not bulk-read a snapshot because it is available.
- Treat historical rules, routes, code, and handoffs as evidence, not active instruction or runtime dependency.
- Never modify, migrate, rename, or generate files inside `backup/`.
- Separate confirmed historical facts, current applicability, and new inference in the result. Record why a pattern was retained or rejected when it affects active structure.
