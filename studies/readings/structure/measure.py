"""The numbers of one mother's batch: per-trade change per ablation, the inversion's mirror, the controls."""

import numpy as np
import pandas as pd

from core import sqxstats, trades as tradecalc
from engines.nulls import filter as randomfilter

STATS = tuple(randomfilter.STATISTICS)          # expectancy, sharpe — both per trade
# The stored sample each leg can be checked against: SQX's sample code and its name. A leg is
# compared with its own window only -- a build rebuild against a stored OOS result says nothing.
SAMPLES = {"build": (10, "IS"), "oos1": (20, "OOS")}


def per_trade(pnl: np.ndarray) -> dict:
    """Trade count and the two per-trade statistics the random-filter null uses.

    Args:
        pnl: Net P/L per trade, account currency.

    Returns:
        `n`, `expectancy`, `sharpe`. Never total profit: an ablation changes the trade
        count, and a total compares two sample sizes.
    """
    return {"n": int(pnl.size),
            **{s: float(randomfilter.STATISTICS[s](pnl)) for s in STATS}}


def subset_null(pool: np.ndarray, kept: np.ndarray, statistic: str, draws: int,
                seed: int) -> dict:
    """The mother against the same number of trades drawn at random from its ablation.

    `engines/nulls/filter.benchmark` asks this of a filter whose trades are a subset of the
    unfiltered list. Here they mostly are not: a strategy that holds one position at a time
    is in a trade the ablation opened when the mother's entry comes, so the lists diverge
    (2 % of twins on `Strategy 23.1.53`). The null is the same — `len(kept)` trades taken
    at random from the unfiltered list, statistics from `filter.STATISTICS` — and the
    observed value is the mother's own list rather than the twins.

    Args:
        pool: Net P/L per trade of the ablation (the strategy without the condition).
        kept: Net P/L per trade of the mother.
        statistic: A key of `filter.STATISTICS`.
        draws: Random subsets drawn.
        seed: Generator seed.

    Returns:
        `observed`, `null_mean`, `p` (share of random subsets at least as good), `draws`
        (the null, for the histogram). `p` is None when the ablation traded no more than
        the mother: the condition was not a filter, and a random subset cannot be drawn.
    """
    score = randomfilter.STATISTICS[statistic]
    observed = float(score(kept))
    if pool.size <= kept.size:
        return {"observed": observed, "null_mean": None, "p": None, "draws": None}
    rng = np.random.default_rng(seed)
    picks = rng.permuted(np.tile(np.arange(pool.size), (draws, 1)), axis=1)[:, :kept.size]
    drawn = score(pool[picks])
    return {"observed": observed, "null_mean": float(drawn.mean()),
            "p": float((1 + (drawn >= observed).sum()) / (draws + 1)), "draws": drawn}


def ablation(mother: pd.DataFrame, ablated: pd.DataFrame, cfg: dict) -> dict:
    """What deleting one condition changed, per trade.

    Args:
        mother: The identity rebuild's trades on one leg.
        ablated: The ablation's trades on the same leg.
        cfg: The study's config.

    Returns:
        Both sides' per-trade statistics, the deltas (mother minus ablation, so positive
        is what the condition added), `identical` when the two trade lists are the same
        trade for trade, the share of the mother's entries the ablation also took
        (`filter.kept_mask`), and one `subset_null` per statistic.
    """
    pm, pa = (f["Profit/Loss"].to_numpy(np.float64) for f in (mother, ablated))
    m, a = per_trade(pm), per_trade(pa)
    identical = (len(mother) == len(ablated)
                 and (mother["Open time"].to_numpy() == ablated["Open time"].to_numpy()).all()
                 and np.allclose(pm, pa))
    twins = randomfilter.kept_mask(ablated, mother).sum() / max(len(mother), 1)
    subsets = cfg["subsets"]
    return {"mother": m, "ablation": a, "identical": bool(identical), "twins": float(twins),
            "delta": {s: m[s] - a[s] for s in STATS},
            "null": {s: subset_null(pa, pm, s, subsets["draws"], subsets["seed"]) for s in STATS}}


