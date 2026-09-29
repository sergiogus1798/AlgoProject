#!/usr/bin/env python3
"""Rewrite one already-configured task -- SPP IS, SPP OOS or OOS -- from a donor known to run."""

import argparse
import re
import subprocess
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.datapaths import projects_backup
from core.paths import WORKERS, worker_dir
from sqx.projects.crosschecks import member_of
from sqx.variants import inputs

# Which task of the TARGET project each kind rewrites, by title -- never by file name. A
# workflow project's "Retest-Task1.xml" is its real `OOS` task, not a spare slot (OPEN.md §38).
TITLES = {"spp_is": "SPP IS", "spp_oos": "SPP OOS", "retest": "OOS"}
# Donor tasks, by what they are for -- the owner's own XAUUSD settings, frozen: copying one
# is how a harness inherits a configuration known to work (knowhow/conditions/active-conditions-in-crosschecks.md).
DONOR = {"spp_is": "Retest-Task13.xml", "spp_oos": "Retest-Task14.xml", "retest": "Retest-Task1.xml"}
CHART = re.compile(r'<Chart symbol="[^"]*" timeframe="[^"]*" spread="([^"]*)" ?/>')


def donor_task(kind: str) -> str:
    """One task of the frozen donor project, as text.

    Args:
        kind: A key of `DONOR`.

    Returns:
        The task XML. The donor is the frozen copy in the data root, never the live master:
        SQX rewrites a project.cfx on save and on exit, so the live one is not a fixed
        point and cannot be a donor.
    """
    cfx = sorted(projects_backup("").glob("*/project.cfx"))[-1]
    return zipfile.ZipFile(cfx).read(DONOR[kind]).decode("utf-8")


def retarget(task: str, symbols: list[str], databanks: tuple[str, str]) -> str:
    """Point every chart at symbols this install has, and name the two databanks.

    Args:
        task: Donor task XML.
        symbols: `symbol timeframe spread` triples, main chart first. A chart with no
            symbol given keeps the donor's.
        databanks: (input, output) databank names.

    Returns:
        The rewritten XML.

        ⚠️ Every `<Chart>` is retargeted, including those of cross-checks that are switched
        off: SQX resolves all of a task's symbols when it loads the project's resources, and
        one it cannot find kills the task without failing it.
    """
    charts = iter(symbols)
    task = CHART.sub(lambda m: next(charts, None) or m.group(0), task)
    task = re.sub(r'(<Databank label="Input databank" name="Input" value=")[^"]*"',
                  rf'\g<1>{databanks[0]}"', task)
    return re.sub(r'(<Databank label="Output databank" name="Output" value=")[^"]*"',
                  rf'\g<1>{databanks[1]}"', task)


def ungate(task: str) -> str:
    """Remove everything that would silently drop a strategy from the output.

    Args:
        task: Task XML.

    Returns:
        The XML with acceptance conditions off, failed strategies kept, and the selection
        flag set. A parameter study cannot afford a filter: a variant that was dropped and
        a variant that lost money become the same thing, and the count stops meaning
        anything. `retestSelected="false"` is the one that decides whether the task runs at
        all -- without it SQX retests the (empty) selection and reports zero.
    """
    task = task.replace('<Condition use="true">', '<Condition use="false">')
    task = task.replace("<DeleteFailedStrategies>true", "<DeleteFailedStrategies>false")
    if 'retestSelected="false"' not in task:
        task = task.replace("<Databanks>", '<Databanks retestSelected="false">')
    return task


def cross_check(task: str, name: str, on: bool) -> str:
    """Turn one named cross-check on or off.

    Args:
        task: Task XML.
        name: Element name, e.g. `SequentialOptimization`.
        on: Whether it should run.

    Returns:
        The XML with that element's `use` set. `<CrossChecks use>` is the master switch and
        is set alongside, because an enabled cross-check under a disabled parent does
        nothing.
    """
    task = re.sub(rf'<{name} use="(?:true|false)"', f'<{name} use="{str(on).lower()}"', task, 1)
    return re.sub(r'<CrossChecks use="(?:true|false)"',
                  f'<CrossChecks use="{str(on).lower()}"', task, 1) if on else task


def spp(task: str, spread: int, step_pct: float, max_tests: int) -> str:
    """Configure the System Parameter Permutation cross-check, and only that one.

    Args:
        task: Task XML.
        spread: Percent up and down from each parameter's value.
        step_pct: How much one step moves a parameter, as a percent of its value. `Steps`
            is derived from it: the walk spans `2 * spread` percent, so that many steps.
        max_tests: Ceiling on how many permutations SQX runs.

    Returns:
        The XML with `OptProfileSysParamPermutation` on and `SequentialOptimization` off.

        ⚠️ **`OptProfileSysParamPermutation` is the SPP. `SequentialOptimization` is not.**
        They sit side by side in the same `<CrossChecks>` block and both talk about
        permuting parameters; the second one walks parameters one at a time looking for a
        better setting, which is a different question and a different cost. Turning on the
        wrong one burns hours and produces no profile.

        ⚠️ **`MaxTests` must be set, never inherited.** A donor task can carry
        `1000000001`, which is SQX's sentinel for *exhaustive* -- every combination of
        every parameter. On a real strategy that is not a long run, it is an unbounded
        one.

        Steps: one step of ~4 % is the house default. Twelve steps over ±30 % is 5 % a
        step and coarse; twenty over ±40 % is 4 % and right.
    """
    block = re.search(r"<OptProfileSysParamPermutation\b.*?</OptProfileSysParamPermutation>",
                      task, re.S)
    inner = block.group(0)
    inner = re.sub(r'<OptProfileSysParamPermutation use="(?:true|false)"',
                   '<OptProfileSysParamPermutation use="true"', inner, 1)
    for tag, value in (("MaxTests", max_tests), ("DistributionUp", spread),
                       ("DistributionDown", spread),
                       ("Steps", round(2 * spread / step_pct))):
        inner = re.sub(rf"<{tag}>\d+</{tag}>", f"<{tag}>{value}</{tag}>", inner, 1)
    inner = recommended(inner)
    task = task[:block.start()] + inner + task[block.end():]
    return cross_check(task, "SequentialOptimization", False)


