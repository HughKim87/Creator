# Document-Based Data Work Rules

- Purpose: govern creation, editing, validation, ownership, and machine-readable derivation of maintained project documents and persistent project data.
- Read when: before creating, editing, moving, classifying, or validating maintained Markdown, root control documents, records, events, snapshots, indexes, or inventories.
- Owner: user-approved policy; project agents maintain accepted wording.
- Authority: task-specific; `PROJECT_RULES.md` remains higher authority.

## Rules

- Before an intended persistent project-data write, record the canonical owner path and the owner sections read; append the material result to that owner before running completion validation.
- Apply `PROJECT_RULES.md` §Document-based data and execution. For each maintained machine-readable artifact, record whether it is a document derivative or read-only legacy before changing it; this task rule owns the classification procedure, not the always-on canonical-data policy.
- After classifying a maintained machine-readable artifact, record its canonical owner path, generator or rebuild command, and verification method. If a required rebuild method is absent, record that evidence gap in the owner and stop the persistent write.
- Apply `PROJECT_RULES.md` §Project structure and ownership. Before writing, record whether the action updates an existing owner or uses the new-document exception; for an exception, record the distinct durable purpose, long-lived reader/read condition, and owner search evidence.
- For an improvement-initiative artifact, record why the existing stage owner cannot serve its long-lived reader before creating a separate report or review file.
- Select the target directory from the ownership assignments in `PROJECT_RULES.md`; this task rule does not redefine folder ownership.
- Write user-facing guides and approval summaries in Korean. Agent-facing rules and routing documents may use concise English.
- Link to an authority instead of copying its procedures or current state. Update `SESSION_HANDOFF.md` only when verified current state or the first next action changes.
- Use the generated active-document inventory for exhaustive path coverage. Keep manually maintained maps as owner/category routers rather than copying every document path.
- After every write, re-read the changed file and verify strict UTF-8, NUL 0, expected sections, relevant local links, trailing whitespace, and the final diff. For machine-readable artifacts, also verify the canonical document link, rebuild relationship, and absence of machine-only active facts.
- Do not call a document user-approved merely because it was generated or structure-validated.
