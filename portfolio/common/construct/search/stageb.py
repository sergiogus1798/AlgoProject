"""Stage B of the funded search: one combination under three Monte Carlos, every block length, every risk."""

import itertools

import numpy as np
import pandas as pd

from portfolio.common.construct.mc import blocklen, judge, paths
from portfolio.common.construct.search import stagea, stageb_data


def risk_grid(plan: dict, cfg: dict) -> np.ndarray:
    """Every risk setting stage B reads: one level of the grid per challenge phase.

    Returns:
        float64 [C, phases], risk per trade as a fraction of the initial balance.
    """
    phases = len(judge.stage_names(plan))
    return np.array(list(itertools.product(cfg["funded"]["risk_grid"], repeat=phases)))


def flavours(data: dict, idxs: np.ndarray, cfg: dict, rng: np.random.Generator) -> list[tuple]:
    """The path sets one combination is judged on, generated one at a time.

    Returns:
        A generator of (`flavour`, `length`, `measured`, paths): D and T2 once per block
        length (the sweep and the one measured on the combination's daily P&L), T1 once.
    """
    days = stageb_data.joint(data, idxs)
    members = [data["units"][i] for i in idxs]
    horizon, n_paths = cfg["funded"]["horizon_days"], cfg["stageb"]["n_paths"]
    measured = blocklen.lengths(days, cfg["stageb"]["sweep_days"])
    for length in measured["lengths"]:
        yield "D", length, length == measured["measured"], paths.daily_blocks(
            days, horizon, n_paths, length, rng)
    yield "T1", 0, False, paths.trade_bootstrap(members, horizon, n_paths, rng)
    for length in measured["lengths"]:
        yield "T2", length, length == measured["measured"], paths.trade_blocks(
            members, horizon, n_paths, length, rng)


def evaluate(data: dict, idxs: np.ndarray, plan: dict, cfg: dict, risk: np.ndarray,
             rng: np.random.Generator) -> pd.DataFrame:
    """One combination: every Monte Carlo flavour and block length at every risk setting.

    Args:
        data: `stageb_data.prepare()` output for the stretch read.
        idxs: The combination's member rows in `data`.
        plan: A `catalog.plan()` dict.
        cfg: The construct config (`funded`, `stageb`).
        risk: float64 [C, phases], `risk_grid()`'s or the settings to read.
        rng: Source of randomness.

    Returns:
        One row per (flavour, length, setting): `flavour` (D, T1, T2), `length` (mean block or
        window in server days; 0 for T1), `measured` (that length is Politis and White's),
        `setting` (row of `risk`), `r_<phase>`, and `mc.judge.figures()`'s columns — all NaN
        where a member's smallest lot would round to zero at that setting, or the setting is
        above the open-risk cap (`stagea.capped`).
    """
    names = judge.stage_names(plan)
    floor = cfg["funded"]["min_lot"] / 2
    feasible = ((risk * plan["size"] * data["lot_unit"][idxs].min() >= floor).all(axis=1)
                & ~stagea.capped(np.array([len(idxs)]), risk, plan, cfg)[0])
    frames = []
    for flavour, length, measured, drawn in flavours(data, np.asarray(idxs), cfg, rng):
        got = judge.figures(judge.outcomes(drawn, plan, risk * plan["size"]), len(names))
        frame = pd.DataFrame({k: np.where(feasible, v, np.nan) for k, v in got.items()})
        for j, name in enumerate(names):
            frame.insert(j, f"r_{name}", risk[:, j])
        frame.insert(0, "setting", np.arange(len(risk)))
        frame.insert(0, "measured", measured)
        frame.insert(0, "length", length)
        frame.insert(0, "flavour", flavour)
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def decide(rows: pd.DataFrame) -> dict:
    """The setting a combination is read at, and by which Monte Carlo.

    Per setting the figure that counts is the lowest P(pass) over every flavour and block
    length (owner, Q18: the most pessimistic decides); the setting kept is the one where
    that figure is highest, the lower risk on a tie.

    Args:
        rows: `evaluate()` output.

    Returns:
        `p` (the deciding P(pass); NaN when no setting is feasible), `setting`, `risk`
        ({phase: r}), `by_flavour` (each flavour's own lowest P(pass) at that setting),
        `flavour`, `length` (the row that decided) and `figures` (that row).
    """
    worst = rows.groupby("setting")["p_pass"].min()
    if worst.isna().all():
        return {"p": float("nan"), "setting": -1, "risk": {}, "by_flavour": {}, "flavour": None,
                "length": None, "figures": {}}
    setting = int(worst.idxmax())
    at = rows[rows["setting"] == setting]
    row = at.loc[at["p_pass"].idxmin()]
    return {"p": float(worst[setting]), "setting": setting,
            "risk": {c[2:]: float(row[c]) for c in rows.columns if c.startswith("r_")},
            "by_flavour": at.groupby("flavour")["p_pass"].min().to_dict(),
            "flavour": row["flavour"], "length": int(row["length"]), "figures": row.to_dict()}


def stability(data: dict, idxs: np.ndarray, plan: dict, cfg: dict, risk: np.ndarray,
              rng: np.random.Generator) -> dict:
    """Whether the paths drawn are enough: the deciding figure recomputed on fresh draws.

    Args:
        risk: float64 [1, phases], the one setting whose figure is repeated.

    Returns:
        `runs`, `values` (each run's deciding P(pass)), `mean`, `spread` (largest minus
        smallest, in probability) and `unstable` (the spread exceeds `stageb.stability_tol`:
        raise `stageb.n_paths` before deciding on it).
    """
    values = [float(evaluate(data, idxs, plan, cfg, risk, rng)["p_pass"].min())
              for _ in range(cfg["stageb"]["stability_runs"])]
    spread = max(values) - min(values)
    return {"runs": len(values), "values": values, "mean": float(np.mean(values)),
            "spread": spread, "unstable": bool(spread > cfg["stageb"]["stability_tol"])}
