---
doc_id: doc.reconstruction
kind: decision_registry
domain: rebuild
lifecycle: active
authority: normative for capability reconstruction status and destination ownership
audience: agent
language: en
validation: structure_validated
purpose: Map every retained project requirement to its self-contained active destination and record deferred or excluded capabilities.
scope: Reconstruction status and destination ownership only; source-history citations, current progress, and layer procedures belong elsewhere.
read_when: Adding, changing, deferring, or removing a framework capability, or checking archive-retirement readiness.
write_when: A retained requirement, active destination, reconstruction status, or reconsideration condition changes.
---
# Active Reconstruction Map

## Status meanings

| Status | Meaning |
|---|---|
| `implemented` | The requirement is present in an active document, code path, or test and needs no migration source. |
| `specified` | The complete retained behavior is reconstructed in an active requirement document; implementation waits for its approved layer. |
| `deferred` | The capability is intentionally absent and has a measurable reconsideration condition. |
| `excluded` | The capability is intentionally omitted from this project design. |

No active task reads a migration source through this map. If a requirement is not sufficiently represented in
an active destination, it is incomplete and must be reconstructed before the dependent layer can finish.

## Implemented foundations

| Requirement | Retained behavior | Active authority | Status |
|---|---|---|---|
| Original and derivative boundaries | Protect user originals, separate derivatives, and prohibit automatic deletion | `PROJECT_RULES.md#workspace-and-data-boundaries` | implemented |
| Portable text and binary handling | Stable line endings and media binary classification across operating systems | `.gitattributes` | implemented |
| Minimum startup context | Start from global rules and current state, then read only task-routed authorities | `AGENTS.md#required-startup` | implemented |
| Rebuild discipline | Prefer small measured improvements, preserve user authority, and reject speculative infrastructure | `docs/agent/rebuild/REBUILD_PRINCIPLES.md#core-principles` | implemented |
| Tool and AI roles | Deterministic tools verify repeatable behavior; AI interprets; users make creative and release decisions | `PROJECT_RULES.md#authorization-and-change-safety` | implemented |
| Validation vocabulary | Keep generated, parsed, structural, tool, application, and user validation distinct | `PROJECT_RULES.md#validation-and-reporting` | implemented |
| Failure stop | Stop after three consecutive failures in one active user execution request | `PROJECT_RULES.md#validation-and-reporting` | implemented |
| Source identity and state | Bind one source ID to one fingerprint and use one versioned state-model authority | `docs/agent/state/VIDEO_TASK_STATE.md` and `tools/state_io.py` | implemented |
| State operations and output lifecycle | Read, write, promote, retain, approve, and consume only an exact designated task through the approved I/O path | `docs/agent/state/STATE_OPERATIONS.md` and `tools/state_io.py` | implemented |

## Reconstructed requirements for later layers

