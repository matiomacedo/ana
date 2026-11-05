# Verification

After every successful file-mutating tool call, Ana runs a **deterministic
verification pass** — replacing what would otherwise be an extra LLM
"critic" call — and feeds any failure straight back into the tool
observation so the model can self-correct in the same turn.

## Levels

The depth is controlled by `ANA_VERIFY_LEVEL` (or the `verify_level`
backend setting):

| Level | Runs |
|---|---|
| `off` | Nothing |
| `syntax` | Syntax check on the changed file |
| `lint` | + `ruff check` on changed files (if the project has a ruff config) |
| `test` *(default)* | + the impacted tests (see below) |

```bash
# Session-wide, in .env:
ANA_VERIFY_LEVEL=lint

# Or live from chat:
/settings verify_level lint
```

## How the feedback loop works

1. The model changes a file with `write_file`, `edit_file`, `multi_edit`,
   `edit_symbol`, `rename_file`, `delete_file`, `lsp_rename`, or `undo`.
2. Verification runs immediately, before the model's next reasoning step. A
   deleted or renamed-away file has nothing to parse, so it only gets the tests
   of what imported it. `lsp_rename` and `undo` report the files they touched,
   and up to 5 of them are checked.
3. On failure, the error output is appended to the tool result —
   the model sees exactly what broke and fixes it in its next action.
4. To avoid nagging the model into a retry loop, verification tells it to stop
   and report after **3 consecutive failures** on a file in one user turn.

Edits made through `shell_command` aren't tracked, so they trigger none of this.

## Which tests run

An edit runs the test named after the file (`test_calc.py` for `calc.py`) plus
the tests that import it, directly or through other modules, found through the
code graph. Nearest tests come first, and one edit runs at most 3 test files. A
graph that hasn't been built yet only costs the importers: the edit doesn't wait
for it.

pytest runs through the project's `.venv` or `venv` interpreter when that
environment has pytest, and from `PATH` otherwise. A test run only counts as
passing until the next verified edit, because that edit may be what breaks it.

A check that times out counts as a failure, since a hang is often what the edit
caused. A check whose binary is missing is skipped.

Checks run with their temp files, home directory, and caches outside the project,
so they don't add anything to `git status`.

## Failures that were already there

Before the first edit in a turn that would trigger a test file, Ana records how it
behaves now: which tests fail for pytest, the exit code for other runners. This
runs once per test file per turn, and not for an edit you reject.

A later failure the record already has is reported to the model as already failing,
with the same output. It doesn't count towards the 3-failure limit or
auto-escalation, because the edit didn't cause it.

## The finish check

When the model gives a final answer in a turn that edited files, Ana re-runs the
impacted tests of those files, up to 6 test files, before ending the turn.

| What it finds | What happens |
|---|---|
| Everything passes | The turn ends |
| Failures new since the turn's edits | The model is sent back to fix them, up to **2** times |
| Failures that were already there | The model is sent back **once**, to fix them if the task needs it and otherwise say so |

A task can literally be "make these tests pass", which is why failures that were
already there still get one pushback.

After that the turn ends, with a last line naming what still fails. There's no
pushback once the 3-failure limit has told the model to stop and report.

The finish check doesn't run for a turn with no edits, an interrupted turn, a model
error, or a turn stopped by the iteration limit or a repeating tool call. It only
runs at the `test` level.

## Auto-escalation

With `ANA_AUTO_ESCALATE=on` (the default), the session moves to a larger installed
model (the [escalation role](../configuration/models.md#model-roles)) for the rest of
the turn when verification failures stop shrinking. A cross-file edit normally fails
while it's half done, so a test run with fewer failures than the last one counts as
progress and doesn't lead to escalation. Two failing checks without progress do.

Runners that only report an exit code count as one failure, so two failures in a row
escalate. Syntax and lint failures don't count as progress.

The turn stays on that model even after an edit passes, because switching
back would reload the model and lose its cache.

Ana only escalates to a model that fits in memory, going by its preset's
`ram_required_gb`, or an estimate from its parameter count, against 90% of your GPU
memory or RAM. If nothing bigger fits, or the size is unknown, it stays on the
current model. This also applies to a model you set as `ANA_ESCALATION_MODEL`.

## Best-of-N edits

For hard edits, `ANA_BEST_OF_N` (default `1`, disabled) samples N candidate
edits and keeps the one whose result parses. Higher N trades latency for
reliability on models that struggle with exact-match edits.

## Related

- [Tools](tools.md#file-tools) — the file tools
- [Settings](../configuration/settings.md#agent-behaviour) — the env vars
- [Models & presets](../configuration/models.md#model-roles) — the
  escalation model role
