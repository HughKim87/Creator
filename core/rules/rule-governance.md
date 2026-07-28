# Rule Governance

- Purpose: keep startup context small while ensuring conditional rules are discoverable, applied, and improved from verified experience.
- Read when: adding, changing, consolidating, or auditing project rules, and before completing controlled work.
- Authority: [PROJECT_RULES.md](../../PROJECT_RULES.md) is higher authority and owns conditional routing.

## Rule placement

- Keep universally required boundaries in `PROJECT_RULES.md`; do not move conditional procedure into startup policy.
- Put a conditional behavior in the narrowest existing owner whose trigger already covers it.
- Add a new rule only when the behavior has a distinct trigger and no existing owner can express it without mixing responsibilities.
- Keep domain procedure with its extension owner. Do not promote one task's facts, wording, or artifacts into project-wide rules.
- Separate speaker and authority when using conversations, reports, or delegated results as evidence. An agent proposal does not become a user instruction or project policy without explicit approval from the applicable owner.
- Prefer a compact invariant derived from evidence over copied session narratives, raw logs, or long examples.

## Rule lifecycle

Treat a rule as a maintained operational interface with this lifecycle:

1. Identify the observable trigger and the durable outcome it protects.
2. Search the existing owner, router, contract, candidate document, and failure index.
3. Reuse or strengthen the narrowest existing owner when it can express the behavior without mixing responsibilities.
4. Create a new rule only when the trigger, reader, responsibility, and verification are distinct.
5. Route the active rule exactly once before using it.
6. Read only the rules matched by the current task, apply them, and verify the scoped result.
7. Keep unverified or single-task observations as candidates until the promotion gate is met.

## Rule creation

- A rule file must state `Purpose`, `Read when`, and `Authority`.
- An operational rule must separate `condition`, `action`, `exception`, and `verification`; a document that only records history or examples is not an active rule.
- One rule owner must have one coherent trigger and responsibility. Do not combine extraction with deletion, policy with procedure, or a reusable invariant with task-specific evidence.
- Before creating a file, search for an existing owner and explain why updating it would mix responsibilities or leave a distinct trigger without an owner.
- Rule IDs, replay IDs, and local anchors must have one owner and must not be duplicated across active rule files.
- Evidence from one video, one user preference, one frame range, one filename, or one report may create a candidate, but does not become a general active rule without the applicable promotion evidence.

## Rule routing

- `PROJECT_RULES.md` is the single router for always-on policy, task class, current-state selection, and core conditional rules.
- `extension/README.md` is the single router for active extension rules. A workflow contract may explain capability ownership, but it must not become a parallel extension rule index.
- Every active rule has exactly one route with an observable trigger, a working Markdown link, and the correct owner. Do not route a report, candidate, cache, or historical document as an active rule.
- When a rule is renamed, split, merged, or retired, update its router, inbound links, tests, and applicable owner in the same logical checkpoint.
- If multiple rules match, read all of them once in the order selected by the current task; resolve conflicts by latest user instruction, higher policy, then the exact active owner.

## Rule reading

- Read the startup policy and selected current-state document first, then the exact active owner and only the rules whose route matches the current action.
- Read each matched maintained rule to EOF with explicit UTF-8 decoding once per logical task. Do not preload every rule or treat a report, candidate, or previous session as a rule.
- A rule reference is a routing hint, not permission to broaden into unrelated rules or protected data. Follow only the additional owner required by the current trigger.
- If the user changes or corrects the task, stop queued mutations, discard the old rule selection, and recalculate the route before continuing.
- Record the rule owner and applied verification at the logical checkpoint; do not copy the whole rule body into a report or task state.

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
