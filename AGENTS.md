# Agent Entry Point

- Purpose: Route an agent to the minimum authoritative project context without duplicating project rules or procedures.
- Use when: At the start of every conversation and before selecting task-specific documents.
- Owner: Project agents maintain this router; changes to authority or mandatory behavior require user approval.
- Language: English.
- Location: Project root. Links to [PROJECT_RULES.md](PROJECT_RULES.md), [DOCUMENT_MAP.md](docs/agent/DOCUMENT_MAP.md), and [SESSION_HANDOFF.md](SESSION_HANDOFF.md).

## Mandatory startup

1. Before any other project action, locate and read every `PROJECT_RULES.md` in each project folder within the authorized workspace scope, completely.
2. Treat the root [PROJECT_RULES.md](PROJECT_RULES.md) as the active project's controlling rules.
3. Treat rule files under `backup/` as historical sources: observe their access-safety constraints while inspecting those snapshots, but do not activate superseded procedures or edit them.
4. Read [SESSION_HANDOFF.md](SESSION_HANDOFF.md) for the current checkpoint.
5. Use [DOCUMENT_MAP.md](docs/agent/DOCUMENT_MAP.md) to select only the documents required for the task.

## Routing

- Common execution procedure: [WORKFLOW.md](docs/agent/WORKFLOW.md)
- Knowledge record contract: [KNOWLEDGE_SYSTEM.md](docs/agent/KNOWLEDGE_SYSTEM.md)
- Retrieval and context contract: [CONTEXT_RETRIEVAL.md](docs/agent/CONTEXT_RETRIEVAL.md)
- Review and freshness contract: [KNOWLEDGE_MAINTENANCE.md](docs/agent/KNOWLEDGE_MAINTENANCE.md)
- User-facing overview: [README.md](README.md) and [GUIDE.md](docs/user/GUIDE.md)

Do not copy detailed rules or current state into this file. Update the owning document and keep this file as a router.
