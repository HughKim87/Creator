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
| Domain | `control`, `rebuild`, `navigation`, `workflow`, `editing`, `tooling`, `state`, `user_status`, `history` |
| Lifecycle | `draft`, `active`, `deprecated`, `superseded`, `historical` |
| Authority | `normative`, `derived`, `implementation`, `evidence` |
| Audience | `agent`, `user`, `both` |
| Validation | `generated`, `structure_validated`, `tool_validated`, `operational_validated`, `user_validated` |

## Registration contract

A complete document record is the combination of its registry row and its own top metadata. Every active Markdown document must declare these six fields within its first ten lines:

1. `Purpose`: the one durable question the document answers.
2. `Scope`: included content and the nearest important exclusion.
3. `Audience and language`: intended reader and required language.
4. `Read when`: task event that justifies loading the document; never use “when relevant.”
5. `Write when`: exact durable change owned by the document.
6. `Authority`: whether it is normative, derived, implementation, or evidence, plus the adjacent authority when confusion is likely.

The registry row supplies the stable ID, path, kind, lifecycle, authority class, audience, validation level, read trigger summary, and relationship. The document header supplies its purpose, detailed scope, and write trigger. A document is not active until both records agree.

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
| `doc.obsidian_adoption_analysis` | `docs/reports/2026-07-19_옵시디언_도입_타당성_분석.md` | report | historical | evidence | user / Korean | structure_validated | Obsidian adoption decision or pilot approval | Evidence-based assessment; recommends a bounded L3 pilot, not full migration |

Temporary migration-source documents are not registered as active and cannot override this registry.

## Domain index

Use this index only after `AGENTS.md` identifies a task route or when no route exists. It narrows discovery by durable ownership, not by similar wording.

| Domain | Primary IDs | Boundary |
|---|---|---|
| `control` | `doc.router`, `doc.rules`, `doc.handoff`, `doc.registry` | Entry, global policy, current state, and document classification only |
| `rebuild` | `doc.rebuild_principles`, `doc.rebuild_plan`, `doc.reconstruction` | Rebuild decisions, layer execution, and capability status |
| `navigation` | `doc.router`, `doc.registry` | Task-to-document and document-to-authority lookup; derived graphs add no authority |
| `workflow` | `doc.workflow_foundation`, future approved workflow rules | Production routes, stage boundaries, and decisions |
| `editing` | `doc.editing_quality` | Editing judgment, evidence, sampling, and quality gates |
| `tooling` | `doc.tool_requirements`, `doc.skill_requirements` | Reusable implementation and skill responsibilities |
| `state` | `doc.file_state`, `doc.file_state_schema` | Task-state meaning, lifecycle, and machine shape |
| `user_status` | `doc.project_status` | Korean milestone view derived from current verified state |
| `history` | `doc.structure_report`, `doc.rebuild_report`, `doc.document_node_analysis`, `doc.obsidian_adoption_analysis` | Named point-in-time evidence; never default execution input |

## Folder contract

- Root: only required entry/control documents and repository configuration.
- `docs/agent/`: English agent authorities and machine-readable contracts.
- `docs/agent/schemas/`: lowercase machine-readable schemas that implement a named agent contract.
- `docs/user/`: active Korean user-facing documents.
- `docs/reports/`: Korean point-in-time, historical, or superseded reports; never execution inputs.
- `tools/` and `tests/`: implementation and verification, not document authorities or navigation indexes.
- User originals, derivatives, and the temporary migration-source directory are data boundaries, never framework-document collections.

Folder depth is not an authority mechanism. Add a subfolder only when a coherent set has its own audience or lifecycle and the move reduces repeated navigation; update the registry, router, links, tests, and derived graph in the same change.

## Naming and format contract

- Root control Markdown keeps its established uppercase name. New agent authority Markdown uses uppercase ASCII `SNAKE_CASE.md`; schema and implementation files use lowercase ASCII `snake_case` with the appropriate extension.
- Active Korean user documents use a stable Korean subject name. Reports use `YYYY-MM-DD_한국어_주제.md` when a date distinguishes the evidence snapshot.
- Stable document IDs use `doc.<lower_snake_case>` and survive a path move. Stable route and write IDs use `lower_snake_case` in `AGENTS.md`.
- Markdown uses one H1, the six-field metadata block, task-oriented H2 sections, repository-relative links, and stable heading anchors. Tables are for exact mappings; prose is for rationale or constraints.
- JSON and schema files are UTF-8 without BOM, use lowercase ASCII keys, declare a schema version or schema identity, and link back to the normative Markdown contract through `$comment` or equivalent metadata.
- Do not create generic names such as `NOTES`, `MISC`, `TEMP`, `FINAL`, or `NEW`. The filename must identify the owned domain or evidence subject; lifecycle belongs in metadata, not filename suffixes.

