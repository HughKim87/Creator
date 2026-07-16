# Design Principles — Supreme Improvement Criteria

- Role: the five governing principles behind this project's structure. Every
  improvement, refactor, new rule, new document, and new tool is judged
  against them.
- Read when: proposing, planning, or reviewing any framework change.
- Retention: permanent while this framework exists. Amend only with explicit
  user approval; these principles outrank all other local documents.
- Confirmed by the user as the top principle set on 2026-07-16.

## P1. The framework is the product

Videos are consumables; the pipeline is the asset. The repository contains
only reusable rules, gates, tools, and tests. Per-video facts, inputs, and
outputs stay outside version control. An improvement that helps one video but
does not survive to the next video is not a framework improvement.

Test: "Does this change make the next ten videos better, or only this one?"

## P2. Trust agents with work, never with quality

Agents are diligent but unreliable workers. Quality comes from deterministic
external checks, not from agent self-reports. Tool success is not content
approval. Every repeated failure becomes a structural fix at the narrowest
effective level, preferring stronger enforcement:

```text
prompt wording < document rule < contract field < tool check < test < hook/CI
```

Test: "If the agent lies or forgets, what still catches the mistake?"

## P3. Agents are interchangeable parts

No dependency on one AI vendor or model. Rules, memory, and judgment live in
the repository; any agent (Claude, Codex, Gemini, or future ones) must produce
the same quality under the same gates. Platform-specific files stay thin
pointers to the shared kernel.

Test: "If this agent is replaced tomorrow, does the workflow lose anything?"

## P4. Context is a budget

Long sessions degrade agent rule-following. Startup load stays minimal, the
router selects documents per task, full rules load only when triggered, and
document sizes have enforced targets. New text must pay for itself in reduced
repeated work or prevented failure.

Test: "Does this addition earn its tokens on every session that loads it?"

## P5. Creative authority stays with the user

AI proposes candidates with evidence traceable to original footage and spoken
lines; the user decides message, tone, editing feel, and upload. A message
that cannot be traced to original lines is discarded, not defended.

Test: "Did the AI decide something only the user may decide?"

## Applying These Principles

- Every improvement proposal names the principle(s) it serves.
- A change that strengthens one principle must not silently weaken another;
  conflicts go to the user.
- The standing direction of travel is P2: move prose rules rightward along
  the enforcement scale toward tool checks, tests, and hooks/CI.
