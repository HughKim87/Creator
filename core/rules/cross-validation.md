# Cross-Validation Work Rules

- Purpose: compare reports or agent conclusions without overstating independence, identity, evidence, or current state.
- Read when: cross-validating reports, comparing multiple agents' analyses, or consolidating their conclusions.
- Authority: task-specific; `PROJECT_RULES.md` remains higher authority.

## Evidence labels

Classify material claims by how they were checked:

- `direct remeasurement`: the current reviewer reproduced the result from primary evidence;
- `independent reproduction`: a separate method reached the result without relying on the same source report;
- `shared-source agreement`: analyses agree but use the same underlying evidence;
- `reported / unverified`: present in a source report but not reproduced.

Shared-source agreement and duplicated report text are not independent corroboration. When the user asks to retain duplicates, keep them without increasing the evidence count.

## Rules

- Identify the current reviewer from the current session. Do not inherit an agent name, role, or runtime identity from a source report.
- Keep source author, current reviewer, evidence source, and verification method separate.
- Prefer primary files, tests, and direct measurements over another report's conclusion.
- Mark contradictions and unverified claims explicitly; do not turn absence of contrary evidence into confirmation.
- For dynamic repository state, record the checked-at time, branch or revision, and relevant counts or paths.
- For current, official, version-sensitive, pricing, API, security, permission, or availability claims, prefer official or primary sources, cross-check the material claim, and label weak or secondary evidence. If the claim remains unresolved, report it as unverified.
- Do not access protected data merely to raise confidence. Exact user authorization remains required for each protected item and purpose.
- Respect the requested artifact budget. A report-only request does not authorize rule changes, implementation, sidecar files, or extra proposals.
- Consolidation should retain decisions, evidence strength, disagreements, and unresolved risks rather than reproducing source narratives.

## Verification

- Trace each material conclusion to its evidence label and safe source.
- Recheck identity, date, revision, and dynamic counts immediately before finalizing.
- Verify that duplicate evidence was not counted as independent and protected paths were not broadened.
