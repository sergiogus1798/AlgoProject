"""The weight walk-forward (M8): each method held fixed and re-estimated, against equal weight."""

from typing import TypedDict, cast

import numpy as np
import pandas as pd

from engines.inference.snooping import superior
from portfolio.common.construct.mc import paths as mc_paths

from .verdict import metrics

ARMS = ("fixed", "reestimated")


class Arms(TypedDict):
    """`arms()`' result: each (method, arm)'s stitched test path, the test days, the weights and the failures."""

    paths: dict[tuple[str, str], np.ndarray]
    dates: pd.DatetimeIndex
    weights: pd.DataFrame
    failed: dict[str, str]


class _Seed(TypedDict, total=False):
    """The seed `wf.main` stamps on a finished run."""

    seed: int


class Walkforward(Arms, _Seed):
    """`wf.run()`'s result: `arms()` plus the comparison table, the states and the cuts."""

    table: pd.DataFrame
    states: dict[str, str]
    cuts: list[dict]
    members: list[str]
    meta: dict
    build: tuple[pd.Timestamp, pd.Timestamp]
    test: tuple[pd.Timestamp, pd.Timestamp]
STATES = {"fixed": "gana a pesos iguales con los pesos fijos",
          "only_reestimated": "solo gana a pesos iguales re-estimando",
          "no": "no gana a pesos iguales"}


def folds(dates: pd.DatetimeIndex, first: pd.Timestamp, lookback_years: int, step_years: int) -> list[dict]:
    """The estimation and test windows: a test window starts at `first`, then every `step_years` on 1 January.

    Args:
        dates: Every day there is, estimation and test, sorted.
        first: The first test day; every day before it is estimation only.
        lookback_years: Years before a window's start its weights are estimated on; 0 = every
            earlier day (the first estimation is then all there is before `first`).
        step_years: Years between two estimations.

    Returns:
        One dict per window with test days: `estimate_from`, `test_from`, `test_to`
        (exclusive) -- estimation is `estimate_from` <= day < `test_from`.
    """
    last = cast(pd.Timestamp, dates[-1])
    starts = cast(list[pd.Timestamp], [first] + [pd.Timestamp(year=y, month=1, day=1)
                                                  for y in range(first.year + step_years, last.year + 1, step_years)])
    ends = starts[1:] + [last + pd.Timedelta(days=1)]
    return [{"estimate_from": a - pd.DateOffset(years=lookback_years) if lookback_years else dates[0],
             "test_from": a, "test_to": b}
            for a, b in zip(starts, ends) if ((dates >= a) & (dates < b)).any()]


def arms(unit: pd.DataFrame, cuts: list[dict], methods: dict, cfg: dict) -> Arms:
    """Every method's test path, weights held from the first window and re-estimated at each.

    Args:
        unit: days x members P&L per unit of risk, no NaN, estimation and test days.
        cuts: `folds()`'s windows.
        methods: name -> weight method (`weights.REGISTRY`'s shape), `equal` among them.
        cfg: The construct config, handed to each method.

    Returns:
        `paths` ({(method, arm): [D] daily P&L on the test days stitched}; `equal` has the
        `fixed` arm only), `dates` (the D test days), `weights` (long: window, test_from,
        method, identity, weight) and `failed` ({method: why it could not be estimated} --
        such a method has no path and nothing replaces it).
    """
    test = [unit[(unit.index >= c["test_from"]) & (unit.index < c["test_to"])] for c in cuts]
    paths: dict[tuple[str, str], np.ndarray] = {}
    rows: list[dict] = []
    failed: dict[str, str] = {}
    for name, method in methods.items():
        try:
            held = [method(unit[(unit.index >= c["estimate_from"]) & (unit.index < c["test_from"])], cfg)
                    for c in cuts]
        except ValueError as error:
            failed[name] = str(error)
            continue
        rows += [{"window": n, "test_from": c["test_from"], "method": name, "identity": i, "weight": w}
                 for n, (c, got) in enumerate(zip(cuts, held)) for i, w in got.items()]
        paths[name, "fixed"] = np.concatenate([t.to_numpy() @ cast(pd.Series, pd.Series(held[0])[t.columns]).to_numpy() for t in test])
        if name != "equal":
            paths[name, "reestimated"] = np.concatenate(
                [t.to_numpy() @ cast(pd.Series, pd.Series(w)[t.columns]).to_numpy() for t, w in zip(test, held)])
    return {"paths": paths, "dates": pd.DatetimeIndex(np.concatenate([t.index for t in test])),
            "weights": pd.DataFrame(rows), "failed": failed}


