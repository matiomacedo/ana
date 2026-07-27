"""Ana benchmark runner.

Runs each fixture task in bench/tasks/ against coding-agent CLIs and scores
them by the task's success command (pytest). Both agents — Ana and Claude
Code — are pointed at the SAME local Ollama models, so runs are free and the
comparison isolates the agent scaffolding, not the model:

- ana:    `ana print --model <m>` (installed binary; backend talks to Ollama)
- claude: Ollama's native Anthropic-compatible API via ANTHROPIC_BASE_URL

(opencode was dropped: its `run` subcommand exits silently or hangs when
spawned non-interactively with an inherited environment — it only behaved
under a stripped-down env — which makes it unbenchmarkable as a subprocess.)

An *arm* is an (agent, variant) pair. The variant applies an env overlay to
the agent, which is how ablations run: `ana:noverify` is Ana with its
deterministic verification loop switched off. Arms are recorded in the result
row, so an ablation can never overwrite the baseline it is measured against.

Standard library only. Run `bench/validate.py` first, then:

    python bench/runner.py --arm ana
    python bench/runner.py --arm ana --arm claude --model gpt-oss:20b
    python bench/runner.py --arm ana:noverify --tier xfile --repeat 2
"""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

BENCH_DIR = Path(__file__).resolve().parent
REPO_ROOT = BENCH_DIR.parent
TASKS_DIR = BENCH_DIR / "tasks"
REPORT_PATH = BENCH_DIR / "report.md"
# Every result is appended here the moment it lands, and the report is
# regenerated from the full accumulated set — a crash mid-matrix (agent bug,
# revoked filesystem permission, power loss) can no longer lose completed
# runs, and interrupted sweeps resume by simply re-running the missing
# combos. Latest entry wins per (agent, variant, model, task, run_index).
RESULTS_PATH = BENCH_DIR / "results.jsonl"
# Per-run evidence: the workspace diff the agent produced, its output, and the
# scoring output. Kept because the paper's central claim is about *why* runs
# fail (dangling cross-file references), which pass/fail alone cannot show.
ARTIFACTS_DIR = BENCH_DIR / "artifacts"

# The per-task cap must not decide the result. A cap set near typical runtimes
# silently scores the *slower* agent lower — it converts throughput into pass
# rate and hides genuine successes as failures. Observed healthy runs land at
# roughly 130-270 s, so 1200 s is far enough out that it only fires when a run
# is actually stuck, at which point failure is the correct verdict.
#
# Wall-clock is still reported: agent_seconds is recorded per run, so pass rate
# under any tighter budget can be computed after the fact (paper/stats.py) as a
# measured outcome rather than baked into scoring. Use --budget-seconds to bound
# the whole sweep instead of squeezing individual tasks.
DEFAULT_TIMEOUT = 1200.0

# Fixed so a shuffled sweep is reproducible.
ORDER_SEED = 20260726

DEFAULT_MODELS = ["qwen3.5:4b", "gpt-oss:20b"]
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")

# Command templates. {prompt}, {workspace}, and {model} are substituted per
# run. EVERY agent executes with cwd={workspace} — this is a fairness
# requirement, not a convenience. An earlier version launched Ana via
# `uv run` from the repo root (which `uv run` needs for its pyproject) while
# the competitor ran from the task workspace. That handed one agent an entire
# unrelated monorepo as its working directory: it inflated that agent's
# runtime, and it let a run mutate a benchmark fixture on disk, silently
# pre-solving a task for every later run. Ana is invoked as the globally
# installed `ana` binary precisely so it needs no repo context.
AGENTS: dict[str, dict[str, object]] = {
    "ana": {
        "argv": [
            "ana",
            "print",
            "--mode",
            "auto_accept",
            "--model",
            "{model}",
            "--project-dir",
            "{workspace}",
            "{prompt}",
        ],
        "cwd": "workspace",
    },
    "claude": {
        "argv": [
            "claude",
            "--model",
            "{model}",
            "-p",
            "{prompt}",
            "--dangerously-skip-permissions",
        ],
        "cwd": "workspace",
        # Ollama speaks the Anthropic Messages API natively (since Jan 2026):
        # point Claude Code at it and blank the cloud key so no request can
        # ever reach (or bill) the Anthropic API.
        "env": {
            "ANTHROPIC_BASE_URL": OLLAMA_HOST,
            "ANTHROPIC_AUTH_TOKEN": "ollama",
            "ANTHROPIC_API_KEY": "",
            "ANTHROPIC_SMALL_FAST_MODEL": "{model}",
            "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
        },
    },
}

