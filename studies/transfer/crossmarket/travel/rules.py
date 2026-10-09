"""P3-P9 of the travel test: every number is read from one strategy's tensor, nothing is simulated again."""

import math

import numpy as np
import pandas as pd

from studies.transfer.crossmarket.travel import stat


def windows(cal: pd.DataFrame) -> dict[str, np.ndarray]:
    """The cell masks every rule reads: the whole span (V0 + V1 + V2, never `after`) and each window."""
    return {"all": (cal["window"] != "after").to_numpy(),
            **{w: (cal["window"] == w).to_numpy() for w in ("V0", "V1", "V2")}}


def on_net(one: dict) -> dict:
    """The tensor read on NET R (`real_net`, `null_net`); itself when it has none or judges net."""
    return {**one, "real": one.get("real_net", one["real"]), "null": one.get("null_net", one["null"])}


def per_market(one: dict, whole: np.ndarray) -> pd.DataFrame:
    """z, p, e and the real trades of each market over the whole span.

    z and p are on the judged quantity (travel.judge_on); `e` is always NET R per trade.

    Args:
        one: A strategy's tensor, as `tensor.build()` returns it.
        whole: The cells of the span.

    Returns:
        One row per market: `z`, `p` (§3.8's z_j), `e` (§4.1, R per trade above the random runs;
        NaN with no trade) and `trades`.
    """
    rows = []
    for j, name in enumerate(one["markets"]):
        got, n = stat.joint(one, [j], whole), float(stat.total(one["trades"], [j], whole))
        net = stat.joint(on_net(one), [j], whole)
        rows.append({"market": name, "z": got["z"], "p": got["p"],
                     "e": (net["real"] - net["mean"]) / n if n > 0 else np.nan, "trades": n})
    return pd.DataFrame(rows)


def minus_market(one: dict, whole: np.ndarray) -> tuple[float, str]:
    """P5: the lowest z over every market list with one left out, and the market left out for it.

    Returns:
        (z_minus_market, minus_market); NaN and "" with fewer than two markets or no z.
    """
    every = range(len(one["markets"]))
    z = [stat.joint(one, [k for k in every if k != j], whole)["z"] for j in every]
    if len(z) < 2 or np.isnan(z).all():
        return np.nan, ""
    j = int(np.nanargmin(z))
    return float(z[j]), one["markets"][j]


def breadth(one: dict, whole: np.ndarray) -> tuple[float, float]:
    """P6, §4.2: in how many markets the real run beats the median of the random ones, against chance.

    Returns:
        (p_breadth, breadth_count). p = (1 + runs with C_b >= C_real) / (runs + 1), each run
        read as if it were the real one. A market with no trade never beats its median (0 is not
        above 0), which is how an absent market counts against.
    """
    every = range(len(one["markets"]))
    real = np.array([stat.total(one["real"], [j], whole) for j in every])
    null = np.stack([stat.total(one["null"], [j], whole) for j in every], 1)
    median = np.nanmedian(null, 0)
    seen, runs = int((real > median).sum()), (null > median).sum(1)
    return (1 + int((runs >= seen).sum())) / (len(runs) + 1), float(seen)


def tau_half(e: np.ndarray, trades: np.ndarray, e_principal: float, min_trades: int) -> float:
    """P7, §4.3: the ceil(M/2)-th largest of e_j / e_principal.

    Args:
        e: The markets' e, R per trade.
        trades: Their real trades.
        e_principal: The main's e on oos1; not above 0 or NaN gives no tau.
        min_trades: travel.min_trades_market; a market below it is -inf (absent ones included).

    Returns:
        The tau, -inf when fewer than half of the markets stand, NaN without a usable denominator.
    """
    if not e_principal > 0:
        return np.nan
    tau = np.where((trades >= min_trades) & np.isfinite(e), e / e_principal, -np.inf)
    return float(np.sort(tau)[::-1][math.ceil(len(tau) / 2) - 1])


def worse(z: np.ndarray, trades: np.ndarray, min_trades: int, worse_z: float) -> int:
    """P8, §4.4: markets where the strategy does clearly worse than random (z <= worse_z); a
    market under `min_trades` is not counted."""
    return int(((trades >= min_trades) & (z <= worse_z)).sum())


def _pool(rows: list, floor: int) -> list[list]:
    """Years in order, each group closed once it holds `floor` trades; the tail joins the last group."""
    groups, now = [], []
    for row in rows:
        now.append(row)
        if sum(r[1] for r in now) >= floor:
            groups, now = groups + [now], []
    if now:
        groups = groups[:-1] + [groups[-1] + now] if groups else [now]
    return groups


