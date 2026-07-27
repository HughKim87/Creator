# Claude Entry Point

- Purpose: give Claude the shared agent startup and routing rules plus only the tool mapping needed to apply them.
- Authority: `AGENTS.md` owns shared startup, classification, and routing; `PROJECT_RULES.md` owns policy; `SESSION_HANDOFF.md` owns current work state. This file adds no policy.

@AGENTS.md

## Claude tool mapping

- Read every startup and routed rule completely with Claude's file-reading tool.
- Search paths and text with Claude's file search tools; use the shell only for execution such as tests, scripts, and Git.
- Treat task-list tools as progress displays, not as additional plan documents.
- Never pass a path containing an `inputs` or `outputs` segment to a tool unless the user approved the exact item and purpose.
- Route creation or changes under `.agents/skills/` through `extension/README.md` and the exact active owner.
