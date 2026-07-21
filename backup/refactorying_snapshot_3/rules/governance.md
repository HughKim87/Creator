---
schema_version: 1.0.0
pack_id: governance
kind: conditional_rules
language: en
owner: user-approved, agent-maintained
---

# Governance Rules

- Purpose: Hold task-scoped governance rules migrated from the original always-loaded policy.
- Use when: Selected by the resolver for staged work, authority ownership, or document-boundary changes.
- Owner: The user approves policy; project agents maintain accepted records.
- Language: English.
- Location: `rules/governance.md`. Governed by [PROJECT_RULES.md](../PROJECT_RULES.md) and parsed by [context_system.py](../tools/context/context_system.py).

## rule.governance.stage-approval

```json
{
  "schema_version": "1.0.0",
  "rule_id": "rule.governance.stage-approval",
  "text": "When work is divided into approval stages, finish and report the current stage, then wait for explicit approval before starting the next stage.",
  "authority": "project_rule",
  "priority": 500,
  "status": "active",
  "applies_when": {"any": [{"field": "task_tags", "op": "intersects", "value": ["stage", "approval"]}, {"field": "phase", "op": "in", "value": ["close"]}]},
  "excludes_when": [],
  "phases": ["plan", "write", "validate", "close"],
  "task_tags": ["stage", "approval"],
  "source_refs": ["src.repo.project-rules#1.3"],
  "validators": ["validate.approval_boundary"]
}
```

## rule.governance.single-owner

```json
{
  "schema_version": "1.0.0",
  "rule_id": "rule.governance.single-owner",
  "text": "Keep one authoritative owner for each rule, state, decision, and datum. A new stage, version, agent, or validation pass does not justify a duplicate owner or document. Update the existing owner and preserve earlier states in Git unless a distinct point-in-time evidence artifact is explicitly required; link instead of copying owned content.",
  "authority": "project_rule",
  "priority": 500,
  "status": "active",
  "applies_when": {"any": [{"field": "actions", "op": "intersects", "value": ["create", "write"]}, {"field": "task_tags", "op": "intersects", "value": ["documentation", "report", "catalog"]}]},
  "excludes_when": [],
  "phases": ["plan", "write", "validate", "close"],
  "task_tags": ["governance", "documentation"],
  "source_refs": ["src.repo.project-rules#1.4"],
  "validators": ["validate.single_owner"]
}
```

## rule.governance.document-boundaries

```json
{
  "schema_version": "1.0.0",
  "rule_id": "rule.governance.document-boundaries",
  "text": "Keep common rules in the policy owner. Put procedures, rebuild plans, technical designs, current state, and point-in-time reports in their designated documents.",
  "authority": "project_rule",
  "priority": 500,
  "status": "active",
  "applies_when": {"any": [{"field": "target_kinds", "op": "intersects", "value": ["policy", "procedure", "technical_contract", "current_state", "report"]}, {"field": "task_tags", "op": "intersects", "value": ["documentation", "design"]}]},
  "excludes_when": [],
  "phases": ["plan", "write", "validate"],
  "task_tags": ["governance", "documentation"],
  "source_refs": ["src.repo.project-rules#3.4"],
  "validators": ["validate.document_owner"]
}
```
