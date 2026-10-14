"""Step 21 for every survivor, and the batch helpers step 13 shares: the panel reading, the mothers' copies, the export, the clear."""

import shutil
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, cast

import pandas as pd

from core.study import identity
from pipeline.autopilot import call, survivors

WIDTH = 4


def reading(project: str, key: str, databank: str, mothers: pd.DataFrame) -> str:
    """Step 21: one strategy study per mother, on the databank the owner named."""
    who = survivors.about(project)
    # A mother carries her last databank's name («…(1)» after a retest); the study reads the
    # panel databank's cosecha, which knows her by its own (📓 2026-10-05, step 22, IndexError).
    spelt = identity.spelt(project, databank, list(mothers["identity"]))
    rows: Iterable[Any] = mothers.itertuples()   # namedtuples, typed as plain tuples
    names = [cast(str, spelt.get(m.identity, m.strategy)) for m in rows]
    jobs = call.window(key, project, databank, who["symbol"], names)
    # One process per mother, each writing only `estrategias/<her name>.json` (`output.member`):
    # no two share a file. Four at a time, because each loads the export's trades.
    with ThreadPoolExecutor(max_workers=min(WIDTH, max(1, len(jobs)))) as pool:
        list(pool.map(call.run, jobs))
    return f"{key} sobre {databank}: {len(jobs)} madre(s)"


def copies(mothers: pd.DataFrame, folder: Path) -> Path:
    """The mothers' `.sqx` copied out of SQX, each under her name: what a batch is made from.

    The folder is emptied first: the factories take every `.sqx` in it as a mother.
    """
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("*.sqx"):
        old.unlink()
    m: Any   # itertuples() rows are namedtuples, typed as plain tuples
    for m in mothers.itertuples():
        shutil.copy2(m.file, folder / f"{m.strategy}.sqx")
    return folder


def export(project: str, role: str, tag: str, banks: list[str]) -> None:
    """The legs' trades in one SQX start, tagged so batches never overwrite each other."""
    call.run(["-m", "sqx.export.export_retest", "--project", project, "--role", role,
              "--batch", tag, *(x for b in banks for x in ("--databank", b))])


def clear(project: str) -> None:
    """Empty the batch's input and the three legs, worker stopped: the next batch loads clean."""
    call.run(["-m", "sqx.variants.execute", "--project", project, "--clear"])
