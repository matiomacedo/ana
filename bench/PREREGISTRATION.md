# Preregistration — does deterministic verification help a local model edit across files?

Hypotheses, run matrix, scoring rule and analysis plan, all fixed **before** the sweep executed.
Anything learned afterwards is appended below, never edited in, with its timing relative to data
collection stated. The point is that a null result cannot be quietly reframed into a positive one
once the numbers land.

Date: 2026-07-26
Author: Mátio Macedo

## Question

Ana's claimed mechanism is a **deterministic post-edit verification loop**: after every mutating
tool call it re-runs impacted tests and performs a `git grep` cross-file stale-reference check,
appending failures to the observation. The prediction is narrow — the loop should help precisely
when an edit in one file leaves a *dangling reference* in another, and do nothing otherwise.

Testing that requires more than beating a baseline. An agent that is simply better at multi-file
work would produce the same headline number. So the design carries a **negative control** (tasks
matched on shape where a dangling cross-file reference is impossible by construction) and an
**ablation** (the same agent with the loop switched off).

## Hypotheses

| | Statement | Falsified if |
|---|---|---|
| **H1** | Ana solves more `xfile` tasks than Claude Code on the same model. | Difference ≤ 0 |
| **H2** | Ana and Claude Code are comparable on `control` tasks. | Ana's `control` difference matches its `xfile` difference |
| **H3** | The interaction (Ana−Claude on `xfile`) − (Ana−Claude on `control`) is positive. | Interaction ≤ 0 |
| **H4** | Ana with `ANA_VERIFY_LEVEL=off` loses most of its `xfile` advantage. | Ablation changes nothing |
| **H5** | The Ana−Claude gap is larger on `qwen3.5:4b` than on `gpt-oss:20b`. | Gap equal or larger on the stronger model |

**H2 and H4 are the falsifiers.** H3 is the headline: it is the only test separating "the
scaffolding fixes cross-file reconciliation" from "Ana is just a better agent on multi-file
projects". If H3 or H4 fails, the mechanism claim is not supported and the paper says so.

H5 is the "makes a weak model usable" claim and is tested only if both mornings run.

## Task suite

21 tasks, three tiers. `bench/validate.py` gates the sweep and checks **three** directions per
task: the untouched fixture must FAIL, the reference `solution/` must PASS, and — for `xfile` —
the `cheat/` shortcut must FAIL.

- **`xfile` (12)** — an edit in one file must be reconciled with references in another.
- **`control` (4)** — same multi-file shape and comparable patch size, but the required change is
  confined to one function and nothing elsewhere references what changes.
- **`smoke` (5)** — single-file. Not part of the study.

Two properties are enforced mechanically rather than assumed:

1. **Prompts name no file.** They state the symptom or the expected behaviour; the tests are the
   specification. Locating *which* files must change is part of the task, because that is the
   problem the verification loop exists to solve. A prompt that enumerates the call sites performs
   the reconciliation on the agent's behalf and leaves the mechanism nothing to do.
2. **Cross-file tasks cannot be solved single-file.** Each `xfile` task ships the most plausible
   one-file shortcut in `cheat/`, and the tests assert cross-file *structure*, not just behaviour.
   An audit found 4 of 8 earlier tasks were satisfiable by a single-file edit; the check now runs
   on every sweep.

### Tier matching

| | `xfile` (n=12) | `control` (n=4) |
|---|---|---|
| **Files the fix must touch (mean)** | **≥2** | **1** |
| Prompt words (mean) | 30.1 | 31.5 |

The bolded row is the manipulation. Prompt depth is matched, with control marginally longer — the
conservative direction, since H3 is a difference of differences.

## Run matrix

| Morning | Model | Arms | Reps | Runs |
|---|---|---|---|---|
| 1 | `gpt-oss:20b` | `ana`, `claude`, `ana:noverify` (xfile only) | 2 | 88 |
| 2 | `qwen3.5:4b` | same | 2 | 88 |