# Ablation arms. The env overlay is applied on top of the agent's own overlay.
VARIANTS: dict[str, dict[str, str]] = {
    "default": {},
    # Disables the post-edit verification loop (syntax/lint/test re-runs and
    # the cross-file stale-reference check) — the mechanism under test.
    "noverify": {"ANA_VERIFY_LEVEL": "off"},
}


# A benchmarked agent must not inherit the environment of whatever launched
# the sweep. Two concrete ways that corrupts a run, both observed here:
#   - CLAUDECODE / CLAUDE_CODE_* are set whenever the sweep is started from
#     inside a Claude Code session. The child then runs as a *nested* session
#     and silently stops applying its edits — it narrates changes it never
#     made, and the workspace comes back untouched. Ana is affected too: it
#     produced empty output and no edits under the same leak.
#   - a stray ANA_* exported in the shell would override the ablation variant
#     under test, so the arm would not be what the results claim it is.
# Everything the run legitimately needs is re-applied from the arm's overlay.
CONTAMINATING_PREFIXES = ("CLAUDE", "ANTHROPIC", "ANA_")


def scrubbed_environ() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if not k.startswith(CONTAMINATING_PREFIXES)}


def check_models_pulled(models: list[str]) -> list[str]:
    """Return the subset of models NOT available on the Ollama server."""
    try:
        with urllib.request.urlopen(f"{OLLAMA_HOST}/api/tags", timeout=5) as resp:
            tags = json.loads(resp.read())
    except (urllib.error.URLError, OSError, json.JSONDecodeError):
        sys.exit(f"Ollama is not reachable at {OLLAMA_HOST} — start it first.")
    available = {str(m.get("name", "")) for m in tags.get("models", [])}
    # `ollama list` reports name:tag; accept both exact and :latest-less matches.
    return [m for m in models if m not in available and f"{m}:latest" not in available]


# Claude Code relies on the server's context length (Ana requests
# num_ctx per call, so it is immune). Below this, their large system prompts
# get truncated and runs fail as garbage tool use rather than as errors.
MIN_COMPETITOR_CONTEXT = 16384


def check_server_context(model: str) -> None:
    """Load `model` and abort when the server's context window is too small
    for competitor CLIs. Best-effort: probe failures never block the run."""
    try:
        req = urllib.request.Request(
            f"{OLLAMA_HOST}/api/generate",
            data=json.dumps({"model": model}).encode(),  # prompt-less = load only
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=300).read()
        with urllib.request.urlopen(f"{OLLAMA_HOST}/api/ps", timeout=5) as resp:
            loaded = json.loads(resp.read()).get("models", [])
    except (urllib.error.URLError, OSError, json.JSONDecodeError):
        return
    for entry in loaded:
        if str(entry.get("name", "")) not in (model, f"{model}:latest"):
            continue
        ctx = int(entry.get("context_length", 0) or 0)
        if 0 < ctx < MIN_COMPETITOR_CONTEXT:
            sys.exit(
                f"Ollama is serving {model} with a {ctx}-token context — "
                f"Claude Code needs >= {MIN_COMPETITOR_CONTEXT}. Restart the server with a larger "
                "window, e.g.:\n  OLLAMA_CONTEXT_LENGTH=32768 ollama serve"
            )


# A degraded Ollama server is indistinguishable, from inside a run, from an
# agent that simply does nothing: every task burns its full timeout, produces no
# edit and no output, and the arm scores zero. That happened once and silently
# invalidated a whole ablation arm, detected only afterwards. Preflight a
# trivial generation and refuse to start if the server cannot answer promptly.
HEALTH_PROMPT_TIMEOUT = 90.0