def degradation(one: dict, cal: pd.DataFrame, whole: np.ndarray, deg: dict) -> dict:
    """P9, §7.3: the slope of the edge per trade over the years, against the random runs' own slopes.

    Args:
        one: A strategy's tensor.
        cal: `cells.table()`.
        whole: The cells of the span.
        deg: travel.degradation (`min_trades_year`, `min_years`).

    Returns:
        `beta`, `z_beta`, `e_end` (the projected edge at the last year with data), `e_end_ratio`
        (over the mean edge) and `d_y`, the series [{years, trades, d}]; the four numbers are NaN
        under `min_years` groups after pooling. A year is the calendar year of the close; a
        pooled group sits at its trades-weighted mean year.
    """
    year = cal["start"].dt.year.to_numpy()
    rows = []
    for y in np.unique(year[whole]):
        cells = whole & (year == y)
        real = stat.total(one["real"], cells=cells)
        if not np.isnan(real):
            rows.append((y, stat.total(one["trades"], cells=cells), real,
                         stat.total(one["null"], cells=cells)))
    out = {"beta": np.nan, "z_beta": np.nan, "e_end": np.nan, "e_end_ratio": np.nan, "d_y": []}
    groups = _pool(rows, deg["min_trades_year"]) if rows else []
    if len(groups) < deg["min_years"]:
        return out
    n = np.array([sum(r[1] for r in g) for g in groups])
    real = np.array([sum(r[2] for r in g) for g in groups])
    null = np.stack([sum(r[3] for r in g) for g in groups], 1)
    t = np.array([np.average([r[0] for r in g], weights=[r[1] for r in g]) for g in groups])
    d, d_null = (real - null.mean(0)) / n, (null - null.mean(0)) / n
    centred = t - np.average(t, weights=n)
    slope = lambda v: (n * centred * v).sum(-1) / (n * centred ** 2).sum()
    beta, spread = slope(d), slope(d_null)
    mean = np.average(d, weights=n)
    end = mean + beta * (rows[-1][0] - np.average(t, weights=n))
    return {"beta": float(beta), "z_beta": float((beta - spread.mean()) / spread.std(ddof=1))
            if spread.std(ddof=1) > 0 else np.nan, "draws": (float(beta), spread),
            "e_end": float(end), "e_end_ratio": float(end / mean) if mean else np.nan,
            "d_y": [{"years": [int(r[0]) for r in g], "trades": int(m), "d": float(v)}
                    for g, m, v in zip(groups, n, d)]}


def evaluate(one: dict, cal: pd.DataFrame, cfg: dict, e_principal: float = np.nan) -> dict:
    """Every column of P3-P9 for one strategy, from its tensor.

    Args:
        one: A strategy's tensor over the valid markets.
        cal: `cells.table()`.
        cfg: The `travel` section of config.yaml.
        e_principal: The main's e (R per trade, oos1); NaN until the step-8 monkey supplies it.

    Returns:
        `verdict` (the contract's columns for P3-P9 and `trades`), `markets` (`per_market`), `d_y` and `beta`
        (z_beta's observed slope and the random runs' slopes, None under `min_years`).
    """
    mask = windows(cal)
    got = {k: stat.joint(one, cells=mask[k]) for k in mask}
    rows = per_market(one, mask["all"])
    z_minus, who = minus_market(one, mask["all"])
    p_breadth, count = breadth(one, mask["all"])
    trades, min_n = rows["trades"].to_numpy(), cfg["min_trades_market"]
    n_worse = worse(rows["z"].to_numpy(), trades, min_n, cfg["worse_z"])
    slope = degradation(on_net(one), cal, mask["all"], cfg["degradation"])     # e_end, beta: net
    judged = degradation(one, cal, mask["all"], cfg["degradation"])    # z_beta: judged
    verdict = {"z_conj": got["all"]["z"], "p_conj": got["all"]["p"], "z_conj_v2": got["V2"]["z"],
               "z_conj_v0": got["V0"]["z"], "z_conj_v1": got["V1"]["z"],
               "z_minus_market": z_minus, "minus_market": who,
               "p_breadth": p_breadth, "breadth_count": count,
               "tau_half": tau_half(rows["e"].to_numpy(), trades, e_principal, min_n),
               "e_principal": e_principal, "worse": n_worse, "worse_fraction": n_worse / len(rows),
               "z_beta": judged["z_beta"], "e_end": slope["e_end"], "beta": slope["beta"],
               "e_end_ratio": slope["e_end_ratio"], "trades": float(trades.sum())}
    return {"verdict": verdict, "markets": rows, "d_y": slope["d_y"],
            "beta": judged.get("draws")}
