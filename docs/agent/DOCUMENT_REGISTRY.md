# Document Registry

- Purpose: Classify project documents and define their authority, lifecycle, audience, and reference relationships.
- Scope: Active framework documents, current user documents, historical reports, and machine-readable document contracts; implementation code is linked but not cataloged here.
- Audience and language: Agents; English.
- Read when: Discovering documents, changing document architecture, auditing authority, or resolving an ambiguous reference.
- Write when: A document is added, moved, renamed, reclassified, superseded, or assigned a different authority.
- Authority: This is the sole document-classification registry. `AGENTS.md` remains the startup router and `SESSION_HANDOFF.md` remains the current-state source.

## Classification model

Each document has independent classifications. Folder location is a quick audience/status signal, not a substitute for document metadata.

| Axis | Values |
|---|---|
| Kind | `router`, `policy`, `state`, `principle`, `plan`, `decision_registry`, `requirements`, `contract`, `schema`, `user_status`, `report` |
| Lifecycle | `draft`, `active`, `deprecated`, `superseded`, `historical` |
| Authority | `normative`, `derived`, `implementation`, `evidence` |
| Audience | `agent`, `user`, `both` |
| Validation | `generated`, `structure_validated`, `tool_validated`, `operational_validated`, `user_validated` |

## Registered documents

| ID | Path | Kind | Lifecycle | Authority | Audience / language | Validation | Read trigger | Relationship |
|---|---|---|---|---|---|---|---|---|
| `doc.router` | `AGENTS.md` | router | active | normative for document selection | agent / English | tool_validated | Every workspace task | Routes to all other documents |
| `doc.rules` | `PROJECT_RULES.md` | policy | active | normative for global rules | agent / English | tool_validated | Every workspace task | Governs every project asset |
| `doc.handoff` | `SESSION_HANDOFF.md` | state | active | normative for current project state | agent / English | structure_validated | Continue, change, or verify work | Links to durable authorities; stores no document catalog or dynamic Git facts |
| `doc.registry` | `docs/agent/DOCUMENT_REGISTRY.md` | decision_registry | active | normative for document classification | agent / English | tool_validated | Document discovery, architecture, or audit | Classifies this table |
| `doc.rebuild_principles` | `docs/agent/REBUILD_PRINCIPLES.md` | principle | active | normative for rebuild decisions | agent / English | structure_validated | Rebuild scope, exception, or stop decision | Applied by the rebuild plan |
| `doc.rebuild_plan` | `docs/agent/REBUILD_PLAN.md` | plan | active | normative for layer scope and gates | agent / English | structure_validated | Approved rebuild work or plan review | Implements rebuild principles |
| `doc.reconstruction` | `docs/agent/RECONSTRUCTION_MAP.md` | decision_registry | active | normative for capability reconstruction decisions | agent / English | structure_validated | Capability change or archive-readiness audit | Maps retained behavior to active authorities |
| `doc.workflow_foundation` | `docs/agent/WORKFLOW_FOUNDATION.md` | requirements | active | normative for pre-L5 workflow knowledge | agent / English | structure_validated | L5-L8 workflow design | Supplies routes, stage boundaries, planning, and decisions to L5 |
| `doc.editing_quality` | `docs/agent/EDITING_QUALITY_RULES.md` | requirements | active | normative for editing-quality knowledge | agent / English | structure_validated | L5, L7, or L8 editing work | Supplies judgment, evidence, sampling, and gates |
| `doc.tool_requirements` | `docs/agent/TOOL_REQUIREMENTS.md` | requirements | active | normative for pre-L7 tool behavior | agent / English | structure_validated | L7 tool selection or implementation | Specifies reusable capabilities without activating them |
| `doc.skill_requirements` | `docs/agent/SKILL_REQUIREMENTS.md` | requirements | active | normative for pre-L8 skill behavior | agent / English | structure_validated | L8 skill selection or implementation | Specifies shared contracts and stage responsibilities |
| `doc.file_state` | `docs/agent/FILE_DATA_CONTRACT.md` | contract | active | normative for task state and output lifecycle | agent / English | tool_validated | Designated task-state operations | Implemented by `tools/state_io.py`; shape declared by `doc.file_state_schema` |
| `doc.file_state_schema` | `docs/agent/schemas/video_task_state.schema.json` | schema | active | implementation contract for JSON shape | agent/tool / English | tool_validated | Schema validation or contract changes | Implements the structural subset of `doc.file_state` |
| `doc.project_status` | `docs/user/PROJECT_STATUS.md` | user_status | active | derived | user / Korean | structure_validated | Milestone or status review | Derived from `doc.handoff` and verified results |
| `doc.structure_report` | `docs/reports/PROJECT_STRUCTURE_ANALYSIS.md` | report | historical | evidence | user / Korean | structure_validated | Explicit historical structure review | Snapshot dated 2026-07-18 |
| `doc.rebuild_report` | `docs/reports/REBUILD_EXECUTION_REPORT.md` | report | superseded | evidence | user / Korean | structure_validated | Explicit review of the discarded first rebuild | Superseded by `doc.rebuild_plan` and `doc.reconstruction` |
| `doc.document_node_analysis` | `docs/reports/2026-07-19_문서_노드_구조_개선_분석.md` | report | historical | evidence | user / Korean | structure_validated | Document-node architecture review or implementation approval | Proposed L3 routing and context-budget refinement; not an execution authority |

Temporary migration-source documents are not registered as active and cannot override this registry.

## Folder contract

- Root: only required entry/control documents and repository configuration.
- `docs/agent/`: English agent authorities and machine-readable contracts.
- `docs/user/`: active Korean user-facing documents.
- `docs/reports/`: Korean point-in-time, historical, or superseded reports; never execution inputs.

## Reference protocol

- Use exact repository-relative paths. Do not use aliases such as `Same workflow`.
- Reference documents by stable heading, for example `docs/agent/FILE_DATA_CONTRACT.md#approval-and-next-use-rules`.
- Reference code by active path and symbol, for example `tools/state_io.py::validate_reference_input`.
- Do not link an active authority to a temporary migration-source path. Reconstruct retained content first and link its active destination.
- State the relationship when ambiguity is possible: `normative`, `implements`, `evidence`, `derived-from`, or `supersedes`.
- Do not persist branch divergence, dirty-worktree state, or other facts that Git can query. Historical reports may cite a commit as point-in-time evidence.
- A moved document must update this registry, routed paths, internal links, and governance tests in the same change.

## Maintenance checks

- Every registered path exists and every active framework Markdown document is registered.
- Active documents declare purpose, scope, audience/language, read/write conditions, and authority at the top.
- One durable domain has one normative authority.
- Derived and evidence documents are not execution inputs.
- Agent documents contain English prose; user and report documents contain Korean prose.
- `AGENTS.md`, `PROJECT_RULES.md`, and `SESSION_HANDOFF.md` stay within their context budgets enforced by tests.
