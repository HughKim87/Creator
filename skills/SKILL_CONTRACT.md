# Shared Skill Document Contract

- Role: shared authoring standards not repeated in each `skills/*/SKILL.md`.
- Read when: creating or fixing a skill, or routing skill work.
- Retention: keep while it reduces repeated items across skill documents.
- Skill stage documents themselves are written in Korean (see Output in
  `PROJECT_RULES.md`); their required section names stay in Korean below.

## Principles

- A skill file contains only that stage's unique inputs, judgments, and
  outputs.
- Link shared safety rules to `PROJECT_RULES.md`; do not copy them.
- Defer tool usage to `tools/README.md` or the script's own help.
- Do not put long research text, past progress, or commit SHAs in skill
  documents.

## Required Sections

Each skill must have the sections below. Names may be adapted per stage.

1. 입력 (inputs)
2. 출력 (outputs)
3. 게이트 (gates)
4. 중단 조건 (stop conditions)
5. 다음 단계 전달물 (handoff to next stage)
6. AI가 확정하지 말 것 (what AI must not finalize)
7. 좋은 요청 예시 (good request examples)

## Authoring Standards

- 입력: required files, prerequisite stages, and default behavior when missing.
- 출력: files, tables, fields, and approval states the next stage uses as-is.
- 게이트: only conditions that can decide pass or fail.
- 중단 조건: only cases where continuing causes loss, distortion, overwrite,
  or wrong finalization.
- 다음 단계 전달물: the minimum information and paths the next skill reads.
- AI가 확정하지 말 것: only choices the user must decide.
- 좋은 요청 예시: only short sentences a user would actually say.

## Cleanup Standards

- If the same sentence repeats in two or more skills, hoist it into this file.
- If one skill grows too long, split tool procedures, examples, and background
  into separate files.
- Do not use deleted legacy skills or applied reinforcement plans as reference.
