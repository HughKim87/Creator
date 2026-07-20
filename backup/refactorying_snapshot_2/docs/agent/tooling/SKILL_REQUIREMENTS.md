---
doc_id: doc.skill_requirements
kind: requirements
domain: tooling
lifecycle: active
authority: normative for pre-L8 workflow skill contracts and responsibilities
audience: agent
language: en
validation: structure_validated
purpose: Define the minimum shared contract and stage-specific responsibilities needed to reconstruct workflow skills in L8.
scope: Skill selection, note shape, inputs, outputs, gates, stops, user authority, source evidence, and next-stage handoff; this note does not activate a skill.
read_when: Selecting, creating, changing, or validating an L8 workflow skill.
write_when: A confirmed-use skill, shared skill contract, or stage responsibility changes.
---
# Workflow Skill Requirements

## Activation boundary

- Reconstruct only skills confirmed by actual user workflow or required by an approved representative stage.
- A row in the inventory is a responsibility specification, not proof that an active skill exists.
- L8 must create the selected skill in the active project, validate one representative execution, register it,
  and update the reconstruction map before calling it implemented.
- Skill documents are agent execution inputs and are written in English. User-facing results remain Korean.

## Required sections for every active skill

1. Purpose and scope
2. Required inputs and missing-input behavior
3. Outputs and authoritative fields
4. Pass/fail gates
5. Stop conditions
6. Handoff to the next stage
7. Decisions the AI must not finalize
8. Short realistic request examples

Shared global policy is linked to `PROJECT_RULES.md`; file state is linked to
`docs/agent/state/STATE_OPERATIONS.md`; stage order is linked to the future L5 workflow rule. A skill contains only
its unique judgments and operations.

## Authoring rules

- Inputs name exact prerequisite files, state eligibility, source identity, and behavior when absent.
- Outputs name exact files, tables, fields, validation level, approval purpose, and next-use status.
- Gates contain only conditions that can pass or fail.
- Stop conditions cover cases where continuing risks loss, distortion, overwrite, false evidence, or an
  unauthorized creative decision.
- Handoff contains only what the next stage reads unchanged.
- User decisions are explicit and narrow. The AI proposes one reviewed recommendation when possible.
- Tool details remain in the tool contract or command help rather than being duplicated in the skill.
- Long research, chat history, transient progress, and Git state do not belong in a skill.

## Source-derived output contract

- Carry the stable source ID and exact fingerprint from stage 4 through stage 8.
- A source-derived result records original source ranges and reused evidence IDs when those fields are consumed.
- A revision records its baseline and affected ranges without duplicating unchanged source evidence.
- Source evidence and version-specific render evidence remain distinct.
- A retained media result must be registered by the active output/state contract before next-stage use.
- Rerunning unchanged inputs reuses the result. Changed input or judgment creates a new version and preserves
  the prior record.

## Stage responsibility inventory

| Stage | Skill responsibility | Required retained judgment | Activation |
|---:|---|---|---|
| 1 | Game and topic research | Demand, freshness, evidence quality, channel fit, and exclusions | L8 if used |
| 2 | Channel planning | Concept, viewer reason, central claim, title and thumbnail direction | L8 if used |
| 3 | Script planning | Claim flow, evidence connection, scene purpose, and tone boundary | L8 if used |
| 4 | Subtitle cleanup | Preserve original meaning, produce cleaned text, disclose timing confidence, and carry source ID | L8 if used |
| 5 | Evidence-based video planning | Audience promise, one central message, evidence spine, counterevidence, character change, and calibration brief | L8 if used |
| 6 | Gameplay evidence analysis | Event, image, audio, audience-interest, counterevidence, and source-coordinate map before planning | L8 if used |
| 7 | Editing export and calibration | Interpret ranges, design microbeats, validate boundaries, build representative samples, then expand approved grammar | L8 if used |
| 8 | Final video review | Intent, continuity, audio, subtitle, source protection, application playback, and release decision support | L8 if used |
| Support | Video observation | Exact-frame, motion, transcript, and source-evidence assistance without inventing meaning | L8 if repeatedly used |

External research, calendar, and YouTube metadata automations are not core production-stage skills. Add them
only through their own approved task and active contract.

## User authority by stage

| Decision | User authority |
|---|---|
| Topic | Select the final topic from researched candidates |
| Concept and claim | Choose the channel viewpoint, message, and tone |
| Subtitle meaning | Approve any correction that could change meaning |
| Audience hypothesis | Confirm the intended viewer and material exclusions |
| Editing direction | Judge one AI-validated representative sample before full expansion |
| Release | Decide whether the final result is uploaded or published |

The user is not the first-line detector for basic chronology, missing evidence, broken boundaries, invalid
interchange, or untested playback. Those checks belong to the agent and deterministic tools before review.

## Representative L8 completion

A selected skill is complete only when:

1. its active file and every linked authority exist outside the migration archive;
2. required and missing inputs produce predictable behavior;
3. output state and files pass their declared validation;
4. stop conditions prevent false promotion or unauthorized decisions;
5. the next stage can resume from the documented handoff; and
6. one synthetic or user-designated representative execution passes.
