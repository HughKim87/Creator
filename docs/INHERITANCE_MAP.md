# Existing-Asset Inheritance Map

- Purpose: Record whether preserved rules, contracts, tools, tests, and skills are adopted, adopted with changes, deferred, or excluded.
- Scope: Legacy-asset decisions only; this document does not define global rules, current state, or layer procedures.
- Audience and language: Agents; English.
- Read when: An approved task adds, replaces, removes, or recovers an existing feature or contract. Read only the relevant row.
- Write when: Evidence changes an asset decision, activation layer, retained contract, or recovery condition.
- Authority: This is the sole source of existing-asset adoption decisions. `backup/` and `backup/root_snapshot_2026-07-18/` remain read-only evidence.

## Decision meanings

| Decision | Meaning |
|---|---|
| `adopt` | Required for project identity, original safety, or result consistency. The implementation may still be simplified. |
| `adopt_with_changes` | The problem and core contract are valid, but the preserved implementation or metadata is too costly or unsafe. |
| `defer` | Keep the source in `backup/`; activate only after the listed real-world condition occurs. |
| `exclude` | Do not use in the active execution path. Preserve only as historical evidence. |

Exclusion never authorizes deletion. No row authorizes modifying or executing code directly inside `backup/`.

## Adopted project foundations

| Asset | Evidence | Retained contract | Active destination |
|---|---|---|---|
| Original and file boundaries | `backup/PROJECT_RULES.md` | Protect `inputs/`, separate derivatives, keep user data outside reusable framework files, and prohibit automatic deletion | `PROJECT_RULES.md` |
| File-format stability | `backup/root_snapshot_2026-07-18/.gitattributes` | Stable text line endings and media binary classification across operating systems | `.gitattributes` |
| Small startup context | `backup/PROJECT_BOOTSTRAP.md`, `backup/docs/INDEX.md` | Start small and read only documents required by the task | `AGENTS.md` |
| Improvement criteria | `backup/docs/DESIGN_PRINCIPLES.md` | Reuse, deterministic validation, agent replaceability, context cost, and user creative authority | `REBUILD_PRINCIPLES.md`, `PROJECT_RULES.md` |
| Tool and AI roles | `backup/PROJECT_RULES.md` | Deterministic tools perform repeatable operations; AI proposes interpretations; tool success is not quality approval | `PROJECT_RULES.md` |
| Validation vocabulary | `backup/PROJECT_RULES.md` | Separate generated, parsed, structure, tool, app, and user validation | `PROJECT_RULES.md` |
| Repeated-failure stop | `backup/PROJECT_RULES.md` | Stop after three consecutive failures on the same objective | `PROJECT_RULES.md` |

## Adopt when the named layer begins

| Asset | Evidence | Retained contract | Activation layer |
|---|---|---|---|
| Source identity | `backup/01_youtube_production_workflow.md`, `backup/tools/source_frame_assets.py` | The same source keeps one stable `source_id`; a changed fingerprint cannot be aliased to the same source | `FILE_DATA_CONTRACT.md`; tool in L7 |
| Original evidence coordinates | `backup/tools/source_frame_assets.py`, `backup/tools/register_source_assets.py` | Link visual and audio evidence to original time/frame and reuse unchanged assets | Boundary recorded in `FILE_DATA_CONTRACT.md`; fields and tool in L7 when consumed |
| Production routes | `backup/01_youtube_production_workflow.md` | Pre-shoot: `1 -> 2 -> 3 -> 4 -> 6 -> 5 -> 7 -> 8`; recorded footage: subtitle confidence, then `6 -> 5 -> 7 -> 8` | L5 |
| User decision points | Same workflow | User decides subject, concept/message, representative editing direction, and upload | L5 |
| Analysis before planning | Same workflow | Do not plan without evidence analysis or edit the full piece without an approved plan | L5 |
| Current and prior versions | Same workflow, `backup/skills/SKILL_CONTRACT.md` | Reuse unchanged results; create a version only after input or judgment changes; preserve prior versions | `FILE_DATA_CONTRACT.md` and `tools/state_io.py` |
| Editing quality knowledge | `backup/docs/EDITING_QUALITY_STANDARD.md` | Separate candidate range from actual cut, use microbeat judgment, justify long cuts, and sample beginning/middle/end | L5 and L8 |
| Evidence-type separation | Quality standard and skill contract | Do not mix original-source evidence with edited-render evidence; record real A/V and app checks separately | L5, L7, L8 |
| Selected existing tools | `backup/tools/README.md`, relevant `backup/tests/` | FFmpeg/ffprobe, remux, source-frame assets, sync advisory, Premiere XML, and editing audit only when selected | L3 or L7 |
| Selected stage skills | `backup/skills/README.md`, selected `backup/skills/*/SKILL.md` | Preserve stage judgment and I/O contracts for skills confirmed in actual use | L8 |

## Adopt with changes

| Asset | Keep | Change before activation | Target form |
|---|---|---|---|
| Source asset record | Stable ID, fingerprint, original time/frame, asset path, integrity, status | Do not require legacy candidate, bit, tag, or note fields without a consumer | L2 source identity core; tool-specific fields only when activated |
| Video work state | Current stage, reference input/output, next action, blocker, user decision | Do not repeat the same state in cards, multiple JSON files, and output metadata | `FILE_DATA_CONTRACT.md` and `tools/state_io.py` |
| Output version record | Current/prior relation, source reference, validation | Do not require all legacy metadata and approval states on every file | Version, status, lineage, integrity, reduced approval, and eligibility fields in `FILE_DATA_CONTRACT.md` |
| Workflow contract | Stage order, required completion, user decisions | Do not restore the full transition graph and default-deny machine contract | Concise human-readable rules; automate only repeated omissions |
| Common check command | Original boundary, required files, real code checks, failure-code preservation | Remove dependencies on discarded docs, hooks, CI, and SQLite | One active-structure check entry point when needed |
| Skill contract | Input, output, stop, user decision, next handoff | Do not impose the full legacy promotion protocol on every skill | Minimum shared format used by active stages |
| Editing quality audit | Surface long sections, late-density gaps, and missing evidence | Do not treat fixed cut length as a target or every finding as a hard gate | Advisory report with human-readable evidence |

## Deferred

| Asset | Reason | Reconsider only when |
|---|---|---|
| SQLite and domain/service/storage layers | Too costly for one-person sequential file work | File-based state repeatedly fails under real concurrency or query load |
| Event-sourced editing memory and append-only revision lineage | Potential value but high input and maintenance cost | Simple current/prior recording repeatedly loses important feedback |
| Full `workflow_gate.py` machine contract | Too much state and transition management | A concise checklist repeatedly misses the same transition |
| `projectctl` work claims and receipts | Duplicate state in a single-writer workflow | Concurrent framework edits repeatedly collide |
| Mandatory hooks, CI, and pre-commit | Installation and environment cost exceeds current need | A single manual check repeatedly fails to prevent violations |
| New CLI wrapper | Wrapping existing commands alone adds no functional value | Repeated command-discovery cost is measured |

## Excluded from the active path

| Asset | Reason |
|---|---|
| The archived nine-stage full rewrite and evidence-package process | Development procedure grew without measured production benefit |
| Independent QA/red-team roles and long multi-item observation gates | Management cost is excessive for the current one-person workflow |
| Approval challenge, provenance, quarantine, and promotion protocols | Complexity exceeds the actual local production risk |
| The archived complete CLI/state/approval command set | Coupled to deferred SQLite and broad machine contracts |
| Caches, virtual environments, and generated reports as active sources | Re-creatable outputs and not operational evidence |
