# Knowledge System Contract

- Purpose: Define the canonical knowledge categories, provenance requirements, lifecycle boundaries, and closed data flow for future implementation.
- Use when: Designing, creating, validating, or changing work records, knowledge items, decisions, cases, relations, or session summaries.
- Owner: The approved architecture is user-controlled; project agents maintain the contract and propose material changes.
- Language: English, while preserving source passages in their original language with metadata.
- Location: `docs/agent/KNOWLEDGE_SYSTEM.md`. Derived from the [approved design report](../reports/2026-07-20_프로젝트_기반_및_지식_시스템_설계.md), constrained by [PROJECT_RULES.md](../../PROJECT_RULES.md), and paired with [retrieval](CONTEXT_RETRIEVAL.md) and [maintenance](KNOWLEDGE_MAINTENANCE.md).

## Current implementation status

R-2A provides the project-file and task-context thin slice. R-2B adds formal decision, knowledge, case, source, and relation schemas; canonical JSONL stores for 17 accepted decisions, four verified knowledge items, seven sources, and six typed relations; a schema-backed JSON record inside the existing stable case document; and a rebuildable record projection. The resolver now selects exact record IDs, verified active one-hop relations, and source locators in the same work context. General record lifecycle writers, review-history automation, databases, and search indexes remain unimplemented and require later stage approval.

## Canonical categories

Keep these data types physically and semantically separate:

1. Append-only original work events.
2. Immutable session summaries and the single current handoff.
3. Verified atomic knowledge items.
4. Decisions with options, rationale, scope, and approval state.
5. Problem, failure, and resolution cases.
6. Typed relationship records.
7. Append-only revision and review history.
8. Derived task context packages.

R-2B canonical decisions and atomic knowledge items use JSONL. Stable case documents remain human-reviewable Markdown and contain a formal schema-backed JSON record; summaries remain Markdown. Sources, relationships, ordered events, and future revision history use JSONL. JSON Schema Draft 2020-12 defines the active machine-readable contracts. Any later SQLite index remains a rebuildable projection.

## Required knowledge metadata

Every knowledge item must include:

- stable ID, kind, title, schema version, and language;
- fact, inference, procedure, or constraint classification;
- creation and update timestamps with timezone;
- author and validator;
- status and retrieval eligibility;
- low, medium, or high confidence plus a written basis;
- source references with stable locators and observed dates;
- related item IDs and typed relationship records;
- validity range, last check, and either a review due date or an explicit user-approved event-driven review policy with a null due date and named immediate triggers;
- revision number and link to append-only update history.

Confidence, retrieval score, or LLM authorship never replaces validation status.

## Provenance

- Repository sources use project-relative POSIX paths, stable locators, and content hashes.
- Work-derived knowledge links to exact session and event ranges.
- Web sources record direct URL, title, publication date when available, and observation date.
- Inferences link to every supporting fact and state the reasoning basis without storing hidden model reasoning.
- Decisions link to considered options, evidence, approver, scope, and superseding decision where applicable.

## Lifecycle

- Knowledge: `candidate -> reviewed -> verified -> needs_review -> superseded/rejected`.
- Decision: `proposed -> accepted -> superseded/revoked`.
- Case: `observed -> confirmed -> resolved/recurring -> retired`.
- Relationship: `candidate -> active -> invalidated`.

Default retrieval uses verified knowledge, accepted decisions, and state-appropriate cases only. Discovery output may show lower states in a clearly separated section when explicitly requested.

## Closed data flow

```text
work record
  -> knowledge extraction as candidate
  -> source and metadata assignment
  -> typed relationship creation
  -> structural, provenance, semantic, freshness, and approval validation
  -> rebuildable search indexing
  -> bounded task context package
  -> performed and verified task result
  -> new work event, candidates, decisions, cases, and review updates
```

An LLM may help extract or summarize candidates, but schema validation, source tracing, indexing, retrieval, and context manifest generation must remain usable without LLM memory.

## Data boundary

Global knowledge must be reusable and independent of protected task content. Task-specific knowledge remains inside the explicitly authorized task scope. Promotion to global knowledge requires sanitization, source review, and removal of secrets, personal absolute paths, and unnecessary user content.
