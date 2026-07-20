---
doc_id: doc.registry
kind: decision_registry
domain: navigation
lifecycle: active
authority: normative for document classification and Obsidian discovery metadata
audience: agent
language: en
validation: tool_validated
purpose: Define the property schema and derived Obsidian index used to classify project documents.
scope: Active note metadata, domain folders, discovery surfaces, and classification changes; placement and naming procedures live in DOCUMENT_PLACEMENT.md.
read_when: Auditing document classification, changing the property schema, or resolving an unknown document domain.
write_when: A property key, domain, lifecycle class, discovery view, or non-note asset registration changes.
---
# Document Registry

## Classification properties

Every Markdown note below `docs/` declares its own authoritative classification in YAML frontmatter. Root control documents remain lightweight direct-startup files and keep their compact Markdown metadata.

| Property | Required meaning |
|---|---|
| `doc_id` | Stable `doc.<lower_snake_case>` identity that survives moves |
| `kind` | `requirements`, `contract`, `plan`, `principle`, `decision_registry`, `user_status`, or `report` |
| `domain` | One domain from the folder table below |
| `lifecycle` | `draft`, `active`, `deprecated`, `superseded`, or `historical` |
| `authority` | Exact ownership statement: `normative`, `derived`, or `evidence`, with the owned decision named |
| `audience` | `agent`, `user`, `both`, or `agent_tool` |
| `language` | `en` or `ko` |
| `validation` | `generated`, `structure_validated`, `tool_validated`, `app_validated`, or `user_validated` |
| `purpose` | The one durable question answered by the note |
| `scope` | Included content and nearest important exclusion |
| `read_when` | Concrete event that justifies loading the note |
| `write_when` | Exact durable change owned by the note |

A note is not an active authority until all twelve properties exist, the values match its folder and content, and governance tests pass. Classification lives once in the note properties; do not recreate a hand-maintained document table.

## Domain folders

| Domain | Folder | Boundary |
|---|---|---|
| `control` | repository root | Always-read router, global rules, and current handoff only |
| `navigation` | `docs/agent/navigation/` | Document discovery, classification, placement, and Obsidian index |
| `rebuild` | `docs/agent/rebuild/` | Rebuild principles, plan, and capability decisions |
| `workflow` | `docs/agent/workflow/` | Production and editing requirements |
| `tooling` | `docs/agent/tooling/` | Reusable tool and skill requirements |
| `state` | `docs/agent/state/` | Task-state meaning, operations, and machine schema |
| `user_status` | `docs/user/` | Current Korean milestone derived from the handoff |
| `history` | `docs/reports/` | Korean point-in-time evidence; never default execution input |

Folder location narrows Obsidian search but does not create authority. A note's properties and the exact `AGENTS.md` route remain decisive.

## Obsidian derived index

`docs/agent/navigation/AGENT_DOCUMENTS.base` is the official Obsidian Base over note properties. It is a generated view, not another source of truth.

- Human review uses its domain and lifecycle views instead of a manually maintained catalog.
- Agent discovery uses the exact domain view or a property/path-bounded search, receives paths only, then selects one note by `purpose` and `authority`.
- Known route IDs still use their exact paths because zero discovery output is cheaper than any search.
- Unknown work starts with one domain view. Cross-domain union is allowed only for explicit independent intents.
- Base or search failure, no result, ambiguity, or protected-path risk is reported; it never triggers an automatic fallback.

## Non-note assets

| ID | Path | Role |
|---|---|---|
| `asset.agent_documents_base` | `docs/agent/navigation/AGENT_DOCUMENTS.base` | Derived Obsidian property index |
| `doc.file_state_schema` | `docs/agent/state/schemas/video_task_state.schema.json` | Machine shape implementing `doc.file_state` |

Root `AGENTS.md`, `PROJECT_RULES.md`, and `SESSION_HANDOFF.md` are registered by their fixed startup roles rather than duplicated YAML properties. Implementation code and tests are linked from their owning note and are not document-index rows.

## Classification change protocol

1. Identify the affected note by exact path or `doc_id`.
2. Change only the properties whose durable meaning changed.
3. If the domain changes, follow `DOCUMENT_PLACEMENT.md#move-or-rename-procedure` in the same change.
4. Query the Base and verify the note appears in exactly one expected domain and lifecycle view.
5. Update `AGENTS.md` only when a recurring task's minimum read set changed.

## Maintenance checks

- Every Markdown note below `docs/` has the twelve required properties and a unique `doc_id`.
- Every note path matches its declared domain folder and lifecycle.
- The Base returns all property-managed notes and no protected-path item.
- Known routes resolve exact existing paths; unknown discovery returns at most three candidates.
- Local Markdown links, Obsidian links, schemas, implementation references, UTF-8, and NUL checks pass.
- `AGENTS.md`, `PROJECT_RULES.md`, and `SESSION_HANDOFF.md` remain within their context budgets.
