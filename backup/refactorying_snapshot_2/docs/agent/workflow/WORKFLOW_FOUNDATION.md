---
doc_id: doc.workflow_foundation
kind: requirements
domain: workflow
lifecycle: active
authority: normative for pre-L5 workflow knowledge
audience: agent
language: en
validation: structure_validated
purpose: Preserve production routes, stage responsibilities, planning requirements, gates, and user decisions needed to design the active workflow.
scope: Durable workflow knowledge for L5-L8; this note does not authorize stage execution or replace the future concise workflow rule.
read_when: Designing or reviewing L5 workflow rules, L6 structure, L7 stage operations, or L8 skill behavior.
write_when: The user changes a durable production route, stage responsibility, planning requirement, or creative decision point.
---
# Workflow Foundation Requirements

## Status boundary

These requirements are reconstructed and active as design input. L5 remains unstarted until the user approves
it. No task may treat this document alone as permission to create stage outputs or advance task state.

## Production routes

- Pre-shoot route: `1 -> 2 -> 3 -> record -> 4 -> 6 -> 5 -> 7 -> 8`.
- Recorded-footage route: source intake -> subtitle cleanup or confidence check -> `6 -> 5 -> 7 -> 8`.
- Recorded footage always uses analysis before planning. A `5 -> 6` route is invalid.
- Missing or low-confidence subtitles require stage 4 before stage 6.
- A generated file does not advance a stage. The stage's evidence and gate must pass.

## Stage responsibilities

| Stage | Purpose | Required input | Durable output | Completion focus | User decision |
|---:|---|---|---|---|---|
| 1 | Topic research | Current demand, community, game, channel, and search evidence | Ranked topic candidates with exclusions | Demand, freshness, and channel fit | Final topic |
| 2 | Channel planning | Selected topic | Concept, central claim, title and thumbnail direction | Channel viewpoint and click reason | Concept and message |
| 3 | Script structure | Approved concept | Argument flow, script structure, and scene purpose | Claims connect to evidence | Tone and claim |
| 4 | Subtitle cleanup | Source media and subtitle or transcript | Preserved original text, cleaned text, and timing confidence | Meaning preservation and disclosed timing confidence | Meaning-changing corrections |
| 5 | Video planning | Approved stage-6 evidence, transcript, and planning requirements | Audience promise, one central message, character change, evidence spine, and calibration brief | Every beat serves the message and traces to source evidence | Direction is judged on a verified sample, not text alone |
| 6 | Evidence analysis | Source media, transcript, and audience-interest hypothesis | Event, emotion, visual, audio, counterevidence, and audience-interest map | Claims trace to source time or frames and pass AI meaning review | Audience hypothesis requiring evidence |
| 7 | Editing materials | Approved analysis and self-reviewed plan | Representative sample, cut decisions, change record, interchange files, and use guide | Source binding, sequence structure, audio, regression scope, and real A/V evidence | One editing-direction decision on a verified sample |
| 8 | Final review | Completed render, plan, and editing records | Review checklist and revision list | Intent, flow, audio, subtitles, source protection, and full playback | Upload or release decision |

## Cross-stage invariants

- Preserve one stable `source_id` for one exact source fingerprint.
- Source-derived visual and audio evidence records original source time or frames. Edited-render evidence cannot
  prove original content.
- Reuse registered source evidence before extracting it again.
- Stage 6 finds and tests evidence; it does not create a cutlist, interchange file, rough cut, or final story.
- Stage 5 selects a message from approved evidence; it does not choose final cut boundaries.
- Limited calibration may begin only from a self-reviewed plan. Full editing requires a user-approved sample direction.
- Stage 7 uses the latest eligible analysis, plan, and cut decisions; technical import success is not creative approval.
- A validation failure in one scope does not erase independent evidence from another scope.
- Changed governing input or judgment creates a new version. Unchanged reruns reuse the current result.

## Planning requirements

### Required inputs

- Eligible stage-6 evidence with source ID, fingerprint, original-time references, and validation limits.
- Original subtitle or transcript with timing-confidence disclosure.
- A user-selected audience hypothesis and explicit exclusions.
- Counterevidence and unresolved items; unresolved items may not be promoted as facts.

### Required planning decisions

1. Write one audience promise that the source can actually deliver.
2. Compare two or three candidate central messages before selecting one.
3. For each candidate, record supporting source evidence, at least two weaknesses or counterexamples, audience fit,
   character-change coverage, and the selection result.
4. Select one central message that includes the start-to-end change, survives counterevidence, and can filter
   redundant scenes.
5. Build an evidence spine in source-event order. Each beat records evidence range, dialogue or image, story
   function, contribution, character change, loss if removed, and pre-edit validation.
6. Separate include, compress, exclude, and revalidate decisions. Explanation cannot substitute for absent footage.
7. Describe character change through event and changed perception, not emotion labels alone.
8. End with a calibration brief containing real A/V questions, not cut boundaries or interchange instructions.

### Planning self-review

Before calibration, the agent checks whether:

- audience interest is delivered by actual scenes rather than explanation;
- the central message has split into multiple unrelated claims;
- genre analysis has erased character behavior, humor, or release;
- counterevidence is hidden or a presenter's inference is treated as source fact;
- an unresolved shot is essential to the hook, conclusion, or world rule;
- a beat can be removed without losing information or change;
- a user would become the first detector of a basic defect.

### Planning completion

- The audience promise is evidence-backed and achievable.
- Exactly one central message connects every retained beat and remains valid with counterevidence.
- Character start, change, and end trace to source evidence.
- Every beat adds information and records the loss if removed.
- Unresolved items stay unresolved.
- Calibration scope authorizes only representative samples from different rhythms and positions. It does not
  authorize full editing or final release.

## Stage 7 internal boundary

| Substage | Responsibility | May produce | Must not do |
|---|---|---|---|
| 7A | Interpret candidate ranges and preservation intent | Story role and keep/compress/remove ranges | Final cut boundaries |
| 7B | Split microbeats and validate visual, subtitle, and audio boundaries | Cut decisions and boundary cautions | Full interchange output before boundary evidence |
| 7C | Calibrate different rhythms and positions | Representative sequence and editing grammar | Full expansion before AI and user direction checks |
| 7D | Expand the approved grammar | Full interchange files, validation material, and use guide | Claim final quality without application and playback evidence |

Candidate ranges are search areas, not actual cuts. Interchange generation is diagnostic until the required
quality gates pass. A new edit version revalidates affected boundaries; it does not invalidate unchanged
source analysis when the fingerprint and audience hypothesis remain unchanged.

## Stop conditions

- The source or current eligible baseline is ambiguous.
- Required evidence cannot be traced to source time or frames.
- A request would use an ineligible result as the next-stage baseline.
- The requested result could mean either analysis or generation and the distinction changes the work.
- The required Premiere interchange or import route is unknown.
- A technical result would be represented as creative, application, or user approval.

## L5 handoff

L5 must convert these requirements into one concise active workflow rule with stage inputs, outputs, one to
three completion criteria, and user decisions. It may simplify wording, but it may not omit the two production
routes, `6 -> 5` ordering, calibration boundary, source evidence, validation scopes, or user creative authority.
