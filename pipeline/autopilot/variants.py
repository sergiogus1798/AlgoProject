"""Step 16.5 for the autopilot: wire the three WFC legs, then make → execute → equity → collect → every variant's trades → clear per mother, then the mothers' trades and each batch's parameter map."""

import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from core.datapaths import tmp_dir, variants_dir
from core.paths import ROOT, project_dir, report_dir, worker_dir
from core.phases import phase
from pipeline.autopilot import call
from sqx.projects import live, registry
from sqx.variants import legs as legmod


def _py(*args: str) -> None:
    """One module run as the skill runs it; its failure ends the step with its own words."""
    with phase(args[0].rsplit(".", 1)[-1] + (".clear" if "--clear" in args else "")):
        got = subprocess.run([sys.executable, "-m", *args], cwd=ROOT, capture_output=True,
                             text=True)
    if got.returncode:
        raise SystemExit(f"{args[0]}: {(got.stderr or got.stdout).strip()[-1500:]}")


def briefs(project: str) -> list[Path]:
    """The design briefs step 16's SPP report wrote, one per mother, from its newest day."""
    days = sorted(report_dir(project, "SPP_IS", "x").parent.glob("*/spp"))
    return sorted(days[-1].glob("design_brief_*.json")) if days else []


def wire(project: str, role: str, markets: bool = True) -> None:
    """Configure the three WFC legs (`sqx.projects.wfc`): on the file with SQX closed, on a copy
    pushed to it with a live session (hard rule 4). `markets` off leaves the legs on the main
    market alone, which is all a pilot reads."""
    less = [] if markets else ["--no-markets"]
    row = next(r for r in reversed(registry.rows()) if r["name"] == project)
    held = project_dir(project, worker_dir(role)) / "project.cfx"
    if not live.mine(role):
        _py("sqx.projects.wfc", row["symbol"], "--cfx", str(held), "--timeframe", row["timeframe"],
            *less)
        return
    with tempfile.TemporaryDirectory(dir=tmp_dir()) as tmp:
        staged = Path(tmp) / "project.cfx"
        shutil.copy2(held, staged)
        _py("sqx.projects.wfc", row["symbol"], "--cfx", str(staged), "--timeframe",
            row["timeframe"], *less)
        live.push(role, project, staged, held)


def run(project: str, role: str, only: set[str] | None = None) -> str:
    """The whole step; one line per mother with its seconds.

    `only`: the survivors of step 16 by name; a brief of a mother its judge cut is skipped.
    The mother's name is the brief's own `strategy`, never its file stem: the stem swaps dots
    for dashes, and a batch filed under it is one 17-20 cannot find (🔬 2026-10-02).

    The legs' active flags matter only to the restart route: live, `livexec.run` starts them
    by the projectXML it sends.
    """
    # Live, every mother's pilot runs first and without the legs' extra markets: it reads the
    # trade count on the main market, and the 11 others were 81 s of its 86 (🔬 2026-10-05,
    # same counts on 300 of 300). The restart route is left as it was: the pilot inside `make`.
    apart = live.mine(role)
    wire(project, role, markets=not apart)
    todo = []
    for brief in briefs(project):
        strategy = json.loads(brief.read_text(encoding="utf-8"))["strategy"]
        if only is None or strategy in only:
            todo.append((strategy, variants_dir(project, strategy), ["--brief", str(brief)]))

    def make(work: Path, brief: list[str]) -> float:
        """One mother's design, pilot and batch of `.sqx`; its seconds."""
        began = time.monotonic()
        call.again(lambda: _py("sqx.variants.make", *brief, "--project", project, "--out",
                               str(work)))
        return time.monotonic() - began

    spent = {strategy: make(work, brief) for strategy, work, brief in todo} if apart else {}
    if apart and todo:
        wire(project, role)
    done, works = [], []
    for strategy, work, brief in todo:
        began = time.monotonic() - (spent[strategy] if apart else make(work, brief))
        call.again(lambda: _py("sqx.variants.execute", "--work", str(work), "--project",
                               project))
        _py("sqx.variants.equity", "--work", str(work))
        _py("sqx.variants.collect", "--work", str(work))
        # Every variant's trades, the three legs and every market, before the databanks empty:
        # the shared excess of steps 14, 16.5 and 17 is computed from them (encargo 48 E/F).
        # `closing.export` is this same command; closing imports this module, so not from there.
        _py("sqx.export.export_retest", "--project", project, "--role", role, "--batch",
            "variants", *(x for leg in legmod.legs() for x in ("--databank", leg["databank"])))
        _py("sqx.variants.varianttrades", "--work", str(work), "--project", project)
        _py("sqx.variants.execute", "--work", str(work), "--project", project, "--clear")
        done.append(f"{strategy} {time.monotonic() - began:.0f} s")
        works.append(work)
    if not done:
        raise SystemExit(f"{project}: el paso 16 no dejó ningún design brief")
    _py("sqx.variants.mothertrades", *(x for work in works for x in ("--work", str(work))))
    # The map (encargo 48 N): no rule, cuts nothing, reads build and oos1 only. Last, with SQX
    # idle and every batch already on disk, so a map that fails loses nothing of the factory.
    for work in works:
        _py("studies.optimisation.cloud.report", "--work", str(work))
    return "; ".join(done)
