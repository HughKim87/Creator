# Document-Based Data Work Rules

- Purpose: govern maintained documents and persistent project data without turning documentation into the work product.
- Read when: creating or changing a maintained design, plan, report, Markdown document, root control, record, event, snapshot, or index.
- Authority: task-specific; `PROJECT_RULES.md` remains higher authority.

## General rules

- Before writing, define the exact artifact budget: owner, path, purpose, reader, and number of files.
- Before the first mutation in controlled work, read each controlling document to EOF and record its applicable clause and any conflict with the latest user instruction in the active plan.
- A request for only a report authorizes only that report. Analysis does not authorize implementation, rule or skill changes, sidecar proposals, or additional persistent artifacts.
- Before writing, identify the canonical owner. Update it instead of creating a file unless a distinct durable purpose or reader requires one.
- Keep one plan·execution·report owner per initiative unless the user requests a separate artifact.
- If a user correction invalidates the current interpretation, stop queued mutations, mark that plan invalid, and update the active plan and success gate before resuming.
- Update only the state document selected by `PROJECT_RULES.md` when current work, a material blocker, verified state, or the first next action changes. Before ending unfinished work, record the current stage, blocker, and first next action there; remove completed detail from the startup path.
- For a maintained machine artifact, identify its document owner, rebuild command, and verification. Do not write it if that relationship is missing.
- Link to policy, procedure, and current state instead of copying them. User-facing guides and approval summaries use Korean; concise agent-only routing may use English.
- Plans and reports retain decisions, authorized scope, success gates, unresolved risks, and the next executable action. Execution checkpoints keep only the goal, prohibitions, owner, and current stage; do not copy conversation text, file-by-file implementation detail, or completed history that Git already preserves.
- Before completion, compress text that does not change a future action, resumability, verification, or audit decision.
- Validate a logical batch at its completion checkpoint: strict UTF-8, NUL 0, relevant structure and links, trailing whitespace, and the scoped diff.
- Run full maintenance only for controlled structural work or when the active plan requires it; otherwise use the smallest direct document checks that cover the change.
- Generated or structure-valid does not mean user-approved.
- For a report carrying a decision or material risk, identify material unverified claims and plausible failure or abuse cases before completion, then record the mitigation or decision. Do not add red-team boilerplate to routine reports.
- A successful write call is not proof of correct content: reread the maintained file and check strict UTF-8, NUL 0, expected content or structure, and a hash when the artifact contract requires it. Keep a corrupt file out of the success state and use the approved version-control recovery path; never silently overwrite the last good version.

## Task-rule document lifecycle

- Condition: standard or controlled work will create intermediate files, span a checkpoint, or may discover reusable operating rules. Without waiting for a separate user request, use exactly one task-rule owner; prefer a `Task rules` section in the active task or phase owner and create `TASK_RULES.md` only when a checkpoint requires a separate owner. Quick work creates none.
- A task-rule is task-local authority below the user and routed rules, never an active project rule or parallel router. Link inherited rules and keep only task identity·outcome, baseline, one scratch root, maintained/final artifacts, and `trigger / extracted rule / evidence / target owner / disposition` rows.

| State | Required action |
|---|---|
| `created` | Fix owner, baseline, scratch root, final artifacts, and inherited links before generating intermediates. |
| `active` | Immediately capture reusable user corrections, verified failures, successful procedures, and workflow gaps; omit logs, routine output, and speculation. |
| `frozen` | Stop adding behavior after execution and confirm discovered reusable knowledge is represented. |
| `absorbed` | Give every row a rule-governance disposition and complete each authorized merge or rejection. |
| `retired` | After absorption and scratch cleanup, remove the section or file and active links in the same checkpoint. |

- Put every non-final derivative under the declared scratch root and move reusable knowledge into the task-rule when discovered. Ignored scratch is not a knowledge owner.
- Keep a section within its owner's read budget. A separate `TASK_RULES.md` ends at 120 lines or 8,000 Unicode characters; freeze and disposition it instead of opening a second buffer.
- Interrupted work keeps one `active` task-rule linked from current state and preserves scratch; invalidated or cancelled work freezes and dispositions it before retirement.
- Verification: at most one task-rule owner is active, scratch and final artifacts are distinct, every row has one disposition, and completed work has no active task-rule link, separate file, or scratch residue.

## Design document rules

- Condition: these rules apply when a maintained document will authorize, guide, resume, or verify future execution.
- Before writing, classify the artifact as exactly one of `overall-design`, `phase-design`, or `reference-evidence`.
- An active design must state its outcome, reader, authority, included and excluded scope, approvals, success gates, stop or recovery conditions, and next executable action.
- An `overall-design` owns stable intent, invariants, stage order, dependencies, and one-line stage outcomes. It must not own current progress, command logs, file-by-file implementation, or detailed future-stage procedures.
- A `phase-design` owns only one stage's exact decisions, scope, execution slices, verification, success gate, recovery, and transition condition. It must not restate the whole roadmap or another stage's implementation.
- A `reference-evidence` may preserve long analysis, alternatives, and success or failure evidence. It must not be a startup-required read, active authority, current-state owner, or next-action owner.
- Every required-read `overall-design` must fit within both 120 lines and 8,000 Unicode characters. Every required-read `phase-design` must fit within both 160 lines and 12,000 Unicode characters.
- If an active design exceeds its read budget, do not route a summary followed by an unread long body. Remove copied policy, state, history, raw evidence, and future-stage detail; then split the work into smaller stages or move optional evidence to an exact reference.
- A user-requested long analysis is a `reference-evidence`, not an exception to the active-design read budget.
- Link to the current-state owner and optional evidence instead of copying them. Completed execution detail remains in Git; only durable decisions that change later action stay in the design owner.

## Design verification

- Count lines and decoded Unicode characters for every required-read design before routing it.
- Confirm that a new session can read the selected current-state document, the overall design, and the active phase design in full and identify the outcome, current stage, first action, prohibitions, and success gate without opening reference evidence.
- Confirm that no active design claims policy authority, current execution state, or completed history owned elsewhere.
- Treat a read-budget excess, missing success gate, duplicate owner, or required long-reference read as a design failure; revise the document before execution.
