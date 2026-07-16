# AGENTS.md

- Role: minimal startup router for every agent.
- First read `PROJECT_RULES.md` completely.
- Then read `SESSION_HANDOFF.md` for current state.
- For execution, read `docs/rebuild/AGENT_EXECUTION_PLAN.md` and only the current stage
  document/report routed by `SESSION_HANDOFF.md`.
- Read `backup/` files only when the active stage routes to one specific framework file.
- Do not duplicate rules here; `PROJECT_RULES.md` is authoritative.
- After writes, run the available project checks and report any unavailable check.
