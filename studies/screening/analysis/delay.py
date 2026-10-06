"""What a strategy's per-trade excess keeps when its entry, its exit or both fill one bar off."""

import numpy as np
import pandas as pd

from engines.market import reprice
from studies.screening.analysis import tradelevel

# Bars the entry and the exit move by. A registry because the config picks from it.
SHIFTS = {"E+1": (1, 0), "S+1": (0, 1), "ES+1": (1, 1), "E-1": (-1, 0)}


def excess(trades: pd.DataFrame, bars: pd.DataFrame, span: tuple[str, str], costs: reprice.Costs,
           drift: dict, shift: tuple[int, int] = (0, 0)) -> np.ndarray:
    """Each trade's excess over the market's drift with its fills moved, as level 1a prices it.

    Args:
        trades: `open_time`, `close_time` (on the bar grid), `side` (+1 / -1) and `lots`.
        bars: The strategies' own timeframe, the whole file, indexed by open time.
        span: (first, last) of the trades' sample.
        costs: As reprice.costs() returns it, for that sample's segment.
        drift: The gate's `drift` block: `window` and `variant`.
        shift: Bars the entry and the exit move by; (0, 0) is the original trade.

    Returns:
        reprice.pnl at the opens of the moved bars, original lots, minus tradelevel.drift_term
        over the moved hold. An entry is never moved past its exit: a one-bar trade entered a
        bar late opens and closes on the same open and pays only its costs. NaN where the
        moved entry leaves the span and the drift term has no window for it.
    """
    leave = bars.index.get_indexer(trades["close_time"]) + shift[1]
    enter = np.minimum(bars.index.get_indexer(trades["open_time"]) + shift[0], leave)
    when, side, lots = bars.index.to_numpy(), trades["side"].to_numpy(), trades["lots"].to_numpy()
    pnl, _ = reprice.pnl(reprice.fills(bars, enter), reprice.fills(bars, leave), when[enter],
                         when[leave], side, lots, costs)
    moved = pd.DataFrame({"Open time": when[enter], "Close time": when[leave],
                          "Type": np.where(side < 0, "Sell", "Buy"), "Size": lots})
    return pnl - tradelevel.drift_term(moved, bars, span, drift["window"], drift["variant"],
                                       costs["point_value"])[0]


def measure(trades: pd.DataFrame, bars: pd.DataFrame, span: tuple[str, str],
            costs: reprice.Costs, drift: dict, variants: list[str]) -> pd.DataFrame:
    """Retention and paired t of every delay variant, per strategy.

    Args:
        trades: excess()'s columns plus `identity` and `excess`, the original trade's; in time
            order within each identity.
        bars, span, costs: As excess() takes them.
        drift: The gate's `drift` block; `se_skew_kurt` picks the t, as in level 1a.
        variants: Keys of `SHIFTS`, in the order a tie for the worst is broken.

    Returns:
        One row per identity and variant, variants in the order given: `identity`, `variant`,
        `ret` (mean moved excess over mean original excess; NaN when the original mean is not
        positive), `t_delta` (mean / sd x sqrt(n) of original minus moved, trade by trade) and
        `t`, level 1a's t on the moved excess. A trade the variant cannot price is left out of
        both of its means.
    """
    t = tradelevel.t_skew_kurt if drift["se_skew_kurt"] else tradelevel.t
    rows = []
    for name in variants:
        moved = excess(trades, bars, span, costs, drift, SHIFTS[name])
        pair = trades.assign(moved=moved, delta=trades["excess"] - moved).dropna(subset=["delta"])
        mean = pair.groupby("identity", sort=False)[["excess", "moved"]].mean()
        rows.append(pd.DataFrame({
            "variant": name, "ret": (mean["moved"] / mean["excess"]).where(mean["excess"] > 0),
            "t_delta": tradelevel.t(pair, "delta")["iid"], "t": t(pair, "moved")["ar1"]}))
    return pd.concat(rows).rename_axis("identity").reset_index()


def worst(table: pd.DataFrame) -> pd.DataFrame:
    """The variant each strategy is judged on: the one that keeps least.

    Args:
        table: What measure() returned.

    Returns:
        Indexed by identity, measure()'s row of the smallest `ret` — so `t_delta` is that same
        variant's; a tie goes to the variant listed first. Strategies with no `ret` are absent.
    """
    return (table.dropna(subset=["ret"]).sort_values("ret", kind="stable")
            .drop_duplicates("identity").set_index("identity"))
