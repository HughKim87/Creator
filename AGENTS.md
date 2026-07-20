# Agent Entry Point

- Purpose: Route an agent to the minimum authoritative project context without duplicating project rules or procedures.
- Use when: At the start of every conversation and before selecting task-specific documents.
- Owner: Project agents maintain this router; changes to authority or mandatory behavior require user approval.
- Language: English.
- Location: Project root. Links to [PROJECT_RULES.md](PROJECT_RULES.md), [DOCUMENT_MAP.md](docs/agent/DOCUMENT_MAP.md), and [SESSION_HANDOFF.md](SESSION_HANDOFF.md).

## Mandatory startup

1. Read the root [PROJECT_RULES.md](PROJECT_RULES.md) completely as the active project's eight-rule boot kernel.
2. Do not discover or activate rule files under `backup/`, `inputs/`, or `outputs/`; `backup/` is historical evidence and the protected paths require exact user scope.
3. Read [SESSION_HANDOFF.md](SESSION_HANDOFF.md) as the only current checkpoint.
4. Read [DOCUMENT_MAP.md](docs/agent/DOCUMENT_MAP.md) to identify direct authorities.
5. For execution, resolve a structured task request with [`tools/context/context_system.py`](tools/context/context_system.py) and apply only the conditional rule IDs selected in its work context. If the resolver is unavailable, use the exact direct route and record that fallback instead of broad-loading `rules/`.

## Routing

- Common execution procedure: [WORKFLOW.md](docs/agent/WORKFLOW.md)
- Knowledge record contract: [KNOWLEDGE_SYSTEM.md](docs/agent/KNOWLEDGE_SYSTEM.md)
- Retrieval and context contract: [CONTEXT_RETRIEVAL.md](docs/agent/CONTEXT_RETRIEVAL.md)
- Review and freshness contract: [KNOWLEDGE_MAINTENANCE.md](docs/agent/KNOWLEDGE_MAINTENANCE.md)
- User-facing overview: [README.md](README.md) and [GUIDE.md](docs/user/GUIDE.md)

Do not copy detailed rules or current state into this file. Update the owning document and keep this file as a router.
