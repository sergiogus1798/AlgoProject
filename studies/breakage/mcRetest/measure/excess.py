"""T2 and T3: what the re-runs keep of the original's excess over the calendar-year drift."""

import numpy as np
import pandas as pd

from core import barstore
from studies.breakage.mcRetest.measure import store
from studies.breakage.mcRetest.model import tails
from studies.breakage.mcRetest.model.retention import retention
from studies.screening.analysis import tradelevel
from studies.screening.gate import inputs as gate


def context(keys: dict, asset: dict | None) -> dict | None:
    """What pricing a drift needs, read once per ingest.

    Args:
        keys: project, databank and day.
        asset: The manifest's `asset`: `feed` and `timeframe`.

    Returns:
        `bars` of the strategies' own timeframe, `span` (the asset's build segment),
        `point_value`, and `drift` — step 8's own window and variant
        (`studies/screening/gate/config.yaml`), so both steps subtract the same thing. None on
        an ingest written before 2026-10-07, which kept no dated build trades.
    """
    if not (store.root(**keys) / store.BUILD).exists():
        return None
    market = gate.market(asset["feed"])
    return {"bars": barstore.read(asset["feed"], asset["timeframe"]),
            "span": market["windows"]["IS"], "point_value": market["point_value"],
            "drift": gate.config([])["drift"]}


def original(trades: pd.DataFrame, pnl: np.ndarray, ctx: dict, tolerance: float) -> dict | None:
    """The original's build trades with dates, SQX's own P/L and the drift each collected.

    Args:
        trades: `store.load_build()` for one strategy: dated, from its harvest.
        pnl: `store.load_original_pnl()` for one task and strategy, USD: the vector the
            re-runs are compared with, chronological and undated.
        ctx: What context() returned.
        tolerance: USD two P/L of the same trade may differ by (`recon.absolute_floor`: the
            harvest rounds to the cent and the .bin truncates).

    Returns:
        `pnl`, `drift` and `opened` per trade, or None when the two lists are not the same
        trades one to one — nothing then gives a date to a P/L and neither test has data.
    """
    trades = trades.sort_values("Close time", kind="stable")
    if len(trades) != pnl.size or np.abs(trades["pnl"].to_numpy() - pnl).max() > tolerance:
        return None
    drift, _ = tradelevel.drift_term(trades, ctx["bars"], ctx["span"], ctx["drift"]["window"],
                                     ctx["drift"]["variant"], ctx["point_value"])
    return {"pnl": pnl, "drift": drift, "opened": trades["Open time"].to_numpy()}


def t2(runs: list[np.ndarray], base: dict) -> dict:
    """T2, the retouched history: approximate, because a re-run's trades have no dates.

    Args:
        runs: P/L per trade of each `ohlc` re-run, USD.
        base: What original() returned.

    Returns:
        `ret_med_aprox`, `ret_p5_aprox` and `f_pos` on each run's total P/L minus the drift
        the ORIGINAL collected (a re-run trades almost when the original did); `ret_benef`,
        the same median on the P/L alone; the measured support for that «almost» —
        `same_count_frac`, the share of runs with exactly the original's trade count, and
        `count_dev_med`, the median distance of a run's count from it as a share of it; `n`.
    """
    totals = np.array([run.sum() for run in runs])
    counts = np.array([run.size for run in runs])
    drift, size = base["drift"].sum(), base["pnl"].size
    kept = retention(totals - drift, base["pnl"].sum() - drift)
    return {"ret_med_aprox": kept["ret_med"], "ret_p5_aprox": kept["ret_p5"],
            "f_pos": kept["f_pos"],
            "ret_benef": retention(totals, base["pnl"].sum())["ret_med"],
            "same_count_frac": float((counts == size).mean()),
            "count_dev_med": float(np.median(np.abs(counts - size)) / size), "n": kept["n"]}


def t3(runs: list[np.ndarray], base: dict, start: np.datetime64, cfg: dict) -> dict:
    """T3, the starting bar: the common window, found by matching each run's tail.

    Args:
        runs: P/L per trade of each `bar` re-run, USD.
        base: What original() returned.
        start: Open of the last bar a re-run may start on; the common window is the
            original's trades opened from it on.
        cfg: The config's `fragility` block: `min_tail`, `min_matched`.

    Returns:
        `ret_med` and `ret_p5`, the dated runs' excess in the window over the original's;
        `matched_frac`, the share of runs whose tail dated them; `identical_frac`, the share
        whose tail covers the whole window (their excess there IS the original's); `distinct`,
        how many different totals the runs gave; `n`, the runs read. Both retentions are NaN
        when fewer than `min_matched` of the runs were dated or all gave one result: no data,
        never a fail.
    """
    inside = base["opened"] >= start
    excess = base["pnl"] - base["drift"]
    shared = np.array([tails.common_suffix(run, base["pnl"]) for run in runs])
    dated = shared >= cfg["min_tail"]
    got = np.array([tails.window_excess(run, tail, excess, base["drift"], inside)
                    for run, tail in zip(runs, shared) if tail >= cfg["min_tail"]])
    distinct = int(np.unique(np.round([run.sum() for run in runs], 2)).size)
    ok = dated.mean() >= cfg["min_matched"] and distinct >= 2
    kept = retention(got if ok else got[:0], excess[inside].sum())
    return {"ret_med": kept["ret_med"], "ret_p5": kept["ret_p5"],
            "matched_frac": float(dated.mean()),
            "identical_frac": float((shared >= inside.size - np.argmax(inside)).mean())
            if inside.any() else 0.0,
            "distinct": distinct, "n": len(runs)}


def _runs(keys: dict, task: str, strategy: str) -> list[np.ndarray]:
    """One task's re-runs of one strategy, each its own P/L vector in USD."""
    pnl = store.load_pnl(**keys, task=task, strategy=strategy)
    return [rows.to_numpy() for _, rows in pnl.groupby("sim", observed=True)["pnl"]]


def describe(keys: dict, strategy: str, provenance: dict, ctx: dict | None, cfg: dict) -> dict:
    """Both tests for one strategy, each absent when it cannot be measured.

    Args:
        keys: project, databank and day.
        strategy: One strategy id.
        provenance: The manifest's entries for this strategy, keyed by task.
        ctx: What context() returned, or None on an ingest that kept no dated build trades
            (before 2026-10-07).
        cfg: What inputs.config.load() returned.

    Returns:
        {"t2": t2() or None, "t3": t3() or None}: None when its task did not run, when the
        ingest has no dated build trades, or when they are not the task's original one to
        one. The common window opens `RandomizeStartingBar.MaxChange` bars — what SQX ran
        with, off the run's own provenance — after the build segment's first bar.
    """
    out = {"t2": None, "t3": None}
    if ctx is None:
        return out
    trades = store.load_build(**keys, strategy=strategy)
    for name, task in (("t2", "ohlc"), ("t3", "bar")):
        if task not in provenance:
            continue
        base = original(trades, store.load_original_pnl(**keys, task=task, strategy=strategy),
                        ctx, cfg["recon"]["absolute_floor"])
        if base is None:
            continue
        runs = _runs(keys, task, strategy)
        if name == "t2":
            out[name] = t2(runs, base)
        else:
            shift = int(provenance[task]["methods"]["RandomizeStartingBar"]["MaxChange"])
            grid = ctx["bars"].index
            start = grid[grid.searchsorted(pd.Timestamp(ctx["span"][0])) + shift]
            out[name] = t3(runs, base, start.to_datetime64(), cfg["fragility"])
    return out
