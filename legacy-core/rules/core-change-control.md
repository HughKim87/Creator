# Core Change Control

- Purpose: keep `core/` immutable by default and define the only approved core-change path.
- Read when: any requested action could create, edit, delete, move, rename, regenerate, or indirectly change `core/**`.
- Authority: `PROJECT_RULES.md` is higher authority; the user approves each exact core-change scope.

## Decision

1. Resolve the exact affected `core/**` paths with read-only checks.
2. Explain why extension-only work cannot satisfy the objective.
3. Check for explicit user approval in the current conversation covering those paths and that reason.
4. If approval is absent:
   - interactive work stops and asks the user;
   - automatic or unattended work does not ask or wait, leaves `core/` untouched, records the failure below, returns non-success, and stops that objective.
5. If approval exists, change only the approved minimum scope and preserve unrelated changes.

## Automatic failure record

Append one compact entry to `extension/work/CORE_CHANGE_FAILURES.md` with:

- a unique UTC-based ID;
- task or automation identity;
- exact requested core paths;
- why the core change appeared necessary;
- confirmation that no core change was made;
- result `failed`;
- restart condition `explicit_user_approval`.

Do not include secrets, protected-data contents, raw logs, or speculative fixes. The failure log is the single owner; other work state may link to its entry instead of copying it.

Use stable error code `core_change_required` and a non-success process or task result.

## Approved verification gate

An approved core change must pass:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONUTF8 = '1'
$env:PYTHONPATH = ((Resolve-Path 'core/src').Path, (Resolve-Path 'extension/src').Path, (Resolve-Path 'core/tests').Path -join ';')
python -m unittest discover -s core/tests -q
python -m unittest discover -s extension/tests -q
python -m file_data --root . maintenance-verify --allow-core-changes
```

`--allow-core-changes` is evidence that the operator already confirmed exact user approval. Automatic or unattended work must never use it.
