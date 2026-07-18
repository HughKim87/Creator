# Workflow Tool Requirements

- Purpose: Define the active capability, safety, interface, and validation requirements for reusable workflow tools before implementation or selection.
- Scope: Reusable state, media inspection, remux, source evidence, sync advisory, interchange, editing audit, and application-validation tools; no tool is activated merely by appearing here.
- Audience and language: Agents; English.
- Read when: Selecting or implementing L7 tools, reviewing a reusable script, or deciding whether a task-specific helper should be promoted.
- Write when: A measured tool need, retained capability, interface contract, validation requirement, or activation decision changes.
- Authority: This is the sole pre-L7 workflow-tool specification. Active implementations and tests must satisfy it without a migration-archive dependency.

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
- Use the warning codes and waiver semantics defined in `docs/agent/EDITING_QUALITY_RULES.md#advisory-audit-contract`.
- Never modify the cutlist and never treat thresholds as target cut lengths.

## Explicitly non-required infrastructure

The project does not require a database, event-sourced edit memory, machine transition graph, work-claim
service, mandatory hooks, CI, broad CLI wrapper, or fail-open guard to implement these capabilities. A later
measured failure must justify any such addition through `docs/agent/RECONSTRUCTION_MAP.md`.
