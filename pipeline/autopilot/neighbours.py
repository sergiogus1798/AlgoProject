"""Step 13's T1 batch for the autopilot: wire two WFC legs, then make → retest → export trades → measure → clear."""

import time
from collections.abc import Callable
from pathlib import Path

import pandas as pd

from core import assetdata
from core.paths import DATA, databank_dir, project_dir, worker_dir
from core.phases import phase
from pipeline.autopilot import call, closing, survivors, variants
from sqx.curate import apply_verdict
from sqx.projects import crosstfload, live, stage
from sqx.variants import inputs, legs as legmod
from ui.daemon.launch import run as launcher

TAG = "neighbours"      # the trade export's batch tag: `raw/<P>/<leg>/<day>/neighbours/`


def run(project: str, role: str, mothers: pd.DataFrame, stamp: str) -> str:
    """T1 of step 14, the SQX half and its measure: every mother with her neighbours through
    the build and oos1 legs, their trades exported and priced.

    Args:
        project: The workflow's own project (hard rule 10), holding the WFC legs.
        role: Its worker.
        mothers: `strategy` and `file`, one row per survivor reaching step 13
            (`survivors.mothers`' shape).
        stamp: The autopilot run's folder name: the batch is `neighbours/<project>/<stamp>/`.

    Returns:
        One line: the batch, the seconds of each phase and what the retest did to the databanks.
        The mother rides in the batch as neighbour 0, so she and her neighbours are retested
        and priced alike. The legs are wired without their extra markets (T1 reads the main
        one); 16.5 and 23-24 wire them again before they run. The export's seconds are what
        decides whether `neighbours.n` stays where it is.

    Raises:
        SystemExit: `neighbours.legs` names a leg on a reserved segment (oos2).
    """
    who = survivors.about(project)
    legs = [leg for leg in legmod.legs() if leg["title"] in inputs.load()["neighbours"]["legs"]]
    segments = assetdata.load(who["symbol"])["segments"]
    held = [leg["title"] for leg in legs if segments[leg["segment"]].get("reserved_for")]
    if held:
        raise SystemExit(f"neighbours.legs nombra {held}: su tramo está reservado y T1 no lo mira")
    root = DATA / "neighbours" / project
    folder, work = closing.copies(mothers, root / "mothers"), root / stamp
    spent = {}

    def timed(name: str, job: Callable[[], object]) -> object:
        """Run one phase, keep and print its seconds."""
        began = time.monotonic()
        with phase(TAG, name):
            got = job()
        spent[name] = time.monotonic() - began
        print(f"T1 {name}: {spent[name]:.0f} s", flush=True)
        return got

    call.run(["-m", "core.assets", who["symbol"]])        # hard rule 5, before the legs are written
    variants.wire(project, role, markets=False)
    if not live.mine(role):       # restart route: `action=start` runs every active task
        stage.just(project_dir(project, worker_dir(role)) / "project.cfx",
                   [leg["title"] for leg in legs])
    timed("make", lambda: call.run(["-m", "sqx.variants.neighbourbatch", "--mothers",
                                    str(folder), "--out", str(work)]))
    said = timed("execute", lambda: retest(project, role, work))
    timed("export", lambda: closing.export(project, role, TAG, [leg["databank"] for leg in legs]))
    timed("measure", lambda: call.run(
        ["-m", "studies.breakage.mcRetest.neighbours.t1", "--project", project, "--work",
         str(work), "--symbol", who["symbol"], "--timeframe", who["timeframe"]]))
    closing.clear(project)
    files = len(list((work / "sqx").glob("*.sqx")))
    return (f"{len(mothers)} madre(s), {files} ficheros en {work}; "
            + ", ".join(f"{name} {seconds:.0f} s" for name, seconds in spent.items())
            + f"; {said}")


def entering(project: str, role: str) -> pd.DataFrame:
    """Who enters step 13: the mothers step 12's cut left in CrossTF, picked as
    `crosstfload.load_mothers` will copy them to what the MC Retest reads.

    Returns:
        `strategy` and `file`, one row per mother.

    Raises:
        survivors.Done: No mother is left.
    """
    folder = databank_dir(project, crosstfload.CROSSTF["output"], apply_verdict.install_of(role))
    files = [f for f in sorted(folder.glob("*.sqx")) if not crosstfload.SIBLING.search(f.stem)]
    if not files:
        raise survivors.Done(f"«{folder.name}» no tiene ninguna madre: no queda nada que seguir")
    return pd.DataFrame({"strategy": [f.stem for f in files], "file": files})


def retest(project: str, role: str, work: Path) -> str:
    """The batch through the two legs: the
    project copied aside first (hard rule 1), the copy gone only when no databank the legs do
    not write lost a file."""
    folder = project_dir(project, apply_verdict.install_of(role))
    kept, before = launcher.snapshot(folder), launcher.counts(folder)
    call.again(lambda: call.run(["-m", "sqx.variants.neighbourbatch", "--work", str(work),
                                 "--project", project]))
    own = {leg["databank"] for leg in legmod.legs()} | {legmod.source()}
    return launcher.compare(before, launcher.counts(folder), own, kept)
