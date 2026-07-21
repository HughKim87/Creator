---
schema_version: 1.0.0
pack_id: documentation
kind: conditional_rules
language: en
owner: user-approved, agent-maintained
---

# Documentation Rules

- Purpose: Hold task-scoped language and maintained-document metadata rules.
- Use when: Selected for reports, guides, agent documents, or maintained Markdown changes.
- Owner: The user approves policy; project agents maintain accepted records.
- Language: English.
- Location: `rules/documentation.md`. Governed by [PROJECT_RULES.md](../PROJECT_RULES.md) and parsed by [context_system.py](../tools/context/context_system.py).

## rule.documentation.user-korean

```json
{
  "schema_version": "1.0.0",
  "rule_id": "rule.documentation.user-korean",
  "text": "Write user-facing guides, reports, and approval summaries in Korean.",
  "authority": "project_rule",
  "priority": 500,
  "status": "active",
  "applies_when": {"any": [{"field": "output_audience", "op": "eq", "value": "user"}, {"field": "target_kinds", "op": "intersects", "value": ["report", "user_guide"]}]},
  "excludes_when": [],
  "phases": ["plan", "write", "close"],
  "task_tags": ["documentation", "user_facing"],
  "source_refs": ["src.repo.project-rules#3.1"],
  "validators": ["validate.document_language"]
}
```

## rule.documentation.agent-english

```json
{
  "schema_version": "1.0.0",
  "rule_id": "rule.documentation.agent-english",
  "text": "Write agent operating documents, technical contracts, schemas, and maintenance instructions in English.",
  "authority": "project_rule",
  "priority": 500,
  "status": "active",
  "applies_when": {"any": [{"field": "target_kinds", "op": "intersects", "value": ["agent_document", "policy", "procedure", "technical_contract", "schema", "current_state"]}, {"field": "task_tags", "op": "intersects", "value": ["agent_facing", "schema"]}]},
  "excludes_when": [],
  "phases": ["plan", "write", "validate", "close"],
  "task_tags": ["documentation", "agent_facing"],
  "source_refs": ["src.repo.project-rules#3.2"],
  "validators": ["validate.document_language"]
}
```

## rule.documentation.required-metadata

```json
{
  "schema_version": "1.0.0",
  "rule_id": "rule.documentation.required-metadata",
  "text": "Every maintained document must state its purpose, use time, owner, language, location, and links to related authorities.",
  "authority": "project_rule",
  "priority": 500,
  "status": "active",
  "applies_when": {"any": [{"field": "actions", "op": "intersects", "value": ["create", "write"]}, {"field": "target_kinds", "op": "intersects", "value": ["report", "user_guide", "agent_document", "rule_pack", "current_state"]}]},
  "excludes_when": [],
  "phases": ["plan", "write", "validate", "close"],
  "task_tags": ["documentation", "metadata"],
  "source_refs": ["src.repo.project-rules#3.5"],
  "validators": ["validate.document_metadata"]
}
```
