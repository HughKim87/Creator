# Document Index — Video Workflow

- Updated: 2026-07-15
- Role: router that selects only the documents needed. No work state lives here.

## Default Load

1. `PROJECT_BOOTSTRAP.md`
2. `docs/INDEX.md`

For continuing work, read `SESSION_HANDOFF.md`, then the output state it routes to.
Load `PROJECT_RULES.md` per "Load Full Rules When" in `PROJECT_BOOTSTRAP.md`.

The root handoff is a reusable pointer. Current video state lives only in
`outputs/SESSION_HANDOFF.md` when that file exists.

## Router

| Situation | Read |
|---|---|
| Project entry overview | `README.md` |
| Continuing work | `SESSION_HANDOFF.md`, then `outputs/SESSION_HANDOFF.md` |
| Rules/safety/structure change | `PROJECT_RULES.md`, `docs/AGENT_MAINTENANCE.md` |
| Production stage decision | `01_youtube_production_workflow.md` |
| Phase gate, promotion, or workflow recovery | `docs/WORKFLOW_CONTRACT.json`, then `outputs/WORKFLOW_STATE.json` and `outputs/WORKFLOW_RULE_REGISTRY.json` |
| Stage 7 editing quality consistency | `docs/EDITING_QUALITY_STANDARD.md`, `skills/premiere-editing-export/SKILL.md` |
| Working principles | `PROJECT_RULES.md` |
| Five-stage planning | `skills/dialogue-based-planning/SKILL.md`, `planning_research/planning_stage_spec_2026-07-06.md` |
| Skill work | `skills/README.md`, `skills/SKILL_CONTRACT.md`, relevant `skills/*/SKILL.md` |
| Tool work | `tools/README.md`, then specific tool help |
| Multi-agent workflow/tool adoption | `planning_research/multi_agent_file_workflow_solution_research_2026-07-14.md` |
| Past operational diagnosis | `planning_research/project_ops_diagnosis_and_improvements_2026-07-07.md` |

## Reference Documents

- `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`: per-platform entry pointers
- `PROJECT_BOOTSTRAP.md`: minimal always-loaded kernel
- `PROJECT_RULES.md`: conditional full rule source
- `docs/AGENT_MAINTENANCE.md`: document maintenance checklist
- `skills/SKILL_CONTRACT.md`: shared skill authoring contract
- `.geminiignore`: Gemini context exclusion list

## Load Principles

- Read selected instruction documents to the end.
- Do not bulk-load long reports or retired documents.
- Do not copy another document's procedures into a document.
- Do not pin commit SHAs or worktree state that Git can report.