def check_server_responsive(model: str) -> None:
    """Abort when a trivial generation does not return quickly."""
    payload = json.dumps({"model": model, "prompt": "Say OK", "stream": False}).encode()
    req = urllib.request.Request(
        f"{OLLAMA_HOST}/api/generate", data=payload, headers={"Content-Type": "application/json"}
    )
    start = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=HEALTH_PROMPT_TIMEOUT) as resp:
            json.loads(resp.read())
    except (urllib.error.URLError, OSError, json.JSONDecodeError, TimeoutError):
        sys.exit(
            f"Ollama did not answer a trivial prompt for {model} within "
            f"{HEALTH_PROMPT_TIMEOUT:.0f}s. The server is degraded — every run would "
            "time out with no edit and score zero, which looks exactly like an agent "
            "failure. Restart it (e.g. OLLAMA_CONTEXT_LENGTH=32768 ollama serve) and "
            "re-run."
        )
    print(f"ollama healthy: {model} answered in {time.monotonic() - start:.0f}s", flush=True)


@dataclass
class TaskResult:
    task: str
    agent: str
    model: str
    passed: bool
    agent_seconds: float
    detail: str = ""
    # Fields below default so the pre-repeat result rows still load.
    variant: str = "default"
    run_index: int = 0
    timed_out: bool = False
    made_edit: bool = False
    edited_tests: bool = False
    started_at: str = ""

    @property
    def arm(self) -> str:
        return self.agent if self.variant == "default" else f"{self.agent}:{self.variant}"


