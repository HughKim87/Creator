---
doc_id: doc.document_placement
kind: requirements
domain: navigation
lifecycle: active
authority: normative for document folders, names, splits, moves, and references
audience: agent
language: en
validation: tool_validated
purpose: Decide where a document belongs and how it is named, split, moved, and linked.
scope: Markdown placement and change procedure; classification property definitions and discovery views live in DOCUMENT_REGISTRY.md.
read_when: Creating, moving, renaming, splitting, merging, or relinking a project document.
write_when: A durable placement, naming, split, merge, move, or reference rule changes.
---
# Document Placement Contract

## Placement decision

1. Select the note's audience and lifecycle first.
2. For active agent notes, select one durable domain and use its folder from `DOCUMENT_REGISTRY.md#domain-folders`.
3. Put current Korean user summaries in `docs/user/` and point-in-time Korean evidence in `docs/reports/`.
4. Keep root limited to `AGENTS.md`, `PROJECT_RULES.md`, `SESSION_HANDOFF.md`, and repository configuration.
5. Never place user originals, derivatives, migration sources, implementation code, or caches in a document folder.

Folder depth is not authority. Add another level only when a coherent set has a distinct audience or lifecycle and measured navigation improves.

## Naming and note format

- Active agent notes use uppercase ASCII `SNAKE_CASE.md`; machine files use lowercase ASCII `snake_case` plus the appropriate extension.
- Active Korean user notes use stable Korean subject names. Historical reports use `YYYY-MM-DD_한국어_주제.md` when the date distinguishes the snapshot.
- Keep one H1 after YAML frontmatter and use task-oriented H2 headings. Use tables for exact mappings and prose for rationale.
- Do not use generic names such as `NOTES`, `MISC`, `TEMP`, `FINAL`, or `NEW`.
- Keep the stable `doc_id` unchanged across a move or rename.

## Split and merge rules

- Split when authority, audience/language, lifecycle, read trigger, write owner, or repeatedly loaded task context differs.
- Keep sections together when all six attributes match and callers normally consume them together. Length alone is not a split reason.
- Merge notes that answer the same durable question for the same audience and lifecycle. Preserve one `doc_id`; mark a retained predecessor as superseded evidence.
- Do not leave compatibility copies as active notes. Obsidian and Git history provide navigation and recovery.

## Move or rename procedure

1. Resolve the exact source and destination below the workspace and confirm the destination does not exist.
2. Move only the approved note and its tightly owned machine assets.
3. Update the note's domain property if its durable domain changed; otherwise preserve all classification properties.
4. Update `AGENTS.md`, active inline paths, Markdown links, schema comments, implementation references, tests, and current user status in the same change.
5. Let the Obsidian Base derive the new path; do not edit a duplicate path table.
6. Run Base query, link, unresolved-link, UTF-8/NUL, route, and integrated tests before calling the move complete.

## Reference rules

- Active authorities use exact repository-relative paths and stable headings, for example `docs/agent/state/STATE_OPERATIONS.md#approval-and-next-use`.
- Use normal Markdown links when a clickable human path matters and inline code for exact tool paths. Obsidian wikilinks may be added only when the note-name target is unique and the link remains understandable outside Obsidian.
- Relationships describe provenance or ownership and never expand an agent read set automatically.
- A moved note updates all active inbound references. Historical prose may retain an old inline path only when it is explicitly part of the dated evidence.
- Do not link active execution sources to protected user data or the migration archive.

## Verification

- Source is absent, destination exists, `doc_id` is unchanged, and the Base shows the destination once.
- No active reference uses the old path.
- No new unresolved link, duplicate `doc_id`, wrong-domain path, or unregistered machine asset exists.
- The affected route selects only the new minimum notes.
