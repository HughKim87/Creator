# AI Agent Document Maintenance

- Role: checklist for document structure changes.
- Principle: reduce rules rather than grow them. Stop only dangerous actions;
  proceed autonomously on reversible work.

## Target Sizes

| File | Target |
|---|---:|
| `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` | ≤ 12 lines each |
| `PROJECT_BOOTSTRAP.md` | ≤ 60 lines |
| `docs/INDEX.md` | ≤ 60 lines |
| `PROJECT_RULES.md` | ≤ 160 lines |
| `SESSION_HANDOFF.md` | ≤ 20 lines |
| `outputs/SESSION_HANDOFF.md` | ≤ 120 lines |

## Maintenance Rules

- Startup load is `PROJECT_BOOTSTRAP.md` and `docs/INDEX.md` only.
- Load `PROJECT_RULES.md` per "Load Full Rules When" in `PROJECT_BOOTSTRAP.md`.
- Keep long research and design rationale out of operating rule documents.
- If the same rule repeats in two or more documents, keep one.
- Inspect roles, sizes, broken references, and risky behavior over wording.

## Authoring Rules

- A new document states its role, when to read it, and retention criteria
  within the first 10 lines.
- The body contains only decisions, procedures, and data unique to that
  document.
- User material belongs only in `inputs/`. Every input-derived file, including
  task state, helper code, and tests, belongs only in `outputs/`.
- Root controllers and framework folders contain only cross-video material.
- Do not pin channel, person, client, or per-source proper nouns in framework
  documents.
- Keep workflow domain names, platform names, tool names, and skill names when
  needed.
- Link shared rules to their source document; do not copy them.
- Keep only sources and judgments from research; do not mix them into
  operating rules.
- Do not keep past states, commit SHAs, or transient work status.
- Skill documents use `skills/SKILL_CONTRACT.md` as the shared contract and
  record only per-stage differences.
- Language policy: see Output in `PROJECT_RULES.md`.

## Work Order

1. Modify one file at a time.
2. Verify each file for NUL bytes and expected content.
3. Check related references with `rg`.
4. Run `tools\run_doccheck.bat` and `git diff --check`.
5. Report what was verified and what was not.

## Deletion Criteria

- Delete one-shot proposals or execution plans after they are applied.
- Do not pin past states, commit SHAs, or worktree status in documents.
- Delete or move only with the user's explicit intent or an approved plan.
