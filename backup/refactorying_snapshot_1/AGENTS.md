# AGENTS.md

- Role: minimal startup router for every agent.
- First read `PROJECT_RULES.md` completely.
- Then read `SESSION_HANDOFF.md` for current state.
- For execution, read `docs/improvement/LAYER_PLAN.md` and only the current layer
  section routed by `SESSION_HANDOFF.md`.
- `docs/rebuild/` is retired history (9-stage rewrite plan, deprecated 2026-07-18).
  Do not use it as an execution source.
- Read `backup/` files only when the active stage routes to one specific framework file.
- Do not duplicate rules here; `PROJECT_RULES.md` is authoritative.
- After writes, run the available project checks and report any unavailable check.
