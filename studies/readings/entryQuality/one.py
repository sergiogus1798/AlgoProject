"""One strategy's entry quality, returned as the contract's data: what the window paints."""

import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from core import barstore
from core.barstore import read as read_bars
from core.study import draws, output, result as envelope
from engines.market import calibrate
from studies.readings.entryQuality import contract, delay, eratio, excursion, inputs
from studies.readings.entryQuality.excursion import Walk
from studies.readings.entryQuality.contract import Reading
from studies.readings.entryQuality.inputs import Located

MODULE = "studies.readings.entryQuality"


def read(packed: Path, strategy: str, cfg: dict) -> Reading:
    """Every measurement for one strategy, with nothing judged and nothing printed.

    Args:
        packed: The `trades.parquet` an export wrote.
        strategy: Its name exactly as the export spells it.
        cfg: What `inputs.config` returned.

    Returns:
        The e-ratio curve and its band, the two delay tables, and the counts behind them.
    """
    run, e, d = cfg["run"], cfg["eratio"], cfg["delay"]
    frame = read_bars(run["feed"], run["timeframe"])
    found = inputs.located(packed, strategy, run, frame)
    keep = inputs.usable(found, e["horizon"], len(frame))

    price = found["trades"]["Open price"].to_numpy(np.float64)
    walk = excursion.paths(
        frame, found["entry"][keep], found["side"][keep], price[keep], e["horizon"]
    )
    scale = calibrate.atr(frame, run["atr"])
    normal = excursion.normalised(walk, found["atr"][keep])
    real = eratio.curve(normal)
    bands = eratio.band(frame, found, keep, scale, e)

    opens = frame["Open"].to_numpy()
    on_tf = delay.cost(
        delay.given_up(opens, found["entry"], found["side"], d["bars"]),
        found["size"],
        found["point_value"],
        found["trades"]["Profit/Loss"].to_numpy(np.float64),
        found["charged"],
        d["bars"],
    )

    minute = barstore.source(run["feed"], ["Open"])
    at_m1 = minute.index.searchsorted(found["trades"]["Open time"].to_numpy())
    on_m1 = delay.cost(
        delay.given_up(minute["Open"].to_numpy(), at_m1, found["side"], d["minutes"]),
        found["size"],
        found["point_value"],
        found["trades"]["Profit/Loss"].to_numpy(np.float64),
        found["charged"],
        d["minutes"],
    )

    hold = found["trades"]["Close time"] - found["trades"]["Open time"]
    return {
        "found": found,
        "keep": keep,
        "real": real,
        "bands": bands,
        "walk": normal,
        "on_tf": on_tf,
        "on_m1": on_m1,
        "peak": int(np.argmax(real)) + 1,
        "hold": hold.median(),
        "sides": by_side(found, normal, keep),
    }


def by_side(found: Located, normal: Walk, keep: np.ndarray) -> dict[str, np.ndarray]:
    """The e-ratio curve of the longs and of the shorts, which can hide a dead half.

    Args:
        found: What `inputs.located` returned.
        normal: What `excursion.normalised` returned.
        keep: The usable mask.

    Returns:
        {"largos": curve, "cortos": curve} for the sides that traded, each with its count
        under "n_largos" / "n_cortos". A strategy whose longs carry everything is a
        different object from one whose two halves work, and the pooled curve shows neither.
    """
    out = {}
    for name, want in (("largos", 1.0), ("cortos", -1.0)):
        mask = found["side"][keep] == want
        if mask.any():
            out[name] = eratio.curve(
                Walk(mfe=normal["mfe"][mask], mae=normal["mae"][mask])
            )
            out[f"n_{name}"] = int(mask.sum())
    return out


def records(strategy: str, found: Reading, cfg: dict) -> list[dict]:
    """The random e-ratio at every horizon, as `core.study.draws` rows.

    Args:
        strategy: Its name.
        found: What `read` returned.
        cfg: What `inputs.config` returned.

    Returns:
        One row per horizon, observed = the strategy's own e(k), the draws = the random sets'.
        No p is computed by this study; the rows let one be.
    """
    seed = cfg["eratio"]["seed"]
    return [
        draws.record(
            "entryQuality",
            "eratio",
            found["real"][k],
            found["bands"]["stacked"][:, k],
            strategy=strategy,
            horizon=k + 1,
            seed=seed,
            raw=False,
        )
        for k in range(found["real"].size)
    ]


def run(
    strategy: str, export: Path, cfg: dict, keep: list | None = None
) -> dict[str, Any]:
    """Whether one strategy's entry carries information, and what arriving late costs.

    Args:
        strategy: Its name exactly as the export spells it.
        export: The `trades.parquet` an export wrote.
        cfg: What `inputs.config` returned.
        keep: When given, the strategy's `records` are appended to it.

    Returns:
        The contract dict: two tabs, each with its reading. No overall verdict: it
        describes the entry, the exits are someone else's question.
    """
    started = time.time()
    found = read(export, strategy, cfg)
    if keep is not None:
        keep.extend(records(strategy, found, cfg))
    kept, total = int(found["keep"].sum()), int(found["keep"].size)
    return envelope.envelope(
        MODULE,
        strategy,
        output.identify(export.parent, [strategy])[strategy],
        cfg,
        started,
        [contract.eratio_tab(found, cfg), contract.delay_tab(found, cfg)],
        warnings=[
            {
                "code": "tier_1",
                "state": "info",
                "text": "El retraso supone que las salidas no se mueven. Con stop o target "
                "eso es falso, y ahí manda el simulador de replay "
                "(docs/encargos/16-replay-de-operaciones.md).",
            }
        ],
        glossary=contract.GLOSSARY,
        summary={"trades": total, "full_path": kept, "sample": cfg["run"]["sample"]},
    )
