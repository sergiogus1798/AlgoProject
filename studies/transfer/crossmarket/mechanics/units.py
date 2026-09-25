"""One number, in every unit a reader needs: bps, per cent, ATR units and dollars.

A log return of 0.00042 is unreadable, and that is the unit every statistic in this study is
computed in. Nothing here changes a number — the maths stays in log space, where subtracting
two windows is legitimate — it only says the same number four more ways."""

import numpy as np

# The cumulative dollar figure is what the owner reads first: "the timing put $16,800 of the
# $40,000 this strategy made" is a sentence; "+0.00042" is not.
LABELS = {"bps": "bps", "pct": "%", "r": "R (ATR)", "usd": "$ / operación",
          "usd_total": "$ acumulado"}


def dollars(logret: np.ndarray, fixed: dict) -> np.ndarray:
    """A per-trade log return converted to account currency, trade by trade.

    Args:
        logret: One log return per trade, same order as fixed["held"].
        fixed: What backtest.setting() returned.

    Returns:
        USD per trade. Price times log return is the price move to first order, which is
        exact to a part in 10,000 at the sizes these returns have; the alternative —
        expm1() — would claim a precision the rest of the pricing does not have.
    """
    entry_px = fixed["enter_px"][fixed["held"]["entry"].to_numpy()]
    return logret * entry_px * fixed["size"]


def scaled(value: float, fixed: dict) -> dict:
    """One mean log return, in every unit the panel prints.

    Args:
        value: A mean log return per trade.
        fixed: What backtest.setting() returned, for the market's ATR scale.

    Returns:
        Keys bps, pct and r. `r` divides by the market's median ATR as a fraction of price —
        the same constant backtest.run() divides mean_r by, so the two are on one axis.
    """
    return {"bps": value * 1e4, "pct": float(np.expm1(value)) * 100.0,
            "r": value / fixed["scale"]}


def spread(values: np.ndarray, fixed: dict) -> dict:
    """A whole per-trade series, in every unit, with its cumulative dollar total.

    Args:
        values: One log return per trade.
        fixed: What backtest.setting() returned.

    Returns:
        What scaled() returns for the mean, plus usd (the mean trade in dollars) and
        usd_total (the sum over every trade) — the figure that says how much money the
        quantity being measured actually moved over the whole sample.
    """
    usd = dollars(values, fixed)
    return {**scaled(float(values.mean()), fixed), "usd": float(usd.mean()),
            "usd_total": float(usd.sum())}
