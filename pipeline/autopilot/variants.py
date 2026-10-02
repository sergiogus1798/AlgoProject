"""Step 16.5 for the autopilot: wire the three WFC legs, then make → execute → equity → collect → clear per mother."""

import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from core.datapaths import tmp_dir, variants_dir
from core.paths import ROOT, project_dir, report_dir, worker_dir
from sqx.projects import live, registry


def _py(*args: str) -> None:
    """One module run as the skill runs it; its failure ends the step with its own words."""
    got = subprocess.run([sys.executable, "-m", *args], cwd=ROOT, capture_output=True, text=True)
    if got.returncode:
        raise SystemExit(f"{args[0]}: {(got.stderr or got.stdout).strip()[-1500:]}")


def briefs(project: str) -> list[Path]:
    """The design briefs step 16's SPP report wrote, one per mother, from its newest day."""
    days = sorted(report_dir(project, "SPP_IS", "x").parent.glob("*/spp"))
    return sorted(days[-1].glob("design_brief_*.json")) if days else []


def wire(project: str, role: str) -> None:
    """Configure the three WFC legs (`sqx.projects.wfc`): on the file with SQX closed, on a copy
    pushed to it with a live session (hard rule 4)."""
    row = next(r for r in reversed(registry.rows()) if r["name"] == project)
    held = project_dir(project, worker_dir(role)) / "project.cfx"
    if not live.mine(role):
        _py("sqx.projects.wfc", row["symbol"], "--cfx", str(held), "--timeframe", row["timeframe"])
        return
    with tempfile.TemporaryDirectory(dir=tmp_dir()) as tmp:
        staged = Path(tmp) / "project.cfx"
        shutil.copy2(held, staged)
        _py("sqx.projects.wfc", row["symbol"], "--cfx", str(staged), "--timeframe", row["timeframe"])
        live.push(role, project, staged, held)


def run(project: str, role: str) -> str:
    """The whole step; one line per mother with its seconds.

    The legs' active flags matter only to the restart route: live, `livexec.run` starts them
    by the projectXML it sends.
    """
    wire(project, role)
    done = []
    for brief in briefs(project):
        strategy = brief.stem.removeprefix("design_brief_")
        work, began = variants_dir(project, strategy), time.monotonic()
        _py("sqx.variants.make", "--brief", str(brief), "--project", project, "--out", str(work))
        _py("sqx.variants.execute", "--work", str(work), "--project", project)
        _py("sqx.variants.equity", "--work", str(work))
        _py("sqx.variants.collect", "--work", str(work))
        _py("sqx.variants.execute", "--work", str(work), "--project", project, "--clear")
        done.append(f"{strategy} {time.monotonic() - began:.0f} s")
    if not done:
        raise SystemExit(f"{project}: el paso 16 no dejó ningún design brief")
    return "; ".join(done)
