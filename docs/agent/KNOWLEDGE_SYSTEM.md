# Knowledge System Contract

- Purpose: Define the canonical knowledge categories, provenance requirements, lifecycle boundaries, and closed data flow for future implementation.
- Use when: Designing, creating, validating, or changing work records, knowledge items, decisions, cases, relations, or session summaries.
- Owner: The approved architecture is user-controlled; project agents maintain the contract and propose material changes.
- Language: English, while preserving source passages in their original language with metadata.
- Location: `docs/agent/KNOWLEDGE_SYSTEM.md`. Derived from the [approved design report](../reports/2026-07-20_프로젝트_기반_및_지식_시스템_설계.md), constrained by [PROJECT_RULES.md](../../PROJECT_RULES.md), and paired with [retrieval](CONTEXT_RETRIEVAL.md) and [maintenance](KNOWLEDGE_MAINTENANCE.md).

## Current implementation status

This file is an approved foundation contract, not a general implementation claim. One user-authorized manual case record exists at [case.project.document-authority-duplication](../../knowledge/cases/case.project.document-authority-duplication.md), and one user-requested closed manual [session record](../../records/sessions/session.2026-07-20.r1-r1.1-document-governance.md) preserves the current conversation and work history. Schemas, writers, automated validators, event stores, databases, and indexes do not yet exist; both records identify their manual bootstrap status.

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

Markdown holds human-reviewable knowledge, decisions, cases, and summaries. JSONL holds ordered events, relationships, and revision history. JSON Schema Draft 2020-12 will define machine-readable contracts. A local SQLite index will remain a rebuildable projection.

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
