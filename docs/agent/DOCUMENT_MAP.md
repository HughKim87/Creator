# Document Map

- Purpose: Identify each active document's authority, audience, use time, and owning responsibility.
- Use when: After startup rules and handoff, before opening additional project documents or creating a new document.
- Owner: Project agents maintain the map; authority changes require user approval.
- Language: English.
- Location: `docs/agent/DOCUMENT_MAP.md`. Routed from [AGENTS.md](../../AGENTS.md) and linked to all active foundation documents.

## Authority classes

| Class | Meaning |
|---|---|
| Policy | Always-applicable instruction. May control agent action. |
| Router | Selects the authoritative document but does not own detailed content. |
| Current state | The single resumable project checkpoint. |
| Session record | A closed historical record of one session's requests, work, decisions, failures, and results. It never owns current state. |
| Procedure | How to perform a class of work. |
| Technical contract | Data, retrieval, or maintenance behavior to implement and verify. |
| User guide | Human-readable explanation; not an agent instruction authority. |
| Current proposal | The sole pending design candidate for one topic. It has no instruction authority until the user accepts it and the owning contracts are updated. |
| Case record | A source-traceable problem, failure, and resolution record. It may supply evidence and retrieval cues; enforceable prevention rules remain in their owning policy or procedure. |
| Report | Point-in-time evidence and recommendation; not automatically active policy. |
| Historical source | Read-only evidence under `backup/`; never an active dependency. |

## Preservation and default-context states

| State | Meaning | Default context behavior |
|---|---|---|
| `maintained-current` | The file is the current owner or maintained projection of its subject. Update it in place. | Read only at its declared route; mandatory files remain mandatory. |
| `current-proposal` | The one pending proposal for a subject. It may replace an earlier proposal but cannot replace accepted authority before approval. | Read for proposal review or its explicitly proposed implementation stage only. |
| `retained-evidence` | A point-in-time analysis, decision source, or implementation result retained for traceability. | Excluded unless an exact provenance, audit, migration, or historical question requires it. |
| `superseded-evidence` | A replaced proposal or report retained only to explain history. Its full snapshot may live in Git while the working-tree file is a short preservation marker. | Excluded from normal context and never used as current instruction or design. |

Git history is the normal preservation surface for superseded full text. Do not keep a second full copy merely to preserve an earlier state.

## Active document registry

| Document | Class | Authority state | Preservation / default context | Read when |
|---|---|---|---|---|
| [AGENTS.md](../../AGENTS.md) | Router | Active router | `maintained-current`; mandatory | Every conversation start |
| [PROJECT_RULES.md](../../PROJECT_RULES.md) | Policy | Active authority | `maintained-current`; mandatory | Every conversation start and throughout work |
| [governance rules](../../rules/governance.md) | Policy pack | Active conditional authority | `maintained-current`; resolver-selected only | Staged work, ownership, or document-boundary predicates match |
| [version-control rules](../../rules/version-control.md) | Policy pack | Active conditional authority | `maintained-current`; resolver-selected only | Backup, recovery, or version-control predicates match |
| [documentation rules](../../rules/documentation.md) | Policy pack | Active conditional authority | `maintained-current`; resolver-selected only | Documentation, report, guide, or metadata predicates match |
| [provenance rules](../../rules/provenance.md) | Policy pack | Active conditional authority | `maintained-current`; resolver-selected only | Claim, source, research, inference, or decision predicates match |
| [knowledge rules](../../rules/knowledge.md) | Policy pack | Active conditional authority | `maintained-current`; resolver-selected only | Knowledge, confidence, conflict, or supersession predicates match |
| [retrieval rules](../../rules/retrieval.md) | Policy pack | Active conditional authority | `maintained-current`; resolver-selected only | Routing, context, catalog, unit, or retrieval predicates match |
| [validation rules](../../rules/validation.md) | Policy pack | Active conditional authority | `maintained-current`; resolver-selected only | Validation, reporting, failure, closure, or handoff predicates match |
| [DOCUMENT_MAP.md](DOCUMENT_MAP.md) | Router and registry | Active authority for document ownership and routing | `maintained-current`; mandatory after startup | Selecting any task-specific document or creating, replacing, or preserving a document |
| [SESSION_HANDOFF.md](../../SESSION_HANDOFF.md) | Current state | Active state owner | `maintained-current`; mandatory | Every conversation start and task resume |
| [2026-07-20 R-1/R-1.1 and document-governance session](../../records/sessions/session.2026-07-20.r1-r1.1-document-governance.md) | Session record | Historical evidence only; current state remains in the handoff | `retained-evidence`; exact history route, not startup | Reviewing this session's conversation sequence, work, decisions, failures, or R-2A authorization history |
| [README.md](../../README.md) | User guide | Maintained projection | `maintained-current`; exact user route | Project orientation |
| [WORKFLOW.md](WORKFLOW.md) | Procedure | Active authority | `maintained-current`; task-routed | Planning, executing, validating, reporting, and closing work |
| [KNOWLEDGE_SYSTEM.md](KNOWLEDGE_SYSTEM.md) | Technical contract | Active approved foundation contract | `maintained-current`; task-routed | Creating or changing record and knowledge behavior |
| [CONTEXT_RETRIEVAL.md](CONTEXT_RETRIEVAL.md) | Technical contract | Active authority | `maintained-current`; task-routed | Selecting context or implementing retrieval |
| [KNOWLEDGE_MAINTENANCE.md](KNOWLEDGE_MAINTENANCE.md) | Procedure and contract | Active authority | `maintained-current`; task-routed | Reviewing stale, conflicting, superseded, or preserved material |
| [GUIDE.md](../user/GUIDE.md) | User guide | Maintained projection | `maintained-current`; exact user route | Operating and approving the project |
| [Existing project analysis](../reports/2026-07-20_기존_프로젝트_분석.md) | Report | Evidence only | `retained-evidence`; default excluded | Exact migration or historical analysis question |
| [Approved foundation and knowledge design](../reports/2026-07-20_프로젝트_기반_및_지식_시스템_설계.md) | Report | Accepted decision source for D-01 through D-11; further implementation is on hold pending correction | `retained-evidence`; exact decision lookup only | Tracing an accepted baseline decision or comparing the pending correction |
| [Foundation build result](../reports/2026-07-20_프로젝트_기본_기반_구축.md) | Report | Evidence only | `retained-evidence`; default excluded | Verifying what Command 3 actually built |
| [Final cross-validation](../../reports/최종_구축상태_교차검증보고.md) | Report | Evidence only | `retained-evidence`; default excluded | Auditing the four deleted source reports or the 36/100 correction trigger |
| [R-1 design correction marker](../reports/2026-07-20_R-1_지식_시스템_설계_정정.md) | Report | Superseded proposal; no current design authority | `superseded-evidence`; preservation marker only | Exact comparison with the replaced 11/18 proposal |
| [Pre-R-2 intent audit marker](../reports/2026-07-20_R-2_착수전_사용자_의도_정합성_검증.md) | Report | Evidence only | `retained-evidence`; preservation marker only | Auditing why R-1.1 was required |
| [R-1.1 corrected design](../reports/2026-07-20_R-1.1_지식_시스템_설계_보정.md) | Report and accepted decision source | Accepted D-01 through D-17 and R-2A implementation boundary | `retained-evidence`; exact R-2A route, not startup | Implementing or validating R-2A, or reviewing later R-2B-to-R-5 boundaries |
| [R-2A context-system implementation result](../reports/2026-07-20_R-2A_컨텍스트_시스템_구현_결과.md) | Report | R-2A implementation and validation evidence; no policy authority | `retained-evidence`; exact R-2A audit route | Auditing the completed R-2A thin slice |
| [R-2B corpus migration result](../reports/2026-07-21_R-2B_기존_지식_코퍼스_이관_결과.md) | Report | R-2B corpus implementation and validation evidence; no policy authority | `retained-evidence`; exact R-2B audit route | Auditing the completed corpus migration or deciding whether to approve R-3 |
| [R-3 resolver/writer generalization result](../reports/2026-07-21_R-3_resolver_writer_일반화_결과.md) | Report | R-3 implementation, maintenance, recovery, and validation evidence; no policy authority | `retained-evidence`; exact R-3 audit route | Auditing R-3 or establishing the measured R-4 baseline |
| [Document authority duplication case](../../knowledge/cases/case.project.document-authority-duplication.md) | Case record | Active resolved case evidence; prevention authority stays in the linked rules and workflow | `maintained-current`; task-routed, not startup | Creating or reviewing documents, reports, proposals, authority, preservation, or duplicate context behavior |

