# Rule Governance

- Purpose: keep startup context small while ensuring conditional rules are discoverable, applied, and improved from verified experience.
- Read when: adding, changing, consolidating, or auditing project rules, and before completing controlled work.
- Authority: [PROJECT_RULES.md](../../PROJECT_RULES.md) is higher authority and owns conditional routing.

## Rule placement

- Keep universally required boundaries in `PROJECT_RULES.md`; do not move conditional procedure into startup policy.
- Put a conditional behavior in the narrowest existing owner whose trigger already covers it.
- Add a new rule only when the behavior has a distinct trigger and no existing owner can express it without mixing responsibilities.
- Keep domain procedure with its extension owner. Do not promote one task's facts, wording, or artifacts into project-wide rules.
- Prefer a compact invariant derived from evidence over copied session narratives, raw logs, or long examples.

## Rule shape

Every active `core/rules/*.md` file must state:

- `Purpose`: the durable outcome it protects;
- `Read when`: the observable trigger that routes to it;
- `Authority`: the higher policy or decision owner.

Operational rules should make the condition, required action, exception, and verification distinguishable. If a new rule only restates a higher rule, merge or remove it.

## Routing and graph

- [PROJECT_RULES.md](../../PROJECT_RULES.md) is the single rule router. Do not create a parallel rule index.
- Link every active `core/rules/*.md` file exactly once from its matching route in `PROJECT_RULES.md`.
- Read only the rules matched by the current task, once per logical task. Do not preload the complete rule set.
- Markdown links provide both agent routing and Obsidian graph edges; plain code paths are not sufficient navigation.

## Controlled closeout

Before completing controlled work, review each rule that matched the task and classify the evidence:

1. applied with no gap;
2. existing owner needs a concise strengthening;
3. verified recurrence belongs in an existing failure case;
4. a distinct trigger requires a new owner.

Change rules only with evidence from the current work or verified history. Core changes still require exact user approval under core change control. Do not create a separate closeout report unless the user requested one.

## Verification

- Confirm routing links are complete, unique, and point to existing files.
- Check the scoped diff, strict UTF-8, NUL bytes, trailing whitespace, and relevant links.
- Run the approved core verification gate after any authorized `core/**` change.
