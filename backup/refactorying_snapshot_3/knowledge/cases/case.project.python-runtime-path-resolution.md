# Case: Python runtime command unavailable on PATH

- Case ID: `case.project.python-runtime-path-resolution`.
- Purpose: Preserve the confirmed cause, durable resolution, validation, and recurrence triggers for project Python commands that fail because a bare executable name is unavailable on `PATH`.
- Use when: A Python command cannot be launched, the runtime layout changes, or the launcher regression test fails.
- Owner: Project agents maintain evidence; the user approves policy changes.
- Language: English.
- Location: `knowledge/cases/case.project.python-runtime-path-resolution.md`. Prevention is owned by [validation rules](../../rules/validation.md#rulevalidationpython-runtime-resolution) and the [workflow](../../docs/agent/WORKFLOW.md#python-runtime-entrypoint); current state remains in [SESSION_HANDOFF.md](../../SESSION_HANDOFF.md).
- Authority and preservation: `maintained-current` resolved case evidence; it does not duplicate or replace the active rule or procedure.
- Status: `resolved`; retrieval eligible.
- Confirmed and resolved: `2026-07-21T09:48:38+09:00`.
- Last verified: `2026-07-21`.

## case.project.python-runtime-path-resolution

```json
{
  "schema_version": "1.0.0",
  "record_kind": "case",
  "case_id": "case.project.python-runtime-path-resolution",
  "title": "Python runtime command unavailable on PATH",
  "status": "resolved",
  "symptom": {
    "state": "confirmed",
    "summary": "A project command invoked the bare name python, and Windows PowerShell returned CommandNotFoundException even though the bundled workspace Python runtime existed.",
    "evidence": [
      {"source_id": "source.task.python-runtime-resilience-request", "locator": "context/requests/python_runtime_resilience.json#intent"},
      {"source_id": "source.repo.python-runtime-launcher-test", "locator": "tests/context/test_python_runtime_launcher.py::PythonRuntimeLauncherTests.test_explicit_runtime_works_with_empty_path"}
    ]
  },
  "resolution": {
    "state": "resolved",
    "summary": "All project Python commands use a CMD entrypoint backed by a validating PowerShell implementation, or an exact workspace-provided interpreter path; the launcher works with an empty PATH, forwards Python options such as -m, and rejects an invalid explicit runtime without fallback.",
    "evidence": [
      {"source_id": "source.repo.python-runtime-launcher", "locator": "tools/runtime/run_python.cmd"},
      {"source_id": "source.repo.python-runtime-resolver", "locator": "tools/runtime/run_python.ps1"},
      {"source_id": "source.repo.validation-rules", "locator": "rules/validation.md#rule.validation.python-runtime-resolution"},
      {"source_id": "source.repo.workflow", "locator": "docs/agent/WORKFLOW.md#python-runtime-entrypoint"}
    ]
  },
  "confidence": "high",
  "source_refs": [
    {"source_id": "source.task.python-runtime-resilience-request", "locator": "context/requests/python_runtime_resilience.json#intent"},
    {"source_id": "source.repo.python-runtime-launcher", "locator": "tools/runtime/run_python.cmd"},
    {"source_id": "source.repo.python-runtime-resolver", "locator": "tools/runtime/run_python.ps1"},
    {"source_id": "source.repo.python-runtime-launcher-test", "locator": "tests/context/test_python_runtime_launcher.py"},
    {"source_id": "source.repo.validation-rules", "locator": "rules/validation.md#rule.validation.python-runtime-resolution"},
    {"source_id": "source.repo.workflow", "locator": "docs/agent/WORKFLOW.md#python-runtime-entrypoint"}
  ],
  "relation_ids": [],
  "confirmed_at": "2026-07-21T09:48:38+09:00",
  "resolved_at": "2026-07-21T09:48:38+09:00",
  "last_verified_at": "2026-07-21",
  "review_policy": "event_driven",
  "review_due_at": null,
  "review_triggers": [
    "tools/runtime/run_python.cmd fails to locate a runtime in a supported workspace",
    "a maintained procedure or active command reintroduces reliance on a bare python executable",
    "tests/context/test_python_runtime_launcher.py fails or the bundled runtime layout changes"
  ],
  "retrieval_eligible": true,
  "task_tags": ["case", "python", "runtime", "path", "failure", "resolution"]
}
```

## Confirmed symptom and impact

- Fact: The first command used `python tools/context/context_system.py --help` and PowerShell returned `CommandNotFoundException`.
- Fact: The workspace dependency provider returned a working bundled Python executable, so the failure was command discovery, not absence of a Python runtime.
- Fact: Direct `.ps1` invocation was also rejected by local PowerShell execution policy during verification.
- Impact: Any future task that copied a bare `python` command or directly invoked the PowerShell implementation could stop before routing, validation, or tests began.

## Root cause

The project had Python entrypoints but no repository-owned runtime launcher or governing execution rule. The agent assumed that a conventional executable name was available on `PATH`. The first launcher revision exposed a second environmental assumption by requiring direct `.ps1` execution under a restrictive PowerShell policy. Its first argument-binding form also allowed `-m` to be interpreted as a PowerShell parameter instead of a Python option.

## Applied resolution

1. `tools/runtime/run_python.cmd` is the public entrypoint and invokes `run_python.ps1` through the absolute SystemRoot PowerShell path with `ExecutionPolicy Bypass`.
2. The internal PowerShell implementation captures unbound automatic arguments, validates them, and selects `PROJECT_PYTHON`, project `.venv`, bundled Codex runtime, or a system launcher in deterministic order.
3. An invalid explicit override stops with exit code 2 and a clear diagnostic; it cannot silently fall back to a different interpreter.
4. `WORKFLOW.md` defines the CMD launcher as the standard project entrypoint and forbids retrying a failed bare command or calling the `.ps1` directly.
5. `rule.validation.python-runtime-resolution` makes the behavior selectable for Python/runtime work.
6. The regression suite clears `PATH`, supplies only the exact interpreter through `PROJECT_PYTHON`, and verifies success, `-m` forwarding, and invalid-override failure through the CMD entrypoint.

## Verification

| Check | Expected and recorded result |
|---|---|
| CMD launcher with normal environment | `run_python.cmd --version` exits 0 |
| Empty `PATH` with exact runtime | Python child runs and reports `launcher-ok` |
| Python module option forwarding | `run_python.cmd -m site --user-site` exits 0 |
| Invalid exact runtime | Exit 2 with an explicit `PROJECT_PYTHON` diagnostic and no fallback |
| Same-stem catalog IDs | `.ps1` and `.cmd` retain distinct deterministic file IDs |
| Python compile and unit regression | All 29 project tests pass, including three launcher and three atomic-write regressions |
| Integrated project validation | `ok=true`, errors 0, orphan files 0 |

Validation is automated and structural. It is not represented as user approval of every implementation detail.

## Recurrence prevention

- Invoke project Python commands through `tools/runtime/run_python.cmd`.
- Use the workspace dependency provider's exact executable only to bootstrap or explicitly override the launcher; never persist a personal absolute path.
- Treat a launcher or regression failure as a review trigger for this case and the owning validation rule.
- Do not change the user's system PATH as a project fix.
