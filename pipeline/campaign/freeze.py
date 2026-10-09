"""Freeze a finished workflow's strategies in the archive — finalists AND their mothers — and copy the run-stamped outputs."""

import shutil
import subprocess
import sys
from pathlib import Path

from core import sqxfile
from core.datapaths import variants_dir
from core.paths import DATA, ROOT

BIG = 300 * 2**20
SMALL = 2 * 2**20       # a file over this (pairs.csv, bar parquets) stays where it is


def _archive(cell: dict, identity: str, sqx: str | Path, note: str) -> tuple[str | None, str]:
    """One `core.archive archive` call: the version folder, or None with the error's tail."""
    done = subprocess.run(
        [sys.executable, "-m", "core.archive", "archive", "--project", cell["project"],
         "--databank", "Results", "--identity", identity, "--step", "25",
         "--family", cell["template"], "--sqx", str(sqx), "--note", note],
        cwd=ROOT, capture_output=True, text=True)
    if done.returncode:
        return None, done.stderr.strip()[-400:]
    return done.stdout.strip().splitlines()[-1], ""


def _size(path: Path) -> int:
    """Bytes under a folder."""
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def _copy(src: Path, dst: Path, skipped: list[dict]) -> None:
    """Copy a run-stamped output folder whole, or record why it was not."""
    if not src.is_dir():
        skipped.append({"path": str(src), "reason": "no existe"})
    elif _size(src) > BIG:
        skipped.append({"path": str(src), "reason": f"{_size(src) >> 20} MB, más de {BIG >> 20}: se queda en su sitio"})
    else:
        shutil.copytree(src, dst)


def _copy_small(src: Path, dst: Path, skipped: list[dict]) -> None:
    """Copy a folder without its files over `SMALL`, recording each one left."""
    left = [f for f in src.rglob("*") if f.is_file() and f.stat().st_size > SMALL]
    shutil.copytree(src, dst, ignore=lambda d, names: [n for n in names if Path(d, n) in left or n == "sqx"])   # sqx/: the variants' own files
    skipped.extend({"path": str(f), "reason": f"{f.stat().st_size >> 20} MB: se queda en su sitio"} for f in left)


def freeze(cell: dict, finalists: list[dict], folder: Path, run: Path) -> tuple[list[dict], list[dict]]:
    """Archive each distinct mother and finalist, link the finalists, copy what the archive cannot pair.

    The studies of steps 8-22 are signed with the MOTHER's identity, so the mother is archived too
    (its .sqx is the one `atrCalculator/<P>/mothers/` holds) and each finalist records both versions.
    Steps 16.5-18.5 (`strategyPermutations/<P>/<mother>/`) and 19-20 (`reports/<P>/WFM`, another identity
    per databank) cannot be paired by identity: they are copied into `madres/` and `WFM/`.

    Args:
        cell: The ledger row, with `project`, `template`.
        finalists: `finalistas.json`'s rows.
        folder: The workflow's folder.
        run: The autopilot run folder; its name is the stamp of steps 23-24's outputs.

    Returns:
        (finalists with `archive`, `mother_identity`, `mother_archive`; what could not be kept).
    """
    note = f"campaña {folder.name}"
    skipped, mothers = [], {}
    (folder / "estrategias").mkdir()
    for f in finalists:
        atr = Path(f["sqx"]).parents[3]                       # atrCalculator/<P>
        if f["mother"] not in mothers:
            sqx = atr / "mothers" / f"{f['mother']}.sqx"
            ident = sqxfile.identity(sqx) if sqx.exists() else None
            ver, err = _archive(cell, ident, sqx, note) if ident else (None, f"falta {sqx}")
            mothers[f["mother"]] = (ident, ver)
            if err:
                skipped.append({"path": f["mother"], "reason": f"madre sin archivar: {err}"})
        f["mother_identity"], f["mother_archive"] = mothers[f["mother"]]
        f["archive"], err = _archive(cell, f["identity"], f["sqx"], note)
        if err:
            skipped.append({"path": f["strategy"], "reason": f"final sin archivar: {err}"})
        else:
            (folder / "estrategias" / f["strategy"]).symlink_to(f["archive"])
    for mother in mothers:                     # steps 16.5-18.5 (wfc, cscv, marketSurfaces) live here
        _copy_small(variants_dir(cell["project"], mother), folder / "madres" / mother, skipped)
        skipped.append({"path": f"{variants_dir(cell['project'], mother)}/sqx", "reason": "los .sqx de las variantes del paso 16.5; la final ya está archivada"})
    if finalists:
        _copy_small(DATA / "reports" / cell["project"] / "WFM", folder / "WFM", skipped)   # steps 19-20, signed with the WFM identity
        atr = Path(finalists[0]["sqx"]).parents[3]
        _copy(atr / run.name, folder / "atrCalculator", skipped)
        _copy(atr.parents[1] / "structural" / atr.name / run.name, folder / "structural", skipped)
        skipped.append({"path": str(atr / "mothers"), "reason": "copias de las madres (50 MB): la madre archivada ya lleva su .sqx"})
    return finalists, skipped
