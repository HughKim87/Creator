---
doc_id: doc.editing_quality
kind: requirements
domain: workflow
lifecycle: active
authority: normative for editing judgment, evidence, sampling, and promotion quality
audience: agent
language: en
validation: structure_validated
purpose: Define the retained editing-judgment, evidence, sampling, self-validation, and promotion requirements needed for consistent quality.
scope: Stage-7 editing quality and evidence only; global safety, task state, workflow order, and tool implementation remain in their own authorities.
read_when: Designing L5 editing gates, implementing L7 editing tools, executing or reviewing stage 7, or aligning an L8 editing skill.
write_when: Verified editing practice or a user decision changes a durable quality rule, warning threshold, evidence requirement, or promotion gate.
---
# Editing Quality Rules

## Quality definition

Consistent quality does not mean identical cut length or density. It means that beginning, middle, and end
received equivalent evidence review, microbeat reasoning, exception explanation, and validation.

## Judgment principles

1. A candidate range is not an actual cut. Split it into information, action, reaction, and state-change microbeats.
2. Preserving a sentence means preserving its meaning and order, not every pause and repetition around it.
3. Preserve connected speech when useful; visual coverage may change with J/L cuts. Remove an unnecessary
   utterance as a complete unit rather than breaking its meaning mid-sentence.
4. A long cut is valid when source action, connecting speech, emotional accumulation, or visible state change
   explains its length.
5. More cuts are not automatically better. Judge removed time against retained information and experience.
6. A beginning-only calibration cannot authorize full expansion. Sample beginning, middle, and end.
7. Automated audits surface deviations and missing explanations; they do not make editing decisions.
8. AI must detect chronology, visual causality, duplication, and boundary defects before user review.
9. Except for an explicit cold open, do not insert future source footage as earlier B-roll. Prefer already-seen
   material for retrospective cutaways.

## Rhythm modes and advisory thresholds

| Mode | Preserve | Compress | Review when |
|---|---|---|---|
| `compress` | New information, action, or required setup | Self-correction, repetition, low-information pause | Average exceeds 6 seconds or one cut exceeds 12 seconds |
| `radio` | Meaningfully connected speech and emotion change | Inter-sentence waiting, semantic repetition, movement without information | Average exceeds 10 seconds or one cut exceeds 18 seconds |
| `breath` | Event-to-reaction-to-result, suspense, visible change | Functionless movement around the event | Average exceeds 18 seconds or one cut exceeds 45 seconds |
| `hook` | Context, peak, and exit signal | Excess explanation and outcome spoilers | Average exceeds 15 seconds or one cut exceeds 30 seconds |

Thresholds trigger review, not automatic cutting. A calibrated exception records the image, sentence, event,
or emotional reason for the longer duration.

## Hook requirements

A hook contains:

1. enough context to understand the threat, question, or situation;
2. a peak in action, emotion, or curiosity; and
3. an exit signal such as completed reaction, intentional impact cut, or natural audio tail.

An immediate cut on the last dialogue frame is a review condition. A natural tail often begins around 0.5 to
1.5 seconds, but source audio and intent decide the actual duration.

## Required beat record

Before full interchange output, every beat records:

- story function and rhythm mode;
- source candidate range;
- microbeats to preserve;
- microbeats to compress or remove;
- actual cut count and selected duration;
- longest cut and its evidence-based justification;
- visual, subtitle, and audio boundary evidence; and
- differences from the approved calibration or user direction.

If one cut retains an entire candidate range, state why internal splitting adds no value.

## Representative sampling

| Position | Required review |
|---|---|
| Beginning | Setup compression and hook-to-body transition |
| Middle | Representative event rhythm and repetition removal |
| End | Fatigue-related looseness, conclusion preservation, and density drift |

The samples may have different rhythms. Each still needs microbeat records and a longest-cut justification.

## Evidence and validation scopes

| Scope | Passing evidence | Boundary |
|---|---|---|
| Audio signal | Source audio, silence/VAD, level or peak measures, and subtitle boundaries | Does not prove visual meaning or application playback |
| Editing meaning | Transcript, source time, frames or movement, microbeats, and causality | Must remain separate from continuous-playback claims |
| Continuous A/V | Evidence from uninterrupted image and audio playback | Does not prove application import behavior by itself |
| Application | Premiere import, sequence, playback, and render evidence | Required only for application claims |
| User direction | Preference, message, rhythm, and release decision | Never substitutes for basic technical or meaning validation |

Source-derived evidence remains tied to original source time and may be reused across edit versions.
Version-specific render evidence can prove compositing, subtitle, effect, sequence, or render behavior only.

## AI self-validation before user review

- Confirm that intended story ranges move through source time in the intended direction.
- Check overlays, J/L cuts, inserts, and cutaways for future spoilers or false causality.
- Compare representative frames with the function assigned to dialogue and action.
- Read hook reset, event-reaction-result, and evaluation-to-irony links in playback order.
- Without reading planning labels, restate the apparent message and character change from source evidence alone.
- Inspect source audio for mid-sentence cuts, abrupt breath cuts, silence, level, and subtitle-boundary risk.
- Run available structural checks for frames, links, sequence layout, and review-page structure.

If the intended message exists only in explanatory labels, the edit fails meaning validation. A single tool
failure marks only its scope failed unless no equivalent evidence path exists for a required scope.

## Promotion gates

| Gate | Pass condition | Failure response |
|---|---|---|
| Q0 Input | Eligible plan, evidence map, source, and subtitle are bound to one source identity | Return to interpretation |
| Q1 Calibration | Different rhythms plus beginning, middle, and end are represented | Add representative samples |
| Q2 Microbeat | Every beat has keep/compress/remove decisions and longest-cut evidence | Complete beat records |
| Q3 Advisory audit | Every warning is reviewed or has an evidence-based exception | Revisit the affected beat |
| Q4 Adversarial review | Abrupt hook exit, late uncut blocks, future spoilers, false causality, and repeated scenes are checked | Create a revised cut decision set |
| Q5 Structure | Interchange frames, links, sequence, text integrity, and review surface pass deterministic checks | Fix generator or input |
| Q6 Application and user | AI-validated representative sample receives user direction; final work receives full playback and application evidence | Do not claim application, full-edit, or release approval |

Q0 through Q4 must pass before a full interchange file becomes the eligible editing baseline. Generating a
diagnostic interchange file is allowed only when it remains explicitly ineligible.

## Advisory audit contract

An audit reads one content sequence, not a multi-sequence file that duplicates cuts. Its per-section profile
contains `section`, `mode`, `waive`, and `justification`.

| Code | Review condition |
|---|---|
| `AVG_LONG` | Section average exceeds its mode threshold |
| `MAX_LONG` | Longest cut exceeds its mode threshold |
| `SINGLE_BLOCK` | A compress or radio section over 8 seconds contains one cut |
| `LATE_DENSITY_CLIFF` | Late average cut length exceeds early average by 1.5 times |
| `MISSING_PROFILE` | A cut section has no profile |
| `MISSING_CUTS` | A profile section has no actual cuts |

An exception stays visible as `WAIVED`; it does not erase the warning. A waiver without justification is an
invalid profile. `REVIEW_REQUIRED` means redesign the beat or record a specific source-based exception.

## Review risks

- Adding unsupported exceptions only to clear a report defeats the gate.
- Matching density mechanically can destroy suspense, emotion, or action continuity.
- Using an over-cut beginning as the target for the ending propagates a bad baseline.
- Changed story function or cut boundaries require the affected profile and audit to run again.
