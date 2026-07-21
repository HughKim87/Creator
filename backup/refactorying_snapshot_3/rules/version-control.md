---
schema_version: 1.0.0
pack_id: version-control
kind: conditional_rules
language: en
owner: user-approved, agent-maintained
---

# Version Control Rules

- Purpose: Hold the task-scoped version-history rule.
- Use when: Selected for backup, recovery, or tracked-file history decisions.
- Owner: The user approves policy; project agents maintain accepted records.
- Language: English.
- Location: `rules/version-control.md`. Governed by [PROJECT_RULES.md](../PROJECT_RULES.md) and parsed by [context_system.py](../tools/context/context_system.py).

## rule.version-control.no-ad-hoc-backup

```json
{
  "schema_version": "1.0.0",
  "rule_id": "rule.version-control.no-ad-hoc-backup",
  "text": "Do not create ad hoc duplicate backup files. Use version history unless the user explicitly requests another backup method.",
  "authority": "project_rule",
  "priority": 500,
  "status": "active",
  "applies_when": {"any": [{"field": "task_tags", "op": "intersects", "value": ["backup", "recovery", "version_control"]}, {"field": "actions", "op": "intersects", "value": ["move", "delete"]}]},
  "excludes_when": [],
  "phases": ["plan", "write", "validate", "close"],
  "task_tags": ["version_control", "backup"],
  "source_refs": ["src.repo.project-rules#2.5"],
  "validators": ["validate.backup_policy"]
}
```
