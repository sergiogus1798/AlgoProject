"""Item 4, tier 1: how much of the edge is given up by entering a few bars late."""

import numpy as np
import pandas as pd


def given_up(opens: np.ndarray, entry: np.ndarray, side: np.ndarray,
             delays: list[int]) -> np.ndarray:
    """The price handed over by entering d bars after the signal.

    Args:
        opens: Open price per bar of whichever grid the delay is measured on.
        entry: Bar index of each entry on that grid.
        side: +1 long, -1 short.
        delays: How many bars late, one column each.

    Returns:
        (trades x delays), in price, signed so that a positive number is price given up.
        Exits are assumed unchanged, which is right for signal and bar-count exits and
        wrong for a stop or a target -- those move with the entry, and tier 2 is what
        handles them.
    """
    steps = np.array(delays)
    later = opens[entry[:, None] + steps[None, :]]
    return side[:, None] * (later - opens[entry][:, None])


def cost(handed: np.ndarray, size: np.ndarray, value: float, pnl: np.ndarray,
         charged: np.ndarray, delays: list[int]) -> pd.DataFrame:
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
        (`knowhow/09-costs.md`), so what is recoverable per trade is the whole modelled
        cost, not the spread alone. The ratio is therefore against total cost and is named
        that way; reading it as spreads would overstate the delay's severity.
    """
    money = handed * (size * value)[:, None]
    gross = (pnl + charged).mean()
    return pd.DataFrame({"d": delays, "entregado": money.mean(axis=0),
                         "esperanza_neta": pnl.mean() - money.mean(axis=0),
                         "DCR": money.mean(axis=0) / gross,
                         "veces_el_coste": money.mean(axis=0) / charged.mean()}
                        ).set_index("d")
