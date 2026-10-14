#!/usr/bin/env python3
"""Runs tests/test_*.py in parallel and names the ones set aside.

`python3 tools/audit_tests.py` runs all of them; `--changed [FILE ...]` only the tests touched by the
changed files (the changed tests themselves + every test that imports a changed module, transitively).
Exit 1 if a test outside ASIDE failed. The daily audit imports `run_all` and `report`.
"""

import argparse
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.paths import ROOT

sys.path.insert(0, str(Path(__file__).resolve().parent))   # depmap, for --changed

TIMEOUT = 300   # seconds per test; a hang counts as a failure
WORKERS = 6

# Set aside, never silently: path -> (reason, date). The audit prints this list as "apartadas" and
# says when one passes again, so the entry is removed. Not a failure while listed.
ASIDE: dict[str, tuple[str, str]] = {
    "tests/test_commission_segments.py": (
        "Darwinex's commission is PercentageBased 0.005 in the asset cards, the donor's Build and "
        "Retest Setup still say SizeBased 5.0: cost cards in motion (assets/_build.yaml)", "2026-10-02"),
    "tests/test_perf66_catalogue.py": (
        "test_timing_unchanged_by_memory_pass_for_numpy_free_code compares two 50 ms busy-waits to "
        "20 ms: passes on an idle machine, fails under load (24 ms at load average 34)", "2026-10-14"),
    "tests/test_taxonomy.py": (
        "8 close-crosses blocks (Donchian, EMA, HMA, Keltner) entered sqx/blocks/taxonomy.yaml in "
        "c81dcbb with empty archetypes: their seven weights are an authoring call, not a test fix",
        "2026-10-14"),
    "tests/test_ui_results.py": (
        "the results catalogue does not match studies/ (board, marketProfile, memory, monteCarlo): "
        "ui/daemon/results/ and studies/research are in motion in another session", "2026-10-02"),
}


def run_one(path: str) -> tuple[str, int, float, str]:
    """Run one test file the way its README says: a plain script, or pytest when it only defines tests.

    pytest gets a file that defines `def test_` and has no `__main__`; anything else runs as a script —
    a file of module-level asserts would make pytest exit 5 (nothing collected), and one that ends in a
    module-level `sys.exit` an INTERNALERROR.

    Args:
        path: Repository-relative path of the test file.

    Returns:
        (path, exit code, seconds, last 40 lines of output). A timeout is exit code 124.
    """
    text = (ROOT / path).read_text(encoding="utf-8")
    pytest_style = "__main__" not in text and "def test_" in text
    command = ["python3", "-m", "pytest", "-q", path] if pytest_style else ["python3", path]
    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
    start = time.time()
    try:
        p = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True,
                           timeout=TIMEOUT)
        code, out = p.returncode, p.stdout + p.stderr
    except subprocess.TimeoutExpired:
        code, out = 124, f"timed out after {TIMEOUT} s"
    return path, code, time.time() - start, "\n".join(out.strip().splitlines()[-40:])[-3000:]


def run_all(paths: list[str] | None = None) -> tuple[list[tuple[str, int, float, str]], float]:
    """Run tests/test_*.py, six at a time.

    Args:
        paths: Repository-relative test paths; every tests/test_*.py when None.

    Returns:
        (one result per test, wall seconds).
    """
    if paths is None:
        paths = sorted(f"tests/{f.name}" for f in (ROOT / "tests").glob("test_*.py"))
    start = time.time()
    with ThreadPoolExecutor(WORKERS) as pool:
        return list(pool.map(run_one, paths)), time.time() - start


def report(results: list[tuple[str, int, float, str]], wall: float) -> tuple[list[str], int]:
    """Markdown lines for the audit and the number of failures not set aside.

    Args:
        results: What `run_all` returned.
        wall: Wall seconds of the whole run.

    Returns:
        (lines, failures not set aside).
    """
    failed = [r for r in results if r[1] and r[0] not in ASIDE]
    aside = [r for r in results if r[0] in ASIDE]
    passed = len(results) - len(failed) - sum(1 for r in aside if r[1])
    lines = [f"| `tests/test_*.py` | {len(results)} run in {wall:.0f} s: {passed} ok, "
             f"{len(failed)} {'FAILED' if failed else 'failed'}, {len(aside)} apartadas |"]
    detail = []
    if failed:
        detail += ["", "## failed tests", ""]
        for path, code, secs, out in failed:
            detail += [f"### `{path}` (exit {code}, {secs:.0f} s)", "", "```", out, "```", ""]
    detail += ["", "## apartadas", "", "| test | now | since | reason |", "|---|---|---|---|"]
    for path, code, _, _ in aside:
        reason, since = ASIDE[path]
        now = "fails" if code else "PASSES: remove it from ASIDE"
        detail.append(f"| `{path}` | {now} | {since} | {reason} |")
    gone = sorted(p for p in ASIDE if not (ROOT / p).exists())
    detail += [f"| `{p}` | file gone: remove it from ASIDE | | |" for p in gone]
    slow = sorted(results, key=lambda r: -r[2])[:3]
    detail += ["", "slowest: " + ", ".join(f"`{r[0]}` {r[2]:.0f} s" for r in slow)]
    return lines + detail, len(failed)


def select(changed: set[str], graph: dict[str, set[str]]) -> dict[str, str]:
    """The tests a change touches: changed tests themselves, plus tests importing a changed file.

    Args:
        changed: Repository-relative changed `.py` paths.
        graph: {file: files it imports}, repository-relative (depmap.file_graph, as strings).

    Returns:
        {test path: why}, why being the changed file it was reached from.
    """
    importers: dict[str, set[str]] = {}
    for file, deps in graph.items():
        for dep in deps:
            importers.setdefault(dep, set()).add(file)
    picked: dict[str, str] = {}
    for root in sorted(changed):
        seen, todo = {root}, [root]
        while todo:
            for f in importers.get(todo.pop(), ()):
                if f not in seen:
                    seen.add(f)
                    todo.append(f)
        for f in seen:
            if f.startswith("tests/test_") and f.count("/") == 1:
                picked.setdefault(f, root)
    return dict(sorted(picked.items()))


def git_changed() -> set[str]:
    """`.py` paths git sees as modified or untracked."""
    out = subprocess.run(["git", "status", "--porcelain", "-uall"], cwd=ROOT, capture_output=True,
                         text=True, check=True).stdout
    return {line[3:].split(" -> ")[-1].strip('"') for line in out.splitlines()
            if line[3:].endswith(".py")}


def main() -> None:
    """Run all tests, or with --changed the touched ones; print the report; exit 1 on a failure."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--changed", nargs="*", metavar="FILE",
                    help="only tests touched by FILEs (default: the .py files in git status)")
    args = ap.parse_args()
    paths = None
    if args.changed is not None:
        from depmap import file_graph, ROOT as DROOT
        graph = {str(f.relative_to(DROOT)): {str(d.relative_to(DROOT)) for d in deps}
                 for f, deps in file_graph().items()}
        changed = {c for c in args.changed if c.endswith(".py")} if args.changed else git_changed()
        picked = select(changed, graph)
        print(f"{len(changed)} changed .py -> {len(picked)} tests selected")
        for test, why in picked.items():
            print(f"  {test}  <- {why}")
        if not picked:
            return
        paths = list(picked)
    results, wall = run_all(paths)
    lines, failed = report(results, wall)
    print("\n".join(lines))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
