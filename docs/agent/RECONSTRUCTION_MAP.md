# Active Reconstruction Map

- Purpose: Map every retained project requirement to its self-contained active destination and record deferred or excluded capabilities.
- Scope: Reconstruction status and destination ownership only; source-history citations, current progress, and layer procedures belong elsewhere.
- Audience and language: Agents; English.
- Read when: Adding, changing, deferring, or removing a framework capability, or checking archive-retirement readiness.
- Write when: A retained requirement, active destination, reconstruction status, or reconsideration condition changes.
- Authority: This is the sole reconstruction-decision map. Active destinations, not the temporary migration archive, are authoritative.

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
| Rebuild discipline | Prefer small measured improvements, preserve user authority, and reject speculative infrastructure | `docs/agent/REBUILD_PRINCIPLES.md#core-principles` | implemented |
| Tool and AI roles | Deterministic tools verify repeatable behavior; AI interprets; users make creative and release decisions | `PROJECT_RULES.md#authorization-and-change-safety` | implemented |
| Validation vocabulary | Keep generated, parsed, structural, tool, application, and user validation distinct | `PROJECT_RULES.md#validation-and-reporting` | implemented |
| Failure stop | Stop after three consecutive failures in one active user execution request | `PROJECT_RULES.md#validation-and-reporting` | implemented |
| Source identity and state | Bind one source ID to one fingerprint and use one task-state authority | `docs/agent/FILE_DATA_CONTRACT.md` and `tools/state_io.py` | implemented |
| Output lifecycle | Reuse unchanged results; version changed results; preserve prior and failed files | `docs/agent/FILE_DATA_CONTRACT.md#lifecycle-and-retention-rules` | implemented |

## Reconstructed requirements for later layers

| Capability | Retained behavior | Active authority | Activation | Status |
|---|---|---|---:|---|
| Production routes and stage responsibilities | Pre-shoot and recorded-footage routes, analysis before planning, stage boundaries, gates, and user decisions | `docs/agent/WORKFLOW_FOUNDATION.md` | L5 | specified |
| Evidence-based planning | Audience promise, one central message, evidence spine, character change, counterevidence, calibration brief, and self-review | `docs/agent/WORKFLOW_FOUNDATION.md#planning-requirements` | L5 | specified |
| Editing quality judgment | Candidate ranges, microbeats, rhythm modes, sampling, evidence separation, self-validation, and promotion gates | `docs/agent/EDITING_QUALITY_RULES.md` | L5 and L8 | specified |
| Reusable media and workflow tools | State, media inspection, remux, source evidence, sync advisory, export, and audit behavior | `docs/agent/TOOL_REQUIREMENTS.md` | L7 | specified |
| Stage skill contract | Minimum inputs, outputs, gates, stops, user decisions, and next-stage handoff | `docs/agent/SKILL_REQUIREMENTS.md` | L8 | specified |

## Deferred capabilities

| Capability | Reason | Reconsider only when |
|---|---|---|
| SQLite and domain/service/storage layers | Excessive cost for sequential single-user file work | File state repeatedly fails under real concurrency or query load |
| Event-sourced editing memory | High input and maintenance cost | Current/prior state repeatedly loses important feedback |
| Full machine transition graph | Duplicates human-readable rules and state | The concise workflow repeatedly permits the same invalid transition |
| Work claims and completion receipts | Duplicates state in a single-writer workflow | Concurrent framework edits repeatedly collide |
| Mandatory hooks and CI | Installation and environment cost | A manual integrated check repeatedly fails to prevent the same regression |
| Broad CLI wrapper | Adds indirection without functional value | Command discovery becomes a measured repeated cost |

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