def _task_tier(task_dir: Path) -> str:
    """Tier tag from task.json; untagged tasks are the default 'smoke' tier."""
    try:
        spec = json.loads((task_dir / "task.json").read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return "smoke"
    return str(spec.get("tier", "smoke"))


def load_tasks(only: list[str] | None, tiers: list[str] | None) -> list[Path]:
    tasks = sorted(d for d in TASKS_DIR.iterdir() if (d / "task.json").is_file())
    if tiers:
        tasks = [t for t in tasks if _task_tier(t) in tiers]
    if only:
        missing = set(only) - {t.name for t in tasks}
        if missing:
            sys.exit(f"Unknown tasks: {', '.join(sorted(missing))}")
        tasks = [t for t in tasks if t.name in only]
    return tasks


def _slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", text)


def workspace_diff(fixture: Path, workspace: Path) -> str:
    """Unified diff of everything the agent changed, added, or deleted."""
    names = sorted(
        {p.name for p in fixture.glob("*.py")} | {p.name for p in workspace.glob("*.py")}
    )

    def _lines(path: Path) -> list[str]:
        if not path.is_file():
            return []
        return path.read_text(encoding="utf-8", errors="replace").splitlines(True)

    out: list[str] = []
    for name in names:
        a = _lines(fixture / name)
        b = _lines(workspace / name)
        out += difflib.unified_diff(a, b, f"a/{name}", f"b/{name}")
    return "".join(out)


def run_task(
    agent: str, variant: str, model: str, task_dir: Path, timeout: float, run_index: int
) -> TaskResult:
    spec = json.loads((task_dir / "task.json").read_text(encoding="utf-8"))
    fixture = task_dir / "fixture"
    workspace = Path(tempfile.mkdtemp(prefix=f"bench-{task_dir.name}-"))
    shutil.copytree(fixture, workspace, dirs_exist_ok=True)

    template = AGENTS[agent]
    started_at = dt.datetime.now(dt.UTC).isoformat(timespec="seconds")

    def _sub(value: str) -> str:
        return value.format(prompt=spec["prompt"], workspace=str(workspace), model=model)

    argv = [_sub(str(part)) for part in template["argv"]]  # type: ignore[union-attr]
    cwd = REPO_ROOT if template["cwd"] == "repo" else workspace
    overlay = {**template.get("env", {}), **VARIANTS[variant]}  # type: ignore[dict-item]
    env = {**scrubbed_environ(), **{k: _sub(str(v)) for k, v in overlay.items()}}

    def _result(passed: bool, seconds: float, detail: str, **kw: object) -> TaskResult:
        return TaskResult(
            task=task_dir.name,
            agent=agent,
            model=model,
            passed=passed,
            agent_seconds=seconds,
            detail=detail,
            variant=variant,
            run_index=run_index,
            started_at=started_at,
            **kw,  # type: ignore[arg-type]
        )

    start = time.monotonic()
    timed_out = False
    agent_log = ""
    try:
        proc = subprocess.run(
            argv, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout, check=False
        )
        agent_log = (proc.stdout or "") + (proc.stderr or "")
        if proc.returncode == 0:
            detail = ""
        else:
            tail = (proc.stderr or proc.stdout or "").strip().splitlines()
            detail = f"agent exit {proc.returncode}: {tail[-1][:150] if tail else 'no output'}"
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        partial = exc.stdout or b""
        agent_log = partial.decode("utf-8", "replace") if isinstance(partial, bytes) else partial
        detail = f"agent timed out after {timeout:.0f}s"
    except FileNotFoundError:
        shutil.rmtree(workspace, ignore_errors=True)
        return _result(False, 0.0, f"'{argv[0]}' not installed")
    elapsed = time.monotonic() - start

    # Snapshot before restoring tests so the artifact shows exactly what the
    # agent did — including any attempt to edit the tests themselves.
    diff = workspace_diff(fixture, workspace)
    edited_tests = any(line.startswith("+++ b/test_") for line in diff.splitlines())

    # The agent must not "solve" the task by editing tests or the scorer's
    # inputs; the fixture's test files are restored before scoring.
    for test_file in fixture.glob("test_*.py"):
        shutil.copy2(test_file, workspace / test_file.name)

    check = subprocess.run(
        spec.get("success_command", ["python", "-m", "pytest", "-x", "-q"]),
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    tests_green = check.returncode == 0
    # A run that blew its time budget is a failure even if the workspace it
    # left behind happens to pass: the agent never declared itself done, and
    # crediting it would reward hitting the cap. The workspace verdict is kept
    # in `detail` so the discarded outcome stays visible.
    passed = tests_green and not timed_out
    if timed_out and tests_green:
        detail += " (workspace passed tests, but scored as failure)"
    if not passed and not detail:
        detail = (
            (check.stdout + check.stderr).strip().splitlines()[-1][:120]
            if (check.stdout or check.stderr)
            else "tests failed"
        )

    result = _result(
        passed,
        elapsed,
        detail,
        timed_out=timed_out,
        made_edit=bool(diff.strip()),
        edited_tests=edited_tests,
    )
    _write_artifacts(result, diff, agent_log, check.stdout + check.stderr)
    shutil.rmtree(workspace, ignore_errors=True)
    return result


def _write_artifacts(result: TaskResult, diff: str, agent_log: str, pytest_log: str) -> None:
    slug = f"{_slug(result.model)}/{_slug(result.arm)}-{result.task}-r{result.run_index}"
    out = ARTIFACTS_DIR / slug
    out.mkdir(parents=True, exist_ok=True)
    (out / "diff.txt").write_text(diff, encoding="utf-8")
    (out / "agent.log").write_text(agent_log[-200_000:], encoding="utf-8")
    (out / "pytest.txt").write_text(pytest_log[-20_000:], encoding="utf-8")
    (out / "meta.json").write_text(json.dumps(asdict(result), indent=2), encoding="utf-8")


def record_result(result: TaskResult) -> None:
    with open(RESULTS_PATH, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(asdict(result)) + "\n")


def load_results(path: Path | None = None) -> list[TaskResult]:
    """All accumulated results, deduped: the latest run of a combo wins."""
    src = path or RESULTS_PATH
    if not src.is_file():
        return []
    latest: dict[tuple[str, str, str, str, int], TaskResult] = {}
    for line in src.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            result = TaskResult(**data)
        except (json.JSONDecodeError, TypeError):
            continue  # a torn write from a crash must not poison the report
        latest[(result.agent, result.variant, result.model, result.task, result.run_index)] = result
    return list(latest.values())


def write_report(results: list[TaskResult]) -> None:
    combos = sorted({(r.arm, r.model) for r in results})
    lines = ["# Benchmark report", "", f"Ollama: `{OLLAMA_HOST}`", ""]
    lines += [
        "| Arm | Model | Passed | Runs | Total time |",
        "|---|---|---|---|---|",
    ]
    for arm, model in combos:
        rs = [r for r in results if (r.arm, r.model) == (arm, model)]
        lines.append(
            f"| {arm} | {model} | {sum(r.passed for r in rs)}/{len(rs)} "
            f"| {len(rs)} | {sum(r.agent_seconds for r in rs):.0f}s |"
        )
    lines.append("")
    for arm, model in combos:
        rs = sorted(
            (r for r in results if (r.arm, r.model) == (arm, model)),
            key=lambda r: (r.task, r.run_index),
        )
        lines += [
            f"## {arm} · {model}",
            "",
            "| Task | Rep | Result | Time | Detail |",
            "|---|---|---|---|---|",
        ]
        lines += [
            f"| {r.task} | {r.run_index} | {'✅ pass' if r.passed else '❌ fail'} "
            f"| {r.agent_seconds:.0f}s | {r.detail or '—'} |"
            for r in rs
        ]
        lines.append("")
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


# A run that exhausts its timeout having written nothing is the signature of a
# dead backend, not a struggling agent: a slow-but-working agent leaves partial
# edits behind. Several of these in a row means every remaining run will also
# burn its full timeout producing nothing — 88 runs x 1200 s is over a day of
# grinding out an arm of zeros that then has to be discarded. Stop instead, and
# say why.
DEAD_RUN_LIMIT = 3


def is_dead_run(result: TaskResult) -> bool:
    return result.timed_out and not result.made_edit


def parse_arm(spec: str) -> tuple[str, str]:
    agent, _, variant = spec.partition(":")
    variant = variant or "default"
    if agent not in AGENTS:
        sys.exit(f"Unknown agent {agent!r} in arm {spec!r}. Known: {', '.join(sorted(AGENTS))}")
    if variant not in VARIANTS:
        known = ", ".join(sorted(VARIANTS))
        sys.exit(f"Unknown variant {variant!r} in arm {spec!r}. Known: {known}")
    if variant != "default" and agent != "ana":
        sys.exit(f"Variant {variant!r} only applies to ana (arm {spec!r}).")
    return agent, variant


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--arm",
        action="append",
        help="Arm to run as 'agent' or 'agent:variant' (repeatable; default: ana)",
    )
    parser.add_argument(
        "--model",
        action="append",
        help=f"Ollama model(s) to benchmark (repeatable; default: {', '.join(DEFAULT_MODELS)})",
    )
    parser.add_argument("--tasks", help="Comma-separated task names (default: all)")
    parser.add_argument(
        "--tier", action="append", help="Only run tasks in this tier (repeatable, e.g. xfile)"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=f"Seconds per task (default {DEFAULT_TIMEOUT:.0f}); sized so it does "
        "not bind on a healthy run — see DEFAULT_TIMEOUT",
    )
    parser.add_argument("--repeat", type=int, default=1, help="Repetitions of the whole matrix")
    parser.add_argument(
        "--budget-seconds",
        type=float,
        help="Stop cleanly once the sweep has run this long (repeats are the outer "
        "loop, so a truncated sweep still leaves a balanced matrix)",
    )
    parser.add_argument(
        "--first-rep",
        type=int,
        default=1,
        help="Index of the first repetition (use 2 to add a second rep to an "
        "existing rep-1 matrix without re-running it)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip (arm, model, task, rep) combos already in results.jsonl, so an "
        "interrupted sweep continues instead of repeating completed work",
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Discard previously accumulated results before running",
    )
    args = parser.parse_args()

    if args.fresh:
        RESULTS_PATH.unlink(missing_ok=True)

    arms = [parse_arm(a) for a in (args.arm or ["ana"])]
    models = args.model or DEFAULT_MODELS
    missing = check_models_pulled(models)
    if missing:
        pulls = "\n".join(f"  ollama pull {m}" for m in missing)
        sys.exit(f"Models not available on {OLLAMA_HOST}:\n{pulls}")

    for model in models:
        check_server_responsive(model)
    if any(agent != "ana" for agent, _ in arms):
        check_server_context(models[0])

    tasks = load_tasks(args.tasks.split(",") if args.tasks else None, args.tier)
    if not tasks:
        sys.exit(f"No tasks matched (tier={args.tier!r}).")

    reps = range(args.first_rep, args.repeat + 1)
    # Count only the (arm, task) pairs that will actually run: ablation arms are
    # skipped off-tier, so the naive product would overstate the sweep.
    planned = (
        len(reps)
        * len(models)
        * sum(
            1
            for _, variant in arms
            for t in tasks
            if variant == "default" or _task_tier(t) == "xfile"
        )
    )
    print(
        f"{planned} runs planned: {len(reps)} rep(s) x {len(arms)} arm(s) "
        f"x {len(models)} model(s) x {len(tasks)} task(s)",
        flush=True,
    )

    already_done: set[tuple[str, str, str, str, int]] = set()
    if args.resume:
        already_done = {(r.agent, r.variant, r.model, r.task, r.run_index) for r in load_results()}
        print(f"resuming: {len(already_done)} completed runs will be skipped", flush=True)

    sweep_start = time.monotonic()
    done = 0
    dead = 0
    truncated = False
    # Loop order matters for more than tidiness.
    #
    # Repeats are OUTERMOST: if the budget runs out mid-sweep, what survives is a
    # complete rep-1 matrix rather than one arm measured twice and another not at
    # all.
    #
    # Arms are INNERMOST, so every arm runs back-to-back on the same task. A
    # previous sweep ran arm-major, which meant the last arm absorbed whatever
    # the machine had drifted into by then — an Ollama server that degraded late
    # in the session wiped out one whole ablation arm, and the arm looked like it
    # had simply failed. Interleaving spreads drift evenly over all arms.
    #
    # Task order is shuffled per repeat (seeded, so a sweep is reproducible), so
    # that a task's position in the run is not confounded with its identity.
    for rep in reps:
        for model in models:
            ordered_tasks = list(tasks)
            random.Random(ORDER_SEED + rep).shuffle(ordered_tasks)
            for task_dir in ordered_tasks:
                for agent, variant in arms:
                    spent = time.monotonic() - sweep_start
                    if args.budget_seconds and spent >= args.budget_seconds:
                        truncated = True
                        break
                    arm = agent if variant == "default" else f"{agent}:{variant}"
                    # An ablation arm only earns its runtime on the tier whose
                    # mechanism it disables. Skipping it elsewhere is what lets
                    # the ablation share ONE invocation with the baseline arms,
                    # so all three interleave per task and any machine drift is
                    # spread over them evenly instead of landing on whichever
                    # arm happened to run last.
                    if variant != "default" and _task_tier(task_dir) != "xfile":
                        continue
                    if (agent, variant, model, task_dir.name, rep) in already_done:
                        continue
                    label = f"[rep {rep}] [{arm} · {model}] {task_dir.name}"
                    print(f"{label} …", flush=True)
                    try:
                        result = run_task(agent, variant, model, task_dir, args.timeout, rep)
                    except Exception as exc:  # one crashed run must not kill the matrix
                        result = TaskResult(
                            task=task_dir.name,
                            agent=agent,
                            model=model,
                            passed=False,
                            agent_seconds=0.0,
                            detail=f"runner error: {exc}",
                            variant=variant,
                            run_index=rep,
                        )
                    done += 1
                    dead = dead + 1 if is_dead_run(result) else 0
                    status = "pass" if result.passed else f"FAIL ({result.detail})"
                    print(f"{label}: {status} in {result.agent_seconds:.0f}s")
                    record_result(result)
                    # Regenerate after every task so the report is always current,
                    # even if a later run takes the whole process down.
                    write_report(load_results())
                    if dead >= DEAD_RUN_LIMIT:
                        print(
                            f"\nABORTING: {dead} consecutive runs timed out having made no "
                            "edit at all. That is a dead backend, not an agent failure — "
                            "every further run would burn its full timeout and score zero. "
                            "Restart Ollama (OLLAMA_CONTEXT_LENGTH=32768 ollama serve) and "
                            "re-run with --resume to pick up where this stopped.",
                            flush=True,
                        )
                        truncated = True
                        break
                if truncated:
                    break
            if truncated:
                break
        if truncated:
            break

    mins = (time.monotonic() - sweep_start) / 60
    print(f"\n{done}/{planned} runs in {mins:.0f} min → {REPORT_PATH} ({RESULTS_PATH.name} is raw)")
    if truncated:
        print(
            f"BUDGET EXHAUSTED after {done} runs — re-run the same command to "
            "finish the remaining combos (completed runs are not repeated only "
            "if you narrow --tasks/--repeat; results are latest-wins per rep)."
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
