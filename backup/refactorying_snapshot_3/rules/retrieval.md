---
schema_version: 1.0.0
pack_id: retrieval
kind: conditional_rules
language: en
owner: user-approved, agent-maintained
---

# Retrieval Rules

- Purpose: Hold task-scoped direct-routing, context-budget, projection, and exclusion rules.
- Use when: Selected for context assembly, routing, catalog, unit, or retrieval work.
- Owner: The user approves policy; project agents maintain accepted records.
- Language: English.
- Location: `rules/retrieval.md`. Governed by [PROJECT_RULES.md](../PROJECT_RULES.md) and parsed by [context_system.py](../tools/context/context_system.py).

## rule.retrieval.direct-routing-first

```json
{
  "schema_version": "1.0.0",
  "rule_id": "rule.retrieval.direct-routing-first",
  "text": "Use direct routing to known authoritative documents before broad search.",
  "authority": "project_rule",
  "priority": 500,
  "status": "active",
  "applies_when": {"any": [{"field": "phase", "op": "in", "value": ["discover", "read"]}, {"field": "target_paths", "op": "nonempty", "value": true}]},
  "excludes_when": [],
  "phases": ["discover", "read", "plan", "write"],
  "task_tags": ["retrieval", "routing"],
  "source_refs": ["src.repo.project-rules#5.1"],
  "validators": ["validate.direct_route"]
}
```

## rule.retrieval.minimum-context

```json
{
  "schema_version": "1.0.0",
  "rule_id": "rule.retrieval.minimum-context",
  "text": "Retrieve only the context required for the current task and respect explicit include and exclude scopes.",
  "authority": "project_rule",
  "priority": 500,
  "status": "active",
  "applies_when": {"any": [{"field": "phase", "op": "in", "value": ["discover", "read", "plan"]}, {"field": "task_tags", "op": "intersects", "value": ["retrieval", "context"]}]},
  "excludes_when": [],
  "phases": ["discover", "read", "plan", "write"],
  "task_tags": ["retrieval", "context"],
  "source_refs": ["src.repo.project-rules#5.2"],
  "validators": ["validate.context_scope"]
}
```

## rule.retrieval.projections-not-authority

```json
{
  "schema_version": "1.0.0",
  "rule_id": "rule.retrieval.projections-not-authority",
  "text": "Treat indexes, search scores, generated summaries, views, and context packages as rebuildable projections, never as the source of truth.",
  "authority": "project_rule",
  "priority": 500,
  "status": "active",
  "applies_when": {"any": [{"field": "target_kinds", "op": "intersects", "value": ["catalog_projection", "index", "work_context", "summary"]}, {"field": "task_tags", "op": "intersects", "value": ["retrieval", "projection"]}]},
  "excludes_when": [],
  "phases": ["discover", "read", "write", "validate"],
  "task_tags": ["retrieval", "projection"],
  "source_refs": ["src.repo.project-rules#5.3"],
  "validators": ["validate.projection_authority"]
}
```

## rule.retrieval.default-exclusions

```json
{
  "schema_version": "1.0.0",
  "rule_id": "rule.retrieval.default-exclusions",
  "text": "Exclude backup, protected user data, secrets, caches, and generated indexes from global indexing by default.",
  "authority": "project_rule",
  "priority": 500,
  "status": "active",
  "applies_when": {"any": [{"field": "phase", "op": "in", "value": ["discover", "read"]}, {"field": "task_tags", "op": "intersects", "value": ["retrieval", "index", "inventory"]}]},
  "excludes_when": [],
  "phases": ["discover", "read", "plan", "validate"],
  "task_tags": ["retrieval", "boundary"],
  "source_refs": ["src.repo.project-rules#5.5"],
  "validators": ["validate.protected_exclusion"]
}
```