def _sharpe(paths: np.ndarray) -> np.ndarray:
    """Daily Sharpe along the last axis; 0 where a path does not vary."""
    sd = paths.std(axis=-1, ddof=1)
    return np.divide(paths.mean(axis=-1), sd, out=np.zeros_like(sd), where=sd > 0)


def compare(got: Arms, cfg: dict, rng: np.random.Generator) -> pd.DataFrame:
    """Each arm's figures on the test days and its Sharpe against equal weight's, with an interval.

    The interval is the stationary bootstrap's: the test days resampled in blocks, the SAME
    days for every arm (the difference is paired), mean block by Politis and White on the
    equal-weight path. Nothing is corrected for the number of arms compared.

    Args:
        got: `arms()`'s result.
        cfg: The construct config (`wf.confidence`, `wf.bootstrap_draws`, `real.losing_year`).
        rng: Draws the resamples.

    Returns:
        One row per (method, arm): the four ranked metrics and `sharpe` (`verdict.metrics`),
        `diff` (Sharpe minus equal weight's) with `lo`, `hi`, `beats` (lo > 0); and on a
        re-estimated arm `diff_fixed`, `lo_fixed`, `hi_fixed` (against the same method held
        fixed). `block` is the mean block length used.
    """
    keys = list(got["paths"])
    stack = np.array([got["paths"][k] for k in keys])
    table = metrics.table(stack, got["dates"], cfg["real"]["losing_year"])
    block = superior.block_length(pd.DataFrame({"pnl": got["paths"]["equal", "fixed"]}))
    days = stack.shape[1]
    index = mc_paths.indices(days, days, int(cfg["wf"]["bootstrap_draws"]), block, rng)
    drawn = {k: _sharpe(p[index]) for k, p in zip(keys, stack)}
    tail = (1 - float(cfg["wf"]["confidence"])) / 2
    rows = []
    for n, (method, arm) in enumerate(keys):
        row = {"method": method, "arm": arm, **{m: float(v[n]) for m, v in table.items()}, "block": block}
        for versus, suffix in ((("equal", "fixed"), ""), ((method, "fixed"), "_fixed")):
            if versus == (method, arm) or (suffix and arm == "fixed"):
                continue
            lo, hi = np.quantile(drawn[method, arm] - drawn[versus], [tail, 1 - tail])
            row.update({f"diff{suffix}": float(_sharpe(stack[n]) - _sharpe(got["paths"][versus])),
                        f"lo{suffix}": float(lo), f"hi{suffix}": float(hi)})
        row["beats"] = bool(row.get("lo", 0.0) > 0)
        rows.append(row)
    return pd.DataFrame(rows)


def decide(table: pd.DataFrame) -> dict[str, str]:
    """Per method, a key of `STATES`: the Council's reversal condition of DECISIONS #5, read literally.

    `only_reestimated` = held fixed it does not beat equal weight and re-estimated it does.
    """
    beats = table.set_index(["method", "arm"])["beats"]
    return {m: "fixed" if bool(beats[m, "fixed"]) else "only_reestimated" if bool(beats[m, "reestimated"]) else "no"
            for m in table["method"].unique() if m != "equal"}
