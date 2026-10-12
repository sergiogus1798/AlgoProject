"""The list step 26 verifies: each survivor's own file, written for its agent and handed to it."""

import json
from pathlib import Path

import pandas as pd

from core import sqxfile
from pipeline.autopilot import survivors

FILE = "finalistas.json"


def write(project: str, mothers: pd.DataFrame, out: Path) -> str:
    """Write `<run folder>/finalistas.json`, the contract with step 26.

    Args:
        project: Project name.
        mothers: `survivors.mothers` after step 25.
        out: The autopilot run's folder.

    Returns:
        How many finalists. One object per finalist, the mother that reached step 26 with no
        stop: `strategy`, `identity` (the file's), `mother` (= `strategy`), `sqx` (the
        mother's own file, absolute), `symbol`, `timeframe`.

    Raises:
        survivors.Done: The list is empty; the file is written all the same.
    """
    who = survivors.about(project)
    rows = [{"strategy": m.strategy, "identity": sqxfile.identity(Path(m.file)),
             "mother": m.strategy, "sqx": str(Path(m.file).resolve()), "symbol": who["symbol"],
             "timeframe": who["timeframe"]} for m in mothers.itertuples()]
    (out / FILE).write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")
    if not rows:
        raise survivors.Done("ningún finalista para el paso 26")
    return f"{len(rows)} finalista(s) en {out / FILE}"


def verify(project: str, params: dict, out: Path) -> str:
    """Step 26, handed to its own module with the finalists and the owner's parameters.

    Args:
        project: Project name.
        params: `start`, `end`, `model`, `firms` — every one given, none defaulted.
        out: The autopilot run's folder, holding `finalistas.json`.

    Returns:
        The step's one summary line.

    Raises:
        survivors.Done: Its own check says it cannot start; the reasons are the stop's why.
    """
    from mt5.verify import autopilot as mt5step     # step 26's agent owns it: imported late
    rows = json.loads((out / FILE).read_text(encoding="utf-8"))
    got = mt5step.check(project, rows, params)
    if not got["ok"]:
        raise survivors.Done("el paso 26 no se lanza: " + "; ".join(got["reasons"]))
    return mt5step.run(project, rows, params, out)
