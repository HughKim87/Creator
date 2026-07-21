---
schema_version: 1.0.0
pack_id: provenance
kind: conditional_rules
language: en
owner: user-approved, agent-maintained
---

# Provenance Rules

- Purpose: Hold task-scoped claim, source, language, and decision provenance rules.
- Use when: Selected for analysis, research, translation, factual claims, inferences, or decisions.
- Owner: The user approves policy; project agents maintain accepted records.
- Language: English.
- Location: `rules/provenance.md`. Governed by [PROJECT_RULES.md](../PROJECT_RULES.md) and parsed by [context_system.py](../tools/context/context_system.py).

## rule.provenance.preserve-source-language

```json
{
  "schema_version": "1.0.0",
  "rule_id": "rule.provenance.preserve-source-language",
  "text": "Preserve source text in its original language when accuracy or provenance requires it, and record the language instead of silently translating the source.",
  "authority": "project_rule",
  "priority": 500,
  "status": "active",
  "applies_when": {"any": [{"field": "task_tags", "op": "intersects", "value": ["source", "translation", "provenance"]}, {"field": "target_kinds", "op": "intersects", "value": ["source", "report"]}]},
  "excludes_when": [],
  "phases": ["read", "write", "validate"],
  "task_tags": ["provenance", "language"],
  "source_refs": ["src.repo.project-rules#3.3"],
  "validators": ["validate.source_language"]
}
```

## rule.provenance.claim-classification

```json
{
  "schema_version": "1.0.0",
  "rule_id": "rule.provenance.claim-classification",
  "text": "Distinguish verified facts, historical claims, inferences, proposals, and accepted decisions explicitly.",
  "authority": "project_rule",
  "priority": 500,
  "status": "active",
  "applies_when": {"any": [{"field": "target_kinds", "op": "intersects", "value": ["report", "case", "knowledge", "decision"]}, {"field": "task_tags", "op": "intersects", "value": ["analysis", "provenance"]}]},
  "excludes_when": [],
  "phases": ["read", "write", "validate", "close"],
  "task_tags": ["provenance", "claims"],
  "source_refs": ["src.repo.project-rules#4.1"],
  "validators": ["validate.claim_classification"]
}
```

## rule.provenance.source-and-rationale

```json
{
  "schema_version": "1.0.0",
  "rule_id": "rule.provenance.source-and-rationale",
  "text": "Record a source and stable locator for factual claims. Record supporting facts and rationale for inferences. Record options, rationale, scope, and approver for decisions.",
  "authority": "project_rule",
  "priority": 500,
  "status": "active",
  "applies_when": {"any": [{"field": "target_kinds", "op": "intersects", "value": ["report", "knowledge", "decision", "case"]}, {"field": "task_tags", "op": "intersects", "value": ["analysis", "decision", "provenance"]}]},
  "excludes_when": [],
  "phases": ["read", "write", "validate", "close"],
  "task_tags": ["provenance", "source"],
  "source_refs": ["src.repo.project-rules#4.2"],
  "validators": ["validate.source_trace"]
}
```

## rule.provenance.current-primary-source

```json
{
  "schema_version": "1.0.0",
  "rule_id": "rule.provenance.current-primary-source",
  "text": "Prefer current official or primary sources for technical facts that may change, and record the observation date.",
  "authority": "project_rule",
  "priority": 500,
  "status": "active",
  "applies_when": {"any": [{"field": "task_tags", "op": "intersects", "value": ["research", "technical_fact", "current_fact"]}, {"field": "target_kinds", "op": "intersects", "value": ["source", "technical_report"]}]},
  "excludes_when": [],
  "phases": ["discover", "read", "write", "validate"],
  "task_tags": ["provenance", "research"],
  "source_refs": ["src.repo.project-rules#4.3"],
  "validators": ["validate.primary_source"]
}
```