**176 runs.** Both agents drive the *same* local Ollama model in every cell; no cloud model is
used, and the harness verifies the baseline is genuinely reaching the local server.

One model per morning, both repetitions, in a **single invocation**, with:

- **arms interleaved per task**, so machine drift is shared evenly instead of landing on whichever
  arm ran last;
- **task order shuffled per repeat** (seed 20260726), so position is not confounded with identity;
- **repeats as the outer loop**, so an interrupted morning leaves a complete rep 1.

There is **no wall-clock budget** — the matrix completes. Runaway protection is a 1200 s per-task
cap (chosen so it does not bind on a healthy run: observed runs are 130–270 s) plus a
dead-backend circuit breaker that aborts after 3 consecutive runs that time out having made no
edit at all. `--resume` makes recovery from an abort cheap.

## Scoring

Success = the task's `success_command` (`pytest -x -q`) exits 0 after the fixture's `test_*.py`
files have been **restored over the workspace**, so no run can pass by editing the tests. A run
that exceeds its cap is scored a **failure** even if the workspace it left behind would pass: the
agent never declared itself done. Both agents are launched with `cwd` set to the task workspace,
so neither sees any wider repository.

## Analysis plan

Fixed in advance; implemented in `paper/stats.py`, stdlib only.

1. Pass rate per (arm, model, tier) with a **Wilson 95% interval**.
2. **Paired bootstrap over tasks** (10,000 resamples, seed 20260725) of the Ana−Claude pass-rate
   difference, per tier and per model.
3. **Exact McNemar** on per-task outcomes, `xfile`, pooled over models.
4. **H3 interaction**: (Ana−Claude on `xfile`) − (Ana−Claude on `control`), bootstrapped over
   tasks within tier.
5. **H4 ablation**: Ana `default` − Ana `noverify` on `xfile`, paired over tasks.
6. **Mechanism check**: failures classified from retained `pytest` output into *broken reference*
   (import/name/attribute/arity errors — an edit never reconciled) versus *wrong behaviour*
   (assertion failures), per arm and tier.
7. **Pass rate versus time budget**, so the speed difference is reported rather than allowed to
   decide the outcome through a cap.

Nothing else will be reported as confirmatory; anything else is exploratory and labelled so.

## Power, stated in advance

With 12 `xfile` tasks per model and 2 models, there are **24 paired comparisons**. A two-sided
exact McNemar cannot reach p < 0.05 unless at least **6 discordant pairs fall the same way**. At a
discordance rate of ~30% this design yields ~7, so significance is reachable but not assured. If
the observed discordance is much lower, the honest conclusion is that the study is underpowered —
not that the effect is absent.

## Known limitations, acknowledged in advance

- Two models, 16 study tasks, one laptop. Small.
- Tasks are synthetic and written by me. The `control` tier makes that bias testable, not absent.
- Fixtures are tiny (2–4 files). A repo map and a stale-reference check are infrastructure for
  codebases too large to hold in context; at this scale the mechanism may have little to do. This
  is the study's deepest limitation and no amount of repetition fixes it.
- Claude Code is driven through `ANTHROPIC_BASE_URL` redirection to Ollama, which is not a
  configuration it was designed for, and there is no second baseline.
- Runs are unseeded; local model sampling is stochastic and 2 repetitions bound that only loosely.
- The design and harness were shaped by a discarded pilot whose results are not reported and do
  not inform any hypothesis above.

---

## Correction to analysis item 6, made during collection

Applied while morning 1 was still running, before any contrast in the analysis plan had been
computed, and prompted by an operational observation rather than by any result.

Roughly one in five Ana-family runs exits early with `the turn ended with a non-recoverable
error`, in 30–95 s, having written nothing. The Ollama server log is clean across the same
window, so this is an Ana-side crash, not a backend fault.

