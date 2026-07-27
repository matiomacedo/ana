"""Bidirectional validation of every benchmark task.

A task is only a valid measurement if it is *failing*, *solvable*, and — for
the cross-file tier — *not satisfiable by a shortcut*:

  1. the untouched fixture must FAIL its success command — otherwise the task
     scores as solved before the agent has done anything;
  2. the fixture with solution/ applied must PASS — otherwise the task is
     unsolvable and every agent is scored against an impossible target;
  3. the fixture with cheat/ applied must FAIL — otherwise the task does not
     measure what its tier claims. A cross-file task that a single-file edit can
     satisfy counts an unreconciled edit as a success, which is precisely the
     failure mode the tier exists to detect. Four of these were found by audit
     and repaired; the check now runs on every sweep so they cannot come back.

This used to be an authoring convention. It is now a gate: run it before any
sweep, because a broken fixture is far cheaper to catch here than after it has
burned an hour of benchmark time.

    python bench/validate.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from runner import TASKS_DIR, _task_tier


def _run_success_command(spec: dict[str, object], workspace: Path) -> tuple[bool, str]:
    command = spec.get("success_command", ["python", "-m", "pytest", "-x", "-q"])
    proc = subprocess.run(
        list(command),  # type: ignore[arg-type]
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    tail = (proc.stdout + proc.stderr).strip().splitlines()
    return proc.returncode == 0, tail[-1][:120] if tail else ""


def _materialise(task_dir: Path, overlay: str | None) -> Path:
    workspace = Path(tempfile.mkdtemp(prefix=f"validate-{task_dir.name}-"))
    shutil.copytree(task_dir / "fixture", workspace, dirs_exist_ok=True)
    if overlay:
        for src in sorted((task_dir / overlay).glob("*.py")):
            shutil.copy2(src, workspace / src.name)
        # The solution must never smuggle in a test edit; the runner restores
        # the fixture's tests before scoring, so mirror that here exactly.
        for test_file in (task_dir / "fixture").glob("test_*.py"):
            shutil.copy2(test_file, workspace / test_file.name)
    return workspace


def validate_task(task_dir: Path) -> list[str]:
    """Return a list of problems; empty means the task is a valid measurement."""
    problems: list[str] = []
    try:
        spec = json.loads((task_dir / "task.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"unreadable task.json: {exc}"]

    # A fixture file that shadows a stdlib module breaks imports in ways that
    # have nothing to do with the task (a fixture named queue.py made pytest's
    # own dependencies import the fixture instead of stdlib queue). That would
    # score as an agent failure, so it is rejected here.
    shadowed = sorted(
        f.stem
        for f in (task_dir / "fixture").glob("*.py")
        if f.stem in sys.stdlib_module_names and not f.stem.startswith("test_")
    )
    if shadowed:
        problems.append(f"fixture shadows stdlib module(s): {', '.join(shadowed)}")

    for field in ("tier", "description", "prompt"):
        if not spec.get(field):
            problems.append(f"task.json is missing {field!r}")
    if not (task_dir / "solution").is_dir() or not any((task_dir / "solution").glob("*.py")):
        return [*problems, "no solution/ — the task cannot be shown to be solvable"]

    def check(overlay: str | None) -> tuple[bool, str]:
        workspace = _materialise(task_dir, overlay)
        result = _run_success_command(spec, workspace)
        shutil.rmtree(workspace, ignore_errors=True)
        return result

    passed, _ = check(None)
    if passed:
        problems.append("untouched fixture PASSES — the task is already solved")

    passed, detail = check("solution")
    if not passed:
        problems.append(f"solution FAILS — the task is unsolvable as written ({detail})")

    cheat = task_dir / "cheat"
    if cheat.is_dir() and any(cheat.glob("*.py")):
        passed, _ = check("cheat")
        if passed:
            touched = ", ".join(sorted(p.name for p in cheat.glob("*.py")))
            problems.append(
                f"cheat PASSES — editing only {touched} satisfies the tests, so this "
                "task does not require the cross-file reconciliation its tier claims"
            )
    elif spec.get("tier") == "xfile":
        problems.append("no cheat/ — an xfile task must prove a single-file edit cannot pass")

    return problems


def main() -> int:
    tasks = sorted(d for d in TASKS_DIR.iterdir() if (d / "task.json").is_file())
    if not tasks:
        sys.exit(f"No tasks found under {TASKS_DIR}")

    failures = 0
    by_tier: dict[str, int] = {}
    for task_dir in tasks:
        tier = _task_tier(task_dir)
        by_tier[tier] = by_tier.get(tier, 0) + 1
        problems = validate_task(task_dir)
        if problems:
            failures += 1
            print(f"✗ {task_dir.name} [{tier}]")
            for problem in problems:
                print(f"    {problem}")
        else:
            print(f"✓ {task_dir.name} [{tier}]")

    tiers = ", ".join(f"{name}={count}" for name, count in sorted(by_tier.items()))
    print(f"\n{len(tasks) - failures}/{len(tasks)} tasks valid ({tiers})")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