def inversion(mother: pd.DataFrame, inverted: pd.DataFrame, point_value: float) -> dict:
    """Whether the inversion took the same trades the other way, and where the P/L went.

    Pairs are taken in order and checked, never assumed: same entry and exit instants,
    same size, opposite side. For a pair, the long's fill move is Δmid − spread and the
    short's is −Δmid − spread, so their half-difference is the move at mid and their
    half-sum is the spread — the mirror is exact at mid and the costs are what is left.

    Args:
        mother: The identity rebuild's trades on one leg.
        inverted: The inversion's trades on the same leg.
        point_value: Account currency per 1.0 of price per lot.

    Returns:
        `paired` share, `corr` of the per-trade gross, the gross at the fill for both,
        `mid` (the mother's move at mid; the inversion's is its negative), `spread`,
        `carry_mother` and `carry_inverted` (swap and commission, core.trades.cost), both
        nets and both per-trade expectancies.
    """
    n = min(len(mother), len(inverted))
    m, i = mother.iloc[:n], inverted.iloc[:n]
    same = ((m["Open time"].to_numpy() == i["Open time"].to_numpy())
            & (m["Close time"].to_numpy() == i["Close time"].to_numpy())
            & np.isclose(m["Size"].to_numpy(float), i["Size"].to_numpy(float))
            & (m["Type"].astype(str).to_numpy() != i["Type"].astype(str).to_numpy()))

    def gross(t: pd.DataFrame) -> np.ndarray:
        """Per-trade P/L from the fill prices, before swap and commission."""
        side = t["Type"].astype("object").map(tradecalc.SIDE).to_numpy(float)
        return (side * (t["Close price"] - t["Open price"]) * t["Size"]
                * point_value).to_numpy(float)

    gm, gi = gross(m), gross(i)
    return {"n_mother": len(mother), "n_inverted": len(inverted),
            "paired": float(same.sum() / max(len(mother), 1)),
            "corr": float(np.corrcoef(gm, gi)[0, 1]),
            "gross_mother": float(gm.sum()), "gross_inverted": float(gi.sum()),
            "mid": float((gm - gi).sum() / 2), "spread": float(-(gm + gi).sum() / 2),
            "carry_mother": float(tradecalc.cost(m, point_value).sum()),
            "carry_inverted": float(tradecalc.cost(i, point_value).sum()),
            "net_mother": float(mother["Profit/Loss"].sum()),
            "net_inverted": float(inverted["Profit/Loss"].sum()),
            "exp_mother": float(mother["Profit/Loss"].mean()),
            "exp_inverted": float(inverted["Profit/Loss"].mean())}


def identity(rebuilt: pd.DataFrame, mother: str, tolerance: float, leg: str) -> list[dict]:
    """The rebuilt mother's backtest on one leg against the result the mother file stored for it.

    Args:
        rebuilt: The identity rebuild's trades on the leg.
        mother: Path of the mother `.sqx` as the plan recorded it.
        tolerance: Relative net-profit gap still called the same backtest.
        leg: "build" or "oos1", which picks the stored sample of the same window.

    Returns:
        One row when the mother stored that window with trades: its trade count and net
        profit, and `match` when both agree with the rebuild. A leg with no stored
        counterpart (the mother was never tested on that window) returns no row: nothing to
        compare is not a pass.
    """
    code, name = SAMPLES[leg]
    s = sqxstats.stats(mother, "Main").get(code, {})
    if not s.get("NumberOfTrades", 0):
        return []
    net = float(rebuilt["Profit/Loss"].sum())
    return [{"sample": name, "stored_trades": int(s["NumberOfTrades"]),
             "stored_net": float(s["NetProfit"]), "trades": len(rebuilt), "net": net,
             "match": bool(s["NumberOfTrades"] == len(rebuilt)
                           and abs(s["NetProfit"] - net) <= tolerance * abs(net))}]
