"""Item 4: how much of the edge is given up by entering a few bars late.

Tier 1 (`given_up`, `cost`) holds the exits where they were: right for signal and bar-count
exits. A strategy with a stop is read by tier 2 (`replayed`): every trade walked again from
the late entry with its stop recomputed (`engines.market.replay`).
"""

import numpy as np
import pandas as pd

from engines.market import reprice
from engines.market.replay import walk


def given_up(
    opens: np.ndarray, entry: np.ndarray, side: np.ndarray, delays: list[int]
) -> np.ndarray:
    """The price handed over by entering d bars after the signal.

    Args:
        opens: Open price per bar of whichever grid the delay is measured on.
        entry: Bar index of each entry on that grid.
        side: +1 long, -1 short.
        delays: How many bars late, one column each.

    Returns:
        (trades x delays), in price, signed so that a positive number is price given up.
        Exits are assumed unchanged, which is right for signal and bar-count exits and
        wrong for a stop or a target -- those move with the entry, and `replayed` is what
        handles them.
    """
    steps = np.array(delays)
    later = opens[entry[:, None] + steps[None, :]]
    return side[:, None] * (later - opens[entry][:, None])


def cost(
    handed: np.ndarray,
    size: np.ndarray,
    value: float,
    pnl: np.ndarray,
    charged: np.ndarray,
    delays: list[int],
) -> pd.DataFrame:
    """What that price is worth, and how it compares with the edge and with the costs.

    Args:
        handed: What `given_up` returned.
        size: Lots per trade.
        value: Account currency per unit of price per lot.
        pnl: Net P&L per trade as SQX reported it.
        charged: What SQX took off each trade.
        delays: The same delays, for the index.

    Returns:
        One row per delay: the mean given up in account currency, the net expectancy that
        would leave, the delay-cost ratio against gross expectancy, and the same figure as
        a multiple of what the backtest was already charged.

        ⚠️ The PDF asks for this in **spread units**. The spread is inside the fill prices
        on this install and does not appear in the `gross - net` residual
        (`knowhow/costs/where-the-spread-is.md`), so what is recoverable per trade is the whole modelled
        cost, not the spread alone. The ratio is therefore against total cost and is named
        that way; reading it as spreads would overstate the delay's severity.
    """
    money = handed * (size * value)[:, None]
    gross = (pnl + charged).mean()
    return pd.DataFrame(
        {
            "d": delays,
            "entregado": money.mean(axis=0),
            "esperanza_neta": pnl.mean() - money.mean(axis=0),
            "DCR": money.mean(axis=0) / gross,
            "veces_el_coste": money.mean(axis=0) / charged.mean(),
        }
    ).set_index("d")


def replayed(
    bars: pd.DataFrame,
    rows: pd.DataFrame,
    costs: reprice.Costs,
    delays: list[int],
    latency: bool,
) -> pd.DataFrame:
    """Tier 2: the delay cost of a strategy with a stop, every trade walked again.

    Args:
        bars: The strategy's own timeframe (`engines.market.replay.inputs.ready`).
        rows: One strategy's rows of that harvest, on one sample, with `Size`, `Profit/Loss`,
            `Open price`, `Close price` and what `walk.replay` takes.
        costs: `reprice.costs` of the segment those rows ran in.
        delays: Bars late, one row each.
        latency: False delays the entry only; True moves signal exits too.

    Returns:
        The columns of `cost`, over the trades that still exist at each delay, plus
        `descartadas` (no trade at that delay) and `desconocidas` (SQX stopped it, the new
        stop misses and its signal exit is unknown, so it runs to the strategy's longest
        trade). The base is SQX's own P/L of the same trades, so the gap is the delay's alone.
    """
    opens, grid = bars["Open"].to_numpy(), bars.index.to_numpy()
    size, side = rows["Size"].to_numpy(float), rows["side"].to_numpy(float)
    sqx = rows["Profit/Loss"].to_numpy(float)
    value = costs["point_value"]
    gross = (
        side * (rows["Close price"] - rows["Open price"]).to_numpy(float) * size * value
    )
    out = []
    for d in delays:
        w = walk.replay(bars, rows, d, latency)
        live = ~w["dropped"]
        net, _ = reprice.pnl(
            opens[w["enter"][live]],
            w["exit_raw"][live],
            grid[w["enter"][live]],
            grid[w["leave"][live]],
            side[live],
            size[live],
            costs,
        )
        handed = sqx[live].mean() - net.mean()
        out.append(
            {
                "d": d,
                "entregado": handed,
                "esperanza_neta": net.mean(),
                "DCR": handed / gross[live].mean(),
                "veces_el_coste": handed / (gross[live] - sqx[live]).mean(),
                "descartadas": float(w["dropped"].mean()),
                "desconocidas": float(w["unknown"].mean()),
            }
        )
    return pd.DataFrame(out).set_index("d")
