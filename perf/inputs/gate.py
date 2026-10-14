"""The gate's levels, the monkey and `kept`, each timed on the same pinned slice of one harvest."""

import tempfile
from pathlib import Path
from typing import Any

import pandas as pd

from core.paths import harvest_dir
from perf.inputs import sample
from studies.readings.seasonality import (
    inputs as seasonality_inputs,
    many as seasonality_many,
)
from pipeline.autopilot import kept
from studies.screening.gate import (
    inputs as gate_inputs,
    level0,
    level1a,
    level1b_centred,
    level1b_data,
    level1b_onepass,
    level2,
    level3ab,
    level3c,
)


def _gate_sample(cfg: dict) -> tuple[dict, Path]:
    """The first N strategies of the pinned gate harvest, staged as the levels read them.

    Args:
        cfg: What config.load() returned; reads `sample.gate`.

    Returns:
        The gate's `data` dict (`inputs.load` then `inputs.staged`, a scratch `out` folder
        that dies with the process) and the harvest folder. N = 0 keeps the whole harvest.
    """
    project, databank, day = cfg["sample"]["gate"]["harvest"]
    folder = harvest_dir(project, databank, day)
    data: dict[str, Any] = dict(gate_inputs.load(folder))
    ids = data["metrics"].index[: cfg["sample"]["gate"]["strategies"] or None]
    data["metrics"] = data["metrics"].loc[ids]
    for key in ("trades", "equity", "missing"):
        data[key] = data[key][data[key]["identity"].isin(ids)]
    data["curve"] = data["curve"].reindex(columns=ids)
    timeframe = gate_inputs.timeframe(data["metrics"], gate_inputs.config([]), [])
    return gate_inputs.staged(
        data, cfg["sample"]["gate"]["feed"], timeframe, Path(tempfile.mkdtemp())
    ), folder


def _gate_level(cfg: dict, *modules) -> sample.Workload:
    """Stage the sample, run level 1a (which writes the per-trade table), then `modules`.

    Args:
        cfg: What config.load() returned.
        *modules: The levels to time on top of staging and level 1a; none for 1a alone.

    Returns:
        Strategies run and bytes of the harvest's trades read. A level's own cost is its
        row minus `gate.level1a`'s: both pay the staging and level 1a.
    """
    data, folder = _gate_sample(cfg)
    everyone = data["metrics"].index
    gate_cfg = gate_inputs.config([])
    level1a.run(data, everyone, gate_cfg)
    for module in modules:
        if module is level3ab:
            data["build"] = gate_inputs.build_pnl(data, everyone)
        module.run(data, everyone, gate_cfg)
    return {
        "scale": len(everyone),
        "bytes_in": sample.weight([folder / "trades.parquet"]),
    }


def gate_stage(cfg: dict) -> sample.Workload:
    """Read and stage the sample only: the part every gate target shares."""
    data, folder = _gate_sample(cfg)
    return {
        "scale": len(data["metrics"]),
        "bytes_in": sample.weight([folder / "trades.parquet"]),
    }


def gate_level0(cfg: dict) -> sample.Workload:
    """Stage the sample and run level 0 (presence, sanity, statics) over it."""
    data, folder = _gate_sample(cfg)
    level0.run(data, data["metrics"].index, gate_inputs.config([]))
    return {
        "scale": len(data["metrics"]),
        "bytes_in": sample.weight([folder / "trades.parquet"]),
    }


def gate_level1a(cfg: dict) -> sample.Workload:
    """Staging plus level 1a: R3's excess and its t, and the table every later level reads."""
    return _gate_level(cfg)


def gate_level1b(cfg: dict) -> sample.Workload:
    """Staging, 1a and the three modules of level 1b (centred, one pass, data quality)."""
    return _gate_level(cfg, level1b_centred, level1b_onepass, level1b_data)


def gate_level2(cfg: dict) -> sample.Workload:
    """Staging, 1a and level 2: every strategy repriced one bar later."""
    return _gate_level(cfg, level2)


def gate_level3ab(cfg: dict) -> sample.Workload:
    """Staging, 1a and levels 3a-3b: the resampling tests against the build."""
    return _gate_level(cfg, level3ab)


def gate_monkey(cfg: dict) -> sample.Workload:
    """Staging, 1a and level 3c: the monkey at `monkey.draws` (5,000) over the four rungs."""
    return _gate_level(cfg, level3c)


def kept_rows(cfg: dict) -> sample.Workload:
    """What step 25's save keeps for funding: the join and the oos1 curves, in memory only.

    Args:
        cfg: What config.load() returned.

    Returns:
        Strategies kept. `kept.save` is not called: it would write under the data root's
        `kept/`. The card is the harvest's names with every fact empty, which costs the same
        join as a real one.
    """
    folder = harvest_dir(*cfg["sample"]["gate"]["harvest"])
    metrics = pd.read_parquet(folder / "metrics.parquet")
    card = metrics[["strategy"]].reindex(columns=["strategy", *kept.FACTS])  # pyright: ignore[reportCallIssue]  # stub: list-select typed as Series
    equity = pd.read_parquet(folder / "equity.parquet")
    got, _ = kept.rows(card, list(card["strategy"]), equity, 1000.0)
    return {"scale": len(got), "bytes_in": sample.weight([folder / "equity.parquet"])}


def seasonality_population(cfg: dict) -> sample.Workload:
    """The calendar reading over the sample's oos1 trades: per-strategy shuffle nulls."""
    project, databank, day = cfg["sample"]["gate"]["harvest"]
    folder = harvest_dir(project, databank, day)
    study = seasonality_inputs.config([])
    trades = seasonality_inputs.oos_trades(folder)
    names = seasonality_inputs.names(folder)
    ids = sorted(trades["identity"].unique())[
        : cfg["sample"]["gate"]["strategies"] or None
    ]
    zone, warnings = seasonality_inputs.clock(cfg["sample"]["gate"]["feed"], folder)
    seasonality_many.run(
        pd.DataFrame(trades[trades["identity"].isin(ids)]), names, zone, study, warnings
    )
    return {"scale": len(ids), "bytes_in": sample.weight([folder / "trades.parquet"])}