| Capability | Retained behavior | Active authority | Activation | Status |
|---|---|---|---:|---|
| Direct task-route navigation | Select stable route and write IDs directly from `AGENTS.md`, require explicit selectors, keep relationships non-expanding, and stop and report ambiguity or protected-path conflicts | `AGENTS.md#selection-protocol` and `docs/agent/navigation/DOCUMENT_PLACEMENT.md` | L3 and L3.3 | implemented |
| Obsidian local review client | Review original Markdown in domain folders with Properties, Bases, links, core navigation, protected-folder UI exclusions, and no cloud or community plugins | `docs/agent/rebuild/REBUILD_PLAN.md#document-navigation-integration-contract` | L3.1 and L3.3 | implemented |
| Obsidian CLI agent document discovery | Query the official Base or one domain folder, compare indexed properties, read one atomic note, and report failures without fallback | `docs/agent/tooling/TOOL_REQUIREMENTS.md#agent-document-discovery-contract` and `AGENTS.md#selection-protocol` | L3.2 and L3.3 | implemented |
| Obsidian property and Base architecture | Store active note classification in YAML Properties, derive the catalog through one Base, and use domain folders without a duplicate hand-maintained index | `docs/agent/navigation/DOCUMENT_REGISTRY.md` and `docs/agent/navigation/AGENT_DOCUMENTS.base` | L3.3 | implemented |
| Graphify document discovery and compatible-format route helpers | Do not retain semantic traversal or the custom typed helper: semantic comparison selected excess context, while the helper did not call Graphify and duplicated the direct route table | `docs/reports/2026-07-20_그래피파이_도입_실패_분석.md` and `docs/agent/rebuild/REBUILD_PLAN.md#l31--obsidian-baseline-and-graphify-evaluation` | Separate future approval plus new evidence only | excluded |
| Production routes and stage responsibilities | Pre-shoot and recorded-footage routes, analysis before planning, stage boundaries, gates, and user decisions | `docs/agent/workflow/WORKFLOW_FOUNDATION.md` | L5 | specified |
| Evidence-based planning | Audience promise, one central message, evidence spine, character change, counterevidence, calibration brief, and self-review | `docs/agent/workflow/WORKFLOW_FOUNDATION.md#planning-requirements` | L5 | specified |
| Editing quality judgment | Candidate ranges, microbeats, rhythm modes, sampling, evidence separation, self-validation, and promotion gates | `docs/agent/workflow/EDITING_QUALITY_RULES.md` | L5 and L8 | specified |
| Reusable media and workflow tools | State, media inspection, remux, source evidence, sync advisory, export, and audit behavior | `docs/agent/tooling/TOOL_REQUIREMENTS.md` | L7 | specified |
| Stage skill contract | Minimum inputs, outputs, gates, stops, user decisions, and next-stage handoff | `docs/agent/tooling/SKILL_REQUIREMENTS.md` | L8 | specified |

## Deferred capabilities

| Capability | Reason | Reconsider only when |
|---|---|---|
| SQLite and domain/service/storage layers | Excessive cost for sequential single-user file work | File state repeatedly fails under real concurrency or query load |
| Event-sourced editing memory | High input and maintenance cost | Current/prior state repeatedly loses important feedback |
| Full machine transition graph | Duplicates human-readable rules and state | The concise workflow repeatedly permits the same invalid transition |
| Work claims and completion receipts | Duplicates state in a single-writer workflow | Concurrent framework edits repeatedly collide |
| Mandatory hooks and CI | Installation and environment cost | A manual integrated check repeatedly fails to prevent the same regression |
| Broad CLI wrapper | Adds indirection without functional value | Command discovery becomes a measured repeated cost |
| Local semantic document analysis, including Ollama-backed options | Current direct routes and Obsidian Properties/Base select exact authorities without semantic inference; local-model indexing and inference add cost without a measured current benefit | Recurring queries cannot be resolved by direct routes or bounded Properties/Base discovery, the corpus has materially grown or contains substantial unclassified legacy content, and a same-corpus benchmark proves a candidate-only semantic fallback improves accuracy or total context; activation still requires separate approval and final authority verification through active document properties |

## Excluded capabilities

| Capability | Reason |
|---|---|
| Nine-stage development bureaucracy and evidence packages | Process management exceeds production value |
| Independent QA or red-team agent roles | The current one-person workflow needs quality checks, not role orchestration |
| Multi-role approval challenge, provenance, and quarantine protocols | The minimal verified-file promotion path covers the actual local risk |
| Complete historical CLI and state command set | Coupled to deferred storage and transition infrastructure |
| Caches, virtual environments, or generated reports as active authorities | Re-creatable outputs are not durable project knowledge |

## Archive-retirement readiness

The migration archive is eligible for a separately approved deletion only when all conditions pass:

1. Every retained row is `implemented` or `specified` in an existing active destination.
2. Active documents, code, tests, and command examples have no runtime or reading dependency on the archive.
3. Every later-layer implementation is tested from its active source without archive access.
4. Deferred and excluded capabilities have enough rationale to remain intentionally absent.
5. The document registry, routing tests, and a repository reference scan pass.
6. The user explicitly approves deletion after reviewing the readiness report.