def recommended(inner: str) -> str:
    """Permute the recommended parameters, and nothing else.

    Args:
        inner: The `OptProfileSysParamPermutation` element.

    Returns:
        The element with `WhatToParametrize` set to SQX's "Recommended parameters" choice:
        `type="0"`, `Recommended` true, every other family false. Picking families by hand
        -- periods and constants and used exit parameters, which is what a donor task may
        carry -- permutes things the strategy does not actually key on and inflates the run
        for nothing.
    """
    what = re.search(r"<WhatToParametrize\b.*?</WhatToParametrize>", inner, re.S)
    block = re.sub(r'type="\d+"', 'type="0"', what.group(0), 1)
    block = re.sub(r"<Recommended>(?:true|false)</Recommended>",
                   "<Recommended>true</Recommended>", block, 1)
    for family in ("Periods", "Shifts", "Constants", "OtherParams", "EntryParams",
                   "EntryLogic", "ExitParamsUsed", "ExitParamsUnused", "BooleanParams"):
        block = re.sub(rf"<{family}>(?:true|false)</{family}>",
                       f"<{family}>false</{family}>", block, 1)
    return inner[:what.start()] + block + inner[what.end():]


def write(cfx: Path, task: str, kind: str, role: str) -> Path:
    """Replace one task member of a project.cfx, found by title -- never any other task's.

    Args:
        cfx: The project.cfx to rewrite -- the mother's own workflow project (hard rule
            10), which already carries "SPP IS" and "SPP OOS" (`sqx/projects/stages.yaml`,
            kept from the donor by `sqx.projects.builder --workflow`). Never a separate
            project built just to hold the harness.
        task: The finished task XML.
        kind: A key of `TITLES` -- which of the project's own tasks this run owns.
        role: Worker role that owns the install.

    Returns:
        The same `cfx`, rewritten.

    Raises:
        SystemExit: The install is running (hard rule 4), or the project carries no task
            titled `TITLES[kind]`.
    """
    listening = subprocess.run(["ss", "-ltn"], capture_output=True, text=True).stdout
    if f':{WORKERS[role]["port"]} ' in listening:
        raise SystemExit(f"{role} esta levantado: paralo antes de reescribir {cfx.parent.name}")
    with zipfile.ZipFile(cfx) as z:
        members = {n: z.read(n) for n in z.namelist()}
    member = member_of(members["config.xml"].decode("utf-8"), TITLES[kind])
    if not member:
        raise SystemExit(f"{cfx.parent.name} no lleva la tarea {TITLES[kind]!r}: un proyecto "
                         "de workflow se crea con `sqx.projects.builder --workflow` "
                         "(regla dura 10).")
    members[member] = task.encode("utf-8")
    with zipfile.ZipFile(cfx, "w", zipfile.ZIP_DEFLATED) as out:
        for name, data in members.items():
            out.writestr(name, data)
    return cfx


def main() -> None:
    """Rewrite a worker harness for one kind of run."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kind", required=True, choices=sorted(DONOR))
    ap.add_argument("--project", required=True,
                    help="project on the worker carrying the task --kind names by title")
    ap.add_argument("--input", default="Results")
    ap.add_argument("--output", required=True)
    ap.add_argument("--chart", action="append", default=[],
                    help='repeatable, main first: \'SYMBOL TIMEFRAME SPREAD\'')
    ap.add_argument("--spp", action="store_true",
                    help="enable the System Parameter Permutation cross-check")
    ap.add_argument("--spp-spread", type=int, default=35,
                    help="percent up and down from each parameter (35 or 40; never 30)")
    ap.add_argument("--spp-step-pct", type=float, default=4.0,
                    help="how much one step moves a parameter, in percent; Steps is derived")
    ap.add_argument("--spp-max-tests", type=int, default=15000,
                    help="ceiling on permutations. NEVER inherit it: a donor can carry "
                         "1000000001, which is SQX's sentinel for exhaustive")
    ap.add_argument("--markets", action="store_true",
                    help="enable the additional-markets cross-check")
    a = ap.parse_args()

    charts = [f'<Chart symbol="{s.split()[0]}" timeframe="{s.split()[1]}" '
              f'spread="{s.split()[2]}" />' for s in a.chart]
    task = ungate(retarget(donor_task(a.kind), charts, (a.input, a.output)))
    task = cross_check(task, "RetestOnAdditionalMarkets", a.markets)
    if a.spp:
        task = cross_check(task, "OptProfileSysParamPermutation", True)
        task = spp(task, a.spp_spread, a.spp_step_pct, a.spp_max_tests)

    role = inputs.load()["execute"]["role"]
    cfx = write(worker_dir(role) / "user/projects" / a.project / "project.cfx", task, a.kind, role)
    print(f"{a.kind}: {a.input} -> {a.output}")
    for line in re.findall(
            r"<(?:Setup|Chart|Databanks|CrossChecks|OptProfileSysParamPermutation|"
            r"SequentialOptimization|RetestOnAdditionalMarkets|WhatToParametrize)\b[^>]*>"
            r"|<(?:Steps|MaxTests|DistributionUp|DistributionDown)>\d+"
            r"|<Recommended>\w+", task):
        print("  ", line[:130])
    print(f"-> {cfx}")


if __name__ == "__main__":
    main()