## Report routing and creation

1. Reports do not enter startup or default task context.
2. Read the R-1.1 report alone for the accepted staged design boundary; use the R-2A or R-2B result only for an exact implementation audit.
3. A stage transition does not by itself justify a new report file. Update the existing current proposal or owning authority when the subject is unchanged.
4. A new report requires a unique point-in-time evidence purpose that no existing document owns. It contains deltas, evidence, validation, and approval status; it links to technical owners instead of restating their full content.
5. Only one `current-proposal` may exist for a subject. Replaced proposals become `superseded-evidence` immediately.
6. When a superseded report substantially duplicates a current document, preserve its full committed snapshot by commit, blob, and content hash and keep only a short preservation marker in the working tree.
7. Every maintained document creation must pass the mandatory [document creation gate](WORKFLOW.md#document-creation-gate). A file without a unique owner and registry row is invalid even when its content is correct.

## Universal file and record catalogs

[`catalog/files.jsonl`](../../catalog/files.jsonl) is the canonical machine registry for every project-governed file. [`catalog/units.jsonl`](../../catalog/units.jsonl), [`catalog/rules.jsonl`](../../catalog/rules.jsonl), and [`catalog/records.jsonl`](../../catalog/records.jsonl) are rebuildable projections. Canonical corpus records live in the typed `knowledge/` stores and stable case documents. This document remains the human authority for maintained-document routing; it does not duplicate hashes, units, records, or work contracts.

## Document metadata contract

Every maintained document must state, near its beginning:

1. Purpose.
2. Use when.
3. Owner or author/editor responsibility.
4. Language.
5. Storage location and links to related authority.

Source quotations and historical artifacts are exempt from retroactive rewriting. Active reports use equivalent Korean labels.

## Placement rules

- Root: entrypoints, always-applicable policy, user overview, and current handoff only.
- `docs/agent/`: agent procedures and technical contracts in English.
- `docs/user/`: current user guidance in Korean.
- `docs/reports/`: Korean point-in-time reports and validation evidence.
- Existing `reports/` is a legacy evidence location for the final cross-validation report only; do not add new reports there.
- `knowledge/cases/`: stable Markdown case records. The current manual bootstrap record was explicitly user-authorized; it does not imply that schemas, writers, indexes, or other record kinds are implemented.
- `records/sessions/`: closed Markdown session records. The current manual record is historical evidence and does not replace `SESSION_HANDOFF.md` or imply that a session-summary writer exists.
- Future `records/work/`, other `knowledge/` kinds, and `context/`: structured data defined by the knowledge contracts, created only in their approved implementation stage.
- `backup/`: immutable historical material.

When adding a document, first verify that an existing owner cannot hold the content. Add a link instead of copying text, and register only durable active documents here.
