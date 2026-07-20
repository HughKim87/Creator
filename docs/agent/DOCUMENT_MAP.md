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
| Procedure | How to perform a class of work. |
| Technical contract | Data, retrieval, or maintenance behavior to implement and verify. |
| User guide | Human-readable explanation; not an agent instruction authority. |
| Report | Point-in-time evidence and recommendation; not automatically active policy. |
| Historical source | Read-only evidence under `backup/`; never an active dependency. |

## Active document registry

| Document | Class | Audience | Read when | Maintainer | Related authority |
|---|---|---|---|---|---|
| [AGENTS.md](../../AGENTS.md) | Router | Agent | Every conversation start | Agent | Routes to rules, handoff, and this map |
| [PROJECT_RULES.md](../../PROJECT_RULES.md) | Policy | Agent | Every conversation start and throughout work | User-approved, agent-maintained | Highest persistent project policy |
| [SESSION_HANDOFF.md](../../SESSION_HANDOFF.md) | Current state | Agent | Every conversation start and task resume | Finishing agent | Links to evidence; does not copy general rules |
| [README.md](../../README.md) | User guide | User | Project orientation | Agent | Links to Korean guide and reports |
| [WORKFLOW.md](WORKFLOW.md) | Procedure | Agent | Planning, executing, validating, and closing work | Agent | Must comply with project rules |
| [KNOWLEDGE_SYSTEM.md](KNOWLEDGE_SYSTEM.md) | Technical contract | Agent | Creating or changing record and knowledge behavior | User-approved design, agent-maintained | Owns canonical knowledge categories and flow |
| [CONTEXT_RETRIEVAL.md](CONTEXT_RETRIEVAL.md) | Technical contract | Agent | Selecting context or implementing retrieval | Agent | Owns routing, retrieval, and package boundaries |
| [KNOWLEDGE_MAINTENANCE.md](KNOWLEDGE_MAINTENANCE.md) | Procedure and contract | Agent | Reviewing stale, conflicting, or superseded knowledge | Agent; material decisions require user | Owns lifecycle and review behavior |
| [GUIDE.md](../user/GUIDE.md) | User guide | User | Operating and approving the project | Agent | Korean projection of active behavior |
| [Existing project analysis](../reports/2026-07-20_기존_프로젝트_분석.md) | Report | User | Reviewing migration evidence | Agent | Input to the approved design |
| [Foundation and knowledge design](../reports/2026-07-20_프로젝트_기반_및_지식_시스템_설계.md) | Report | User | Reviewing the approved architecture and phase boundaries | Agent | Design source for foundation and future implementation |

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
- Future `records/`, `knowledge/`, and `context/`: structured data defined by the knowledge contracts, created only in the approved implementation stage.
- `backup/`: immutable historical material.

When adding a document, first verify that an existing owner cannot hold the content. Add a link instead of copying text, and register only durable active documents here.