Such a run leaves the fixture untouched, so `pytest` reports the *fixture's own* original failure
— frequently a `TypeError` or `AttributeError`. The classifier in analysis item 6 keyed purely on
exception type and would therefore have recorded an agent crash as a **broken cross-file
reference**: inflating precisely the quantity the mechanism analysis exists to measure, in the
direction that flatters the hypothesis.

The classifier now checks `made_edit` first and assigns a separate **no-edit** class to any run
that changed nothing; only runs that actually edited are classified by exception type. The
mechanism table reports `no-edit` as its own column.

This changes how failures are *categorised*. It changes no hypothesis, no pass/fail scoring, and
no contrast. Pass rates are unaffected — a crashed run was, and remains, a failure.

---

## Agent defect fixed, and the sweep restarted from scratch

Morning 1 was **stopped at 45/88 runs and its data discarded** (archived under `bench/discarded/`,
not analysed). Reason: ~17% of Ana-family runs were dying before the architecture was exercised,
for a cause unrelated to any hypothesis.

**Defect.** `gpt-oss:20b` is configured `tool_strategy: native`, and periodically emits raw Python
source where Ollama's native tool-call parser expects a JSON arguments object. Ollama raises
`error parsing tool call ... invalid character 'i' looking for beginning of value`. Because this
arrives as an *exception* rather than as unusable *content*, it bypassed the `ParseError` retry
machinery and landed in the fatal branch. The only recovery there was a one-shot failover to the
background-role model, guarded by `fallback != model_name` — and the background role resolves to
the session model by design, so that guard is false whenever no distinct background model is
configured. The sole recovery path was therefore dead code, and any such error killed the turn.

**Fix.** On a parse-shaped exception the same model is retried once with native tool-calling
dropped and constrained decoding enabled — the path the repair logic already uses. Genuine backend
failures (connection refused, model not found, deadline exceeded) remain fatal, unchanged.
Regression tests in `packages/core/tests/agent/test_tool_parse_retry.py` cover all four cases,
including that the retry branch reconfigures the model correctly and that a persistently
malformed model still terminates.

**Why a full restart rather than resuming.** The agent under test changed, so runs from before and
after the fix measure different systems and cannot be pooled. No hypothesis, task, scoring rule or
analysis step was altered. The discarded runs are not reported as a result; the crash rate that
prompted the fix is reported as a defect found during piloting.

---

## Morning 2 scope reduced to one repetition

`qwen3.5:4b` is a *thinking* model: it emits ~1,600 reasoning tokens even for a trivial prompt.
On the benchmark's multi-file tasks this makes runs far slower than on `gpt-oss:20b` — Claude Code
averaged ~999 s per run against Ana's ~243 s — putting two repetitions at 8–11 h. Rep 1 (44 runs,
all 16 study tasks) is run instead; rep 2 can be appended later via `--first-rep 2 --resume`
without repeating work. Consequence: **`qwen3.5:4b` cells are single-run**, so H5 is tested with
less precision than `gpt-oss:20b`, where both repetitions completed.

### A baseline-validity check, and why it did not become an exclusion

The first 2 Claude runs on `qwen3.5:4b` produced **zero edits** — one at 798 s, one hitting the
1200 s cap — while Ana solved the same task in 166 s. That is the signature of a non-functional
baseline, which would have made any Ana "win" on this model an artifact rather than a result, so
the sweep was stopped and Claude Code was probed directly on the same model.

It is not broken: it answered a plain question correctly (41 s) and, given a single-file bug,
**used its tools to apply a correct fix (54 s)**. The zero-edit runs are therefore the benchmark's
harder multi-file tasks defeating a 4B thinking model within the cap — a legitimate outcome, not
an instrumentation failure.

Those 7 partial runs were discarded and the model re-run from scratch, because the sweep had been
interrupted mid-matrix. Recorded here because the check could equally have gone the other way, and
the conclusion drawn from n=2 without it would have been wrong.
