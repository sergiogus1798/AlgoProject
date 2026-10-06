"""The list step 26 verifies: each survivor's stop-grafted file, written for its agent and handed to it."""

import json
from pathlib import Path

import pandas as pd

from core import sqxfile
from pipeline.autopilot import survivors, traded
from sqx.variants import stopgrid

FILE = "finalistas.json"


def write(project: str, mothers: pd.DataFrame, out: Path) -> str:
    """Write `<run folder>/finalistas.json`, the contract with step 26.

    Args:
        project: Project name.
        mothers: `survivors.mothers` after step 25.
        out: The autopilot run's folder.

    Returns:
        How many finalists, and the mothers left out for lack of a step-24 stop, by name.
        One object per finalist: `strategy` (the grafted file's own name, «<mother>
        <variant>»), `identity` (that file's — a retest of it will carry another),
        `mother`, `sqx` (absolute), `symbol`, `timeframe`, `stop` {percentile, x}.

    Raises:
        survivors.Done: The list is empty; the file is written all the same.
    """
    picked, left = traded.stops(project, mothers)
    who = survivors.about(project)
    rows = [{"strategy": stopgrid.NAME.format(strategy=p["strategy"], variant_id=p["variant"]),
             "identity": sqxfile.identity(Path(p["sqx"])), "mother": p["strategy"],
             "sqx": p["sqx"], "symbol": who["symbol"], "timeframe": who["timeframe"],
             "stop": {"percentile": p["percentile"], "x": p["x"]}} for p in picked]
    (out / FILE).write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")
    said = f"SIN stop del paso 24, fuera: {', '.join(left)}" if left else ""
    if not rows:
        raise survivors.Done("ningún finalista para el paso 26" + (f" ({said})" if said else ""))
    return f"{len(rows)} finalista(s) en {out / FILE}" + (f"; {said}" if said else "")


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