## Split, merge, and lifecycle rules

- Split a document when content has a different authority, audience/language, lifecycle, read trigger, or independent write owner, or when unrelated sections are repeatedly loaded for separate task routes.
- Keep sections together when they share all five attributes and are normally read and changed as one unit. Length alone is not a split reason.
- Merge documents when they answer the same durable question for the same audience and lifecycle and one is only restating the other. Preserve the surviving stable ID and mark any retained predecessor as superseded evidence.
- Before a split, merge, rename, or move, identify the surviving authority and affected route IDs. In the same change update this registry, `AGENTS.md`, inbound links, tests, and the derived route graph; do not leave compatibility copies as active authorities.
- Drafts are not execution inputs. Deprecation requires a replacement or explicit no-replacement decision. Historical and superseded documents remain available only through exact-name history routes.

## Navigation model

Navigation has two orthogonal indexes and no third hand-maintained catalog:

1. `AGENTS.md` is the task-time index: stable route ID -> startup set -> exact read delta -> selector -> default exclusions, plus stable write ID -> authority.
2. This registry is the document index: stable document ID -> purpose/classification/path -> read trigger -> relationships.

Start with the task index and use it directly for known routes. Use the document index to resolve an affected authority, unknown route, lifecycle, or relationship, and invoke the derived graph only for ambiguity or large-set validation. Related links never expand the read set automatically. Search by route ID, document ID, exact path, or stable heading before using broad text search.

## Reference protocol

- Use exact repository-relative paths. Do not use aliases such as `Same workflow`.
- Reference documents by stable heading, for example `docs/agent/FILE_DATA_CONTRACT.md#approval-and-next-use-rules`.
- Reference code by active path and symbol, for example `tools/state_io.py::validate_reference_input`.
- Do not link an active authority to a temporary migration-source path. Reconstruct retained content first and link its active destination.
- State the relationship when ambiguity is possible: `normative`, `implements`, `evidence`, `derived-from`, or `supersedes`.
- Use `routes_to`, `governed_by`, `implements`, `derived_from`, `evidence_for`, and `supersedes` as typed relationship labels in generated navigation data. Only `always_read`, `read_when_current_work`, and `requires` may select read documents.
- Do not persist branch divergence, dirty-worktree state, or other facts that Git can query. Historical reports may cite a commit as point-in-time evidence.
- A moved document must update this registry, routed paths, internal links, and governance tests in the same change.

## Derived Graphify route graph

- Generate the route graph from `AGENTS.md` and this registry; never hand-edit it or treat it as a third source of truth.
- Store generated graphs, manifests, query results, and caches outside the repository. The graph contains document metadata and paths, not document bodies or protected user-data nodes.
- Resolve exactly one route ID before traversal. Multi-intent work uses an explicit union of route IDs; free-form semantic similarity cannot choose extra documents.
- Traverse at most one edge from a route or write node. Document-to-document traversal, generic `references` edges, community expansion, and unbounded BFS are prohibited for read selection.
- Require exact hashes of both generating authorities. A stale hash, missing selector, unknown route, unexpected path, or non-whitelisted edge fails closed to the direct `AGENTS.md` route.
- Return only selected paths, bounded headings/selectors, exclusions, and provenance. Open document contents through the normal project read path after selection.
- Keep direct routing as the default while its exact path is known. A generated graph becomes default only after the same-task total context, including its compact result payload, is lower without an accuracy regression.
- Adding unrelated registered documents must not change an existing route result. Adding or changing a route intentionally changes `AGENTS.md`, invalidates the derived graph, and requires routing tests.

## Maintenance checks

- Every registered path exists and every active framework Markdown document is registered.
- Active documents declare purpose, scope, audience/language, read/write conditions, and authority at the top.
- Stable route, write, and document IDs are unique; every fixed routed path is registered and every selector is explicit.
- One durable domain has one normative authority.
- Derived and evidence documents are not execution inputs.
- Agent documents contain English prose; user and report documents contain Korean prose.
- Generated route graphs contain zero protected paths, use only whitelisted one-hop selection edges, and fail closed when `AGENTS.md` or this registry changes.
- `AGENTS.md`, `PROJECT_RULES.md`, and `SESSION_HANDOFF.md` stay within their context budgets enforced by tests.
