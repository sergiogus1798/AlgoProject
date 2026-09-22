#!/usr/bin/env python3
"""Build a worker's one-task retest harness from a donor task that is known to have run."""

import argparse
import re
import subprocess
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.paths import DATA, WORKERS, worker_dir
from sqx.variants import inputs

TASK = "Retest-Task1.xml"
# Donor tasks, by what they are for. These are the owner's own XAUUSD settings, frozen:
# copying one is how a harness inherits a configuration that demonstrably works, instead of
# being hand-assembled and silently missing an element (knowhow/03-driving-sqx.md).
DONOR = {"spp_is": "Retest-Task13.xml", "spp_oos": "Retest-Task14.xml",
         "retest": "Retest-Task1.xml"}
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
    cfx = sorted((DATA / "donors").glob("*/project.cfx"))[-1]
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


def spp(task: str, spread: int, steps: int, keep: int = 0) -> str:
    """Set the permutation range and resolution of the SPP cross-check.

    Args:
        task: Task XML.
        spread: Percent up and down from each parameter's value.
        steps: How many values per parameter SQX walks.
        keep: `PctToPass` -- the share of permutations that must be profitable for the
            strategy to be accepted. **0 for a study.** The donor runs 80 because it is
            filtering a population; a parameter study needs the profile of every strategy
            it asked about, including the ones that fail, and a strategy rejected here
            never reaches the output databank at all.

    Returns:
        The XML. `steps` is the only real lever on how many simulations a run performs --
        integer parameters collapse duplicate values afterwards, so the permutation count
        that comes back is always lower than steps x parameters, and by how much depends on
        the strategy. Measure it; do not predict it.
    """
    # ⚠️ Scoped to the element, not applied to the file. `DistributionUp`, `Steps` and
    # friends are generic names that several cross-checks use, and this task carries five
    # of them; a first-match substitution silently retunes the Monte Carlo instead.
    block = re.search(r"<SequentialOptimization\b.*?</SequentialOptimization>", task, re.S)
    inner = block.group(0)
    for tag, value in (("DistributionUp", spread), ("DistributionDown", spread),
                       ("Steps", steps), ("PctToPass", keep)):
        inner = re.sub(rf"<{tag}>\d+</{tag}>", f"<{tag}>{value}</{tag}>", inner, 1)
    return task[:block.start()] + inner + task[block.end():]


def write(project: str, task: str, role: str) -> Path:
    """Replace the harness project's single task, on disk.

    Args:
        project: Project name on the worker.
        task: The finished task XML.
        role: Worker role that owns the install.

    Returns:
        The project.cfx that was rewritten.

    Raises:
        SystemExit: The install is running. SQX rewrites a project.cfx on save and on exit,
            so editing one an instance holds loses the change in silence -- hard rule 4.
    """
    cfx = worker_dir(role) / "user/projects" / project / "project.cfx"
    listening = subprocess.run(["ss", "-ltn"], capture_output=True, text=True).stdout
    if f':{WORKERS[role]["port"]} ' in listening:
        raise SystemExit(f"{role} esta levantado: paralo antes de reescribir {project}")
    members = {n: z.read(n) for z in [zipfile.ZipFile(cfx)] for n in z.namelist()}
    members[TASK] = task.encode("utf-8")
    with zipfile.ZipFile(cfx, "w", zipfile.ZIP_DEFLATED) as out:
        for name, data in members.items():
            out.writestr(name, data)
    return cfx


def main() -> None:
    """Rewrite a worker harness for one kind of run."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kind", required=True, choices=sorted(DONOR))
    ap.add_argument("--project", required=True, help="harness project on the worker")
    ap.add_argument("--input", default="Results")
    ap.add_argument("--output", required=True)
    ap.add_argument("--chart", action="append", default=[],
                    help='repeatable, main first: \'SYMBOL TIMEFRAME SPREAD\'')
    ap.add_argument("--spp-steps", type=int, help="enable SPP with this many steps")
    ap.add_argument("--spp-spread", type=int, default=35, help="percent up and down")
    ap.add_argument("--spp-keep", type=int, default=0,
                    help="PctToPass: share of permutations that must be profitable. 0 for "
                         "a study -- the donor's 80 rejects the strategy and its profile")
    ap.add_argument("--markets", action="store_true",
                    help="enable the additional-markets cross-check")
    a = ap.parse_args()

    charts = [f'<Chart symbol="{s.split()[0]}" timeframe="{s.split()[1]}" '
              f'spread="{s.split()[2]}" />' for s in a.chart]
    task = ungate(retarget(donor_task(a.kind), charts, (a.input, a.output)))
    task = cross_check(task, "SequentialOptimization", bool(a.spp_steps))
    task = cross_check(task, "RetestOnAdditionalMarkets", a.markets)
    if a.spp_steps:
        task = spp(task, a.spp_spread, a.spp_steps, a.spp_keep)

    cfx = write(a.project, task, inputs.load()["execute"]["role"])
    print(f"{a.kind}: {a.input} -> {a.output}")
    for line in re.findall(r"<(?:Setup|Chart|Databanks|CrossChecks|SequentialOptimization|"
                           r"RetestOnAdditionalMarkets)\b[^>]*>|<Steps>\d+|<Distribution\w+>\d+"
                           r"|<PctToPass>\d+",
                           task):
        print("  ", line[:130])
    print(f"-> {cfx}")


if __name__ == "__main__":
    main()
