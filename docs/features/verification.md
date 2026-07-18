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
| `test` *(default)* | + the impacted test file found by naming convention |

```bash
# Session-wide, in .env:
ANA_VERIFY_LEVEL=lint

# Or live from chat:
/settings verify_level lint
```

## How the feedback loop works

1. The model edits a file (`edit_file`, `write_file`, `apply_patch`, …).
2. Verification runs immediately, before the model's next reasoning step.
3. On failure, the error output is appended to the tool observation —
   the model sees exactly what broke and fixes it in its next action.
4. To avoid nagging the model into a retry loop, verification stops
   reporting failures for a given file after **3 consecutive failures** in
   a session.

## Auto-escalation

With `ANA_AUTO_ESCALATE=on` (the default), two consecutive verification
failures in one turn escalate the session to a larger installed model (the
[escalation role](../configuration/models.md#model-roles)) for the
remainder of the turn — a small-model-with-fallback pattern: fast local
models do the routine work, a stronger one steps in when edits keep
failing.

## Best-of-N edits

For hard edits, `ANA_BEST_OF_N` (default `1`, disabled) samples N candidate
edits and keeps the one whose result parses. Higher N trades latency for
reliability on models that struggle with exact-match edits.

## Related

- [Tools](tools.md#file-tools) — which tools trigger verification
- [Settings](../configuration/settings.md#agent-behaviour) — the env vars
- [Models & presets](../configuration/models.md#model-roles) — the
  escalation model role
