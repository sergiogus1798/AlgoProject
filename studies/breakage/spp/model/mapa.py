"""The SPP as a map: one window's floored grid, its four readings, and the two windows side by side."""

from fnmatch import fnmatch

import numpy as np
import pandas as pd

from core.surface import dedupe
from studies.breakage.spp.model import decay
from studies.breakage.spp.verdict import noise

# Row label -> SQX column. AvgProfitPerYear is NetProfit / TotalDataYears to SQX's rounding
# (max gap 0.25 USD over 340,000 permutations, measured 2026-10-07), so it is the one used.
METRICS = {"benef_anual": "AvgProfitPerYear", "sharpe": "SharpeRatio",
           "profit_factor": "ProfitFactor", "drawdown": "Drawdown"}
LOWER_IS_BETTER = {"drawdown"}


def is_fixed(name: str, patterns: list[str]) -> bool:
    """Whether a parameter is a shift: it matches one of the `grid.fixed` patterns, any case."""
    return any(fnmatch(name.lower(), p.lower()) for p in patterns)


def floored(grid: pd.DataFrame, names: list[str], cfg: dict) -> tuple[pd.DataFrame, dict]:
    """The grid every statistic of a window reads.

    Args:
        grid: `export.grid()` of one window, the mother (permutation -1) included.
        names: The parameters the SPP permuted.
        cfg: The `grid` block of `config.yaml`.

    Returns:
        Without the mother and the sentinel rows, without a row where any shift parameter
        differs from the mother's value (SQX moves shifts 0-6 from 1, a far larger change than
        the +-35 % of the rest), without exact duplicates, and without permutations under
        `min_trades` trades; plus `fijos_frac` (share the shifts removed), `excluidas_frac`
        (share of the distinct rows the trade floor removed) and `n` (rows left).
    """
    frame = dedupe.drop_sentinels(grid[grid.index != -1])
    shifts = [n for n in names if is_fixed(n, cfg["fixed"])]
    before = len(frame)
    if shifts:
        frame = frame[(frame[shifts] == grid.loc[-1, shifts]).all(axis=1)]
    fijos = 1 - len(frame) / before if before else np.nan
    frame = dedupe.distinct(frame)
    kept = frame[frame["NumberOfTrades"] >= cfg["min_trades"]]
    return kept, {"fijos_frac": float(fijos), "n": int(len(kept)),
                  "excluidas_frac": float(1 - len(kept) / len(frame)) if len(frame) else np.nan}


def reading(values: np.ndarray, real: float, lower_is_better: bool, iqr_floor: float) -> dict:
    """The mother against its grid on one metric.

    Returns:
        `real`, `median`, `iqr`; `d` = (real - median) / IQR, sign flipped for a metric where
        lower is better so that high always reads «suspiciously good»; NaN when the IQR is
        under `iqr_floor` of the larger of |median| and |real| (a flat grid, not infinity).
        `puesto` = share of the grid strictly worse than the mother.
    """
    values = values[np.isfinite(values)]
    if not values.size:
        return dict.fromkeys(("real", "median", "iqr", "d", "puesto"), np.nan)
    q1, med, q3 = np.percentile(values, [25, 50, 75])
    iqr = q3 - q1
    gap = (med - real) if lower_is_better else (real - med)
    flat = iqr <= iqr_floor * max(abs(med), abs(real))
    worse = values > real if lower_is_better else values < real
    return {"real": float(real), "median": float(med), "iqr": float(iqr),
            "d": float("nan") if flat else float(gap / iqr), "puesto": float(worse.mean())}


def window(grid: pd.DataFrame, names: list[str], cfg: dict) -> dict:
    """Everything one window says: the four readings, the tails, and the grid's own facts.

    Args:
        grid: `export.grid()` of the window, mother included.
        names: The parameters its SPP permuted.
        cfg: The parsed `config.yaml`.

    Returns:
        `metrics` (row label -> `reading` plus `s`, `p10`, `p5` on benef_anual and `m_dd` on
        drawdown), `n`, `excluidas_frac`, `fijos_frac`, `frac_vecinos_rentables`, `years`,
        `sobresale` (today's noise call on Sharpe, annotation only) and `frame`.
    """
    frame, info = floored(grid, names, cfg["grid"])
    mother = grid.loc[-1]
    out = {}
    for label, col in METRICS.items():
        values = frame[col].to_numpy(float)
        out[label] = reading(values, float(mother[col]), label in LOWER_IS_BETTER,
                             cfg["grid"]["iqr_floor"])
    benef, dd = frame["AvgProfitPerYear"].to_numpy(float), frame["Drawdown"].to_numpy(float)
    if benef.size:
        p10, p5 = np.percentile(benef, [10, 5])
        real = out["benef_anual"]["real"]
        out["benef_anual"] |= {"s": out["benef_anual"]["median"] / real if real > 0 else np.nan,
                               "p10": float(p10), "p5": float(p5)}
        out["drawdown"]["m_dd"] = (float(np.percentile(dd, 95)) / out["drawdown"]["real"]
                                   if out["drawdown"]["real"] > 0 else np.nan)
    sobresale = None
    if info["n"] >= cfg["grid"]["min_noise_n"]:
        sobresale = noise.noise_check(frame, "SharpeRatio", cfg["verdict"]["margin"])
    return {"metrics": out, **info, "years": float(mother["TotalDataYears"]), "frame": frame,
            "frac_vecinos_rentables": float((frame["NetProfit"] > 0).mean()) if len(frame) else np.nan,
            "sobresale": sobresale}


def across(build: dict, oos: dict, cfg: dict) -> dict:
    """The two windows' Sharpe distributions compared, never paired.

    Returns:
        `r_s` = median(oos1)/median(build), only when the build median reaches the
        `criteria.is_floor`; `z_decay` = the median shift over its expected noise,
        sqrt(1/T_build + 1/T_oos1); `a` = Vargha-Delaney's A of oos1 over build.
    """
    b, o = build["metrics"]["sharpe"], oos["metrics"]["sharpe"]
    if not (build["n"] and oos["n"]):
        return dict.fromkeys(("r_s", "z_decay", "a"), np.nan)
    noise_sd = np.sqrt(1 / build["years"] + 1 / oos["years"])
    return {"r_s": o["median"] / b["median"] if b["median"] >= cfg["criteria"]["is_floor"]["SharpeRatio"]
            else np.nan,
            "z_decay": float((o["median"] - b["median"]) / noise_sd),
            "a": decay.superiority(build["frame"]["SharpeRatio"].to_numpy(float),
                                   oos["frame"]["SharpeRatio"].to_numpy(float))}
