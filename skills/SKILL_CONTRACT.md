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

## Source-Derived Artifact Contract

- Carry the stable `source_id` from stage 4 through stage 8. Resolve it from the
  existing source fingerprint; do not invent a per-run alias.
- A source-derived output records `source_id`, `source_start`, `source_end`, and
  any reused `asset_ids`. A revision also records `baseline_version` and
  `changed_ranges`.
- Classify retained evidence as `reusable_source_evidence` or
  `version_specific_render_evidence`. Separately assign the promotion role from
  `docs/WORKFLOW_CONTRACT.json`: `draft`, `calibration_candidate`,
  `historical_failure_evidence`, `approved_baseline`, `current_deliverable`, or
  `superseded`.
- Query the shared source asset manifest before capture. Register every retained
  media file after creation; unregistered media is a failed gate.
- Source evidence is reusable across edit versions. Render evidence is tied to
  one edit version and cannot prove original content.

## Version Lifecycle

- Rerunning unchanged inputs reuses the existing output; it does not create a
  timestamped or numbered copy.
- Create a version only for changed governing input or decision. Record
  `status`, `supersedes`, and `current_pointer`, then update `CURRENT.json` only
  after the stage gates pass.
- Mark prior versions `superseded`. Report cleanup candidates, but do not delete
  or move them without clear user intent.

## Cleanup Standards

- If the same sentence repeats in two or more skills, hoist it into this file.
- If one skill grows too long, split tool procedures, examples, and background
  into separate files.
- Do not use deleted legacy skills or applied reinforcement plans as reference.
