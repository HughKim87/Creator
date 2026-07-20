---
doc_id: doc.tool_requirements
kind: requirements
domain: tooling
lifecycle: active
authority: normative for agent discovery and pre-L7 reusable tool behavior
audience: agent
language: en
validation: structure_validated
purpose: Define the capability, safety, interface, and validation requirements for agent discovery and reusable workflow tools before implementation or selection.
scope: Bounded agent-document discovery plus reusable state, media, interchange, audit, and application-validation tools; appearance here alone does not activate a tool.
read_when: Invoking or reviewing agent discovery, selecting or implementing L7 tools, reviewing a reusable script, or considering helper promotion.
write_when: A measured tool need, retained capability, interface contract, validation requirement, or activation decision changes.
---
# Workflow Tool Requirements

## Activation rule

- Implement or activate only a capability selected by the user from measured repeated work.
- Prefer a thin deterministic operation with explicit inputs and outputs.
- Do not claim media, A/V, or application validation without evidence from that surface.
- A reusable tool belongs in `tools/`; input-specific helpers remain with the designated task output.
- Before a tool is considered reconstructed, its implementation, help or contract, and synthetic regression
  tests must all exist in the active project.

## Capability catalog

| Capability | Required behavior | Layer status |
|---|---|---|
| Agent document discovery | Call the official Obsidian CLI directly, query one Base domain view or domain folder, return at most three candidate paths, read one atomic note, and report failure without fallback | Implemented in L3.2 and optimized in L3.3 |
| Task-state I/O | Strict schema, safe paths, atomic replacement, source fingerprint checks, bounded output verification, and verified promotion | Implemented in `tools/state_io.py` |
| Media inspection | Report container, streams, duration, frame rate, and audio properties from an exact named file | Candidate for L7 |
| Lossless remux | Convert a named MKV recording to an MP4 container without re-encoding; preserve the source and skip an existing destination | Candidate for L7 |
| Source evidence assets | Resolve source identity, reuse matching time/frame/size assets, create missing assets, and register integrity | Candidate for L7 |
| Subtitle and cut sync advisory | Detect speech, subtitle, and boundary risks without modifying the authoritative cutlist | Candidate for L7 |
| Premiere interchange | Produce a documented XML, EDL, or CSV route selected for the user's actual Premiere environment | Candidate for L7 |
| Editing quality audit | Calculate section cut statistics and emit advisory warnings and justified waivers from one content sequence | Candidate for L7 |
| Application validation | Record exact import, playback, and render evidence without converting it into creative approval | Candidate for L7 |

## Common interface contract

- Accept exact paths and options; never discover user tasks by enumerating `inputs/` or `outputs/`.
- Preserve Unicode and spaced paths and never overwrite originals.
- Use non-zero exit codes for invalid input, unavailable dependency, partial output, or failed validation.
- Print or return actual created and reused paths. A success message alone is insufficient.
- A rerun with unchanged governing input reuses or safely skips existing output.
- Temporary files live outside the repository or in an already ignored task-local location and are removed on failure.
- Partial output remains ineligible and cannot replace the last verified state.
- Tests use synthetic files unless the user designates an exact real item and purpose.

## Agent document-discovery contract

- Use the official Obsidian product CLI directly. Do not add a Python, PowerShell, MCP, Graphify, or compatible-format wrapper merely to invoke it.
- The verified Windows entry point is `C:\Users\Hugh\AppData\Local\Programs\Obsidian\Obsidian.com`. Execute that exact command through its confirmed approved boundary as required by `PROJECT_RULES.md#authorization-and-change-safety`; do not first retry the default sandbox.
- Obsidian must be running. If the first direct version check reports that the app is stopped, start the installed Obsidian app once and retry the same direct command once; report another failure.
- For unknown routes, query `base:query path='docs/agent/navigation/AGENT_DOCUMENTS.base' view='<Domain>' format=paths`. If no domain can be selected, report ambiguity instead of querying every note.
- For an unresolved selector inside one domain, use `search query='<2-6 concise English terms or property filter>' path='docs/agent/<domain>' limit=3 format=json`.
- Accept only paths returned by the selected domain view or folder. Results are candidates, not authority and not permission to read adjacent files.
- Compare `purpose` and `authority` through `property:read`; read `scope` and `read_when` only for a tie. Select one atomic note, then use `read path='<candidate>'`. Use `outline` only when the selected note explicitly declares multiple task contexts.
- Root startup documents and known `AGENTS.md` routes remain direct reads; the CLI does not replace them.
- On a non-zero exit, unavailable app, permission mismatch, malformed result, no result, unresolved ambiguity, or protected-path risk, report the condition and stop discovery. Do not silently fall back to direct routing or another engine.
- The checked-in Obsidian Base is the only generated index. QMD, embeddings, Ollama, Graphify, community plugins, MCP, shared servers, and other generated indexes remain inactive unless a separate measured failure and user approval justify one.

## Source evidence contract

- One exact fingerprint maps to one stable source ID. The same fingerprint cannot silently acquire another ID,
  and one ID cannot accept a changed fingerprint.
- Evidence identity includes source ID, original time or frame, extraction parameters, asset path, SHA-256, size,
  and status.
- Lookup checks the active catalog before extraction and returns existing matching assets unchanged.
- Edited timeline time is converted through the active cut mapping before source evidence lookup.
- Register retained frame, audio, and contact-sheet assets. Duplicate asset IDs or paths fail closed.
- Source evidence is never overwritten or deleted automatically.

## Sync advisory contract

- Accept the exact media, subtitle, and cutlist inputs from the caller.
- Report suspected speech cuts, subtitle-boundary risk, silence, and alignment issues with source coordinates.
- Do not decide microbeat function, keep/remove judgment, or editing tempo.
- A correction command creates a new cutlist and applies only named boundary changes.

## Interchange and application contract

- The user selects the actual delivery route after the environment is confirmed: XML, EDL, CSV, or another
  supported form.
- Validate frame rate, timebase, source references, audio mapping, sequence duration, and missing media before
  calling a file structurally valid.
- Premiere import or render must be tested in Premiere before claiming application validation.
- Technical import success does not approve message, rhythm, or editing direction.

## Editing audit contract

- Accept one content sequence and one section-to-mode profile.
- Calculate cut count, selected duration, average, maximum, and late-density comparison.
- Use the warning codes and waiver semantics defined in `docs/agent/workflow/EDITING_QUALITY_RULES.md#advisory-audit-contract`.
- Never modify the cutlist and never treat thresholds as target cut lengths.

## Explicitly non-required infrastructure

The project does not require a database, event-sourced edit memory, machine transition graph, work-claim
service, mandatory hooks, CI, broad CLI wrapper, or fail-open guard to implement these capabilities. A later
measured failure must justify any such addition through `docs/agent/rebuild/RECONSTRUCTION_MAP.md`.
