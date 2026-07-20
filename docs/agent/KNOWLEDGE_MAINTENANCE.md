# Knowledge Maintenance Contract

- Purpose: Define how project knowledge is reviewed, refreshed, conflicted, superseded, and retired without losing provenance.
- Use when: A source changes, a review date passes, a test fails, knowledge conflicts, or a decision is replaced.
- Owner: Project agents perform evidence-backed maintenance; the user approves material policy, scope, and creative decisions.
- Language: English.
- Location: `docs/agent/KNOWLEDGE_MAINTENANCE.md`. Applies to records defined by [KNOWLEDGE_SYSTEM.md](KNOWLEDGE_SYSTEM.md) and search eligibility defined by [CONTEXT_RETRIEVAL.md](CONTEXT_RETRIEVAL.md).

## Current implementation status

R-3 records contract-gated text, code, config, binary, move, and delete operations; restores all touched paths after a partial failure; and links a successful retry to the rejected or failed event. `maintain-knowledge` creates non-eligible candidates, performs hash-and-revision-gated reviews and revisions, and preserves superseded knowledge beside a replacement candidate and pending typed relation. `check-sources` compares registered project-document hashes, changes mismatched sources and dependent knowledge to `needs_review`, and appends review and revision evidence; `maintain-source` accepts a reviewed current hash only when the source has not changed again. Automated scheduling, case and decision lifecycle writers, review queues, and search reindexing remain unimplemented because they are outside R-3.

## Review triggers

Create a review requirement when any of the following occurs:

- a repository source hash changes or the locator disappears;
- an official source is unavailable, updated, or replaced;
- `review_due_at` passes;
- a governing rule, schema, or accepted decision is superseded or revoked;
- a reproduction or regression test fails;
- new evidence contradicts, invalidates, or narrows an existing item;
- task results reveal an unrecorded boundary or repeated failure.
- the user explicitly requests review of an item or its governing subject.

Detection changes status to `needs_review`; it never deletes knowledge or silently rewrites the claim.

## Event-driven review without a periodic deadline

A record may omit a periodic review date only when the user explicitly approves event-driven review for that record or class. Such a record must set `review_policy=event_driven`, `review_due_at=null`, identify the approving user decision, and list concrete triggers that cause immediate review. A null date means “review on trigger,” never “do not review.”

When a listed trigger occurs or the user asks for review, mark the item `needs_review` before reusing its resolution as current guidance, perform the review in the same task when authorized, and append the result to its change history.

## Review procedure

1. Resolve the current item, revision history, source references, relationships, and dependent records.
2. Verify the source at its recorded locator and compare its current hash or publication state.
3. Reassess fact versus inference classification, scope, confidence basis, and retrieval eligibility.
4. Preserve conflicting claims and link them with `contradicted_by` until authority and scope resolve the conflict.
5. Choose one explicit outcome: keep, narrow scope, revise, supersede, reject, revoke, or retire.
6. Append a history event with old and new hashes, actor, timestamp, reason, evidence, and related decision or review ID.
7. Rebuild the derived index and rerun affected retrieval evaluations.

## Authority-specific behavior

- Project instructions follow current user direction, active project rules, and accepted decisions.
- Technical facts prefer current official or primary sources and reproducible project tests.
- Creative choices remain the user's authority unless explicitly delegated.
- Historical reports remain evidence of what was claimed or tested at that time; they do not automatically override current verified knowledge.

## Conflict and replacement

Never overwrite a conflict to produce one apparently clean answer. Keep both records, their dates, scopes, sources, and relationship. A new record may supersede an old one only with an explicit reason and authority. Superseded records stay available for historical questions but are excluded from default current-context retrieval.

## Maintenance outputs

Each completed review must produce:

- a review record and append-only history event;
- updated current record metadata and status;
- relationship changes where required;
- a rebuilt index manifest when an index is selected, or the R-4 measured `not_needed_baseline_passed` decision and logical result hash when no index exists;
- affected evaluation results;
- a handoff update when the change affects current work.

R-3 structured knowledge and source review operations must use the lifecycle commands and append-only history stores. Record kinds without an implemented lifecycle writer remain manual evidence in the active Korean report and [SESSION_HANDOFF.md](../../SESSION_HANDOFF.md); do not claim automated maintenance for those kinds.
