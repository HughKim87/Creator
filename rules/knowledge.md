---
schema_version: 1.0.0
pack_id: knowledge
kind: conditional_rules
language: en
owner: user-approved, agent-maintained
---

# Knowledge Rules

- Purpose: Hold task-scoped verification and conflict-preservation rules for knowledge work.
- Use when: Selected for knowledge, case, confidence, conflict, or supersession changes.
- Owner: The user approves policy; project agents maintain accepted records.
- Language: English.
- Location: `rules/knowledge.md`. Governed by [PROJECT_RULES.md](../PROJECT_RULES.md) and parsed by [context_system.py](../tools/context/context_system.py).

## rule.knowledge.confidence-is-not-verification

```json
{
  "schema_version": "1.0.0",
  "rule_id": "rule.knowledge.confidence-is-not-verification",
  "text": "A high confidence score, search rank, summary, or LLM output does not convert a candidate into verified knowledge.",
  "authority": "project_rule",
  "priority": 500,
  "status": "active",
  "applies_when": {"any": [{"field": "target_kinds", "op": "intersects", "value": ["knowledge", "case", "candidate"]}, {"field": "task_tags", "op": "intersects", "value": ["knowledge", "confidence"]}]},
  "excludes_when": [],
  "phases": ["read", "write", "validate"],
  "task_tags": ["knowledge", "verification"],
  "source_refs": ["src.repo.project-rules#4.4"],
  "validators": ["validate.knowledge_status"]
}
```

## rule.knowledge.preserve-conflicts

```json
{
  "schema_version": "1.0.0",
  "rule_id": "rule.knowledge.preserve-conflicts",
  "text": "Preserve conflicts and superseded knowledge through status and relationships; do not silently overwrite history.",
  "authority": "project_rule",
  "priority": 500,
  "status": "active",
  "applies_when": {"any": [{"field": "target_kinds", "op": "intersects", "value": ["knowledge", "case", "decision"]}, {"field": "task_tags", "op": "intersects", "value": ["conflict", "supersession"]}]},
  "excludes_when": [],
  "phases": ["read", "write", "validate"],
  "task_tags": ["knowledge", "history"],
  "source_refs": ["src.repo.project-rules#4.5"],
  "validators": ["validate.conflict_history"]
}
```
