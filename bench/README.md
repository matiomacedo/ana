# Cross-file benchmark

A small benchmark for coding agents on **multi-file edits**: changes where an
edit in one file has to be reconciled with references in another. Both agents
under comparison drive the **same local model through the same server**, so what
is being measured is the agent scaffolding rather than the model.

Everything here is standard library only. There is nothing to install beyond the
agents you want to score and `pytest`.

## Layout

```
tasks/<name>/
  task.json    tier, prompt, success command
  fixture/     the project as the agent receives it (tests included)
  solution/    a reference fix, used to prove the task is solvable
  cheat/       the most plausible single-file shortcut, which must NOT pass
runner.py      runs the matrix and scores it
validate.py    gates the suite before any sweep
PREREGISTRATION.md   hypotheses, matrix and analysis, fixed before the study ran
```

## Tiers

| Tier | n | What it is |
|---|---|---|
| `xfile` | 12 | An edit that must be reconciled across files: a return shape changing under two unpacking call sites, a callback contract widening across a dispatcher and its handlers, a class moving module and its importers repointing, an exception type propagating through a handler that catches the old one. |
| `control` | 4 | The negative control. Same project shape and comparable patch size, but the change is confined to one function and nothing elsewhere references what changes, so cross-file breakage is impossible by construction. |
| `smoke` | 5 | Single-file plumbing checks. Not part of the study. |

The control tier is the point of the design. Without it, an agent that is simply
better at multi-file projects produces the same headline number as one whose
scaffolding actually fixes cross-file reconciliation.

## Running it

Validate first. A broken fixture is far cheaper to catch here than after it has
burned an hour of sweep time:

```bash
python bench/validate.py
```

It checks three directions per task: the untouched fixture must **fail**, the
fixture with `solution/` applied must **pass**, and for `xfile` the fixture with
`cheat/` applied must **fail**. That last check is not decoration: an audit found
four of the then-eight cross-file tasks satisfiable with a single-file edit,
because their tests asserted behaviour without asserting structure.

Then score:

```bash
python bench/runner.py --arm ana --model qwen3.5:4b
python bench/runner.py --arm ana --arm claude --model gpt-oss:20b --repeat 2
python bench/runner.py --arm ana --tier xfile --resume
```

Results append to `bench/results.jsonl`, one row per run; `bench/artifacts/`
keeps the workspace diff and the scoring output of each run, because the
interesting question about a failure is usually *why*, which pass/fail alone
cannot answer.

## What the harness enforces

- **Test restoration.** Fixture `test_*.py` files are copied back over the
  workspace before scoring, so no run can pass by editing the tests.
- **Environment scrubbing.** `CLAUDE*`, `ANTHROPIC*` and `ANA_*` are stripped
  from the child environment. Without this, a sweep launched from inside an
  agent session leaks session variables and the child runs in a nested mode
  where it narrates edits it never applies.
- **Symmetric working directory.** Every agent starts in the task workspace, so
  none of them sees a wider repository than the others.
- **Timeouts are failures.** A run that exceeds its cap fails even if the
  workspace it left behind would pass: the agent never declared itself done. The
  cap is set well above healthy runtimes so it does not quietly decide outcomes.
- **Arms are `(agent, variant)`.** A variant applies an environment overlay, so a
  config-only ablation needs no second binary and can never overwrite the
  baseline row it is measured against.

## Adding a task

Create the four parts above and run `validate.py`. Two rules matter more than
they look:

1. **The prompt names no file.** State the symptom or the expected behaviour and
   leave the tests as the specification. Locating *which* files must change is
   the problem being measured; a prompt that enumerates the call sites performs
   the reconciliation on the agent's behalf.
2. **Assert structure, not only behaviour.** Otherwise the single-file shortcut
   in `cheat/` passes and the task silently stops measuring its tier.
