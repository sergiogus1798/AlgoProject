"""Each trade with the spread it would really have paid, and its P/L once SQX's flat spread is swapped for it.

SQX prices on Dukascopy's bid bars and adds its declared spread to the ask side: a long pays it
on entry, a short on exit (`knowhow/export/fill-and-pricing.md`). So the spread a trade really
pays is the one standing at its entry if long, at its exit if short — the first Darwinex tick
at or after that bar's open, which is where a market order fills at DATATICK precision. Where
Darwinex has no tick near (every year before 2017), the day's reconstructed relative spread times
that hour's intraday multiplier stands in, and the trade says so.

Only the costs move: a market order's fill is the same bar open either way, so no trade appears,
disappears or changes its exit. Two versions: the spread alone swapped, and the spread plus a
slippage that follows it (half the real spread at each fill, the owner's convention). Commission
and swap stay what SQX charged.
"""

import numpy as np
import pandas as pd

from studies.data.spread import measure

DIRECTION = {"Buy": 1, "Sell": -1}


def _standing(m: pd.DataFrame, daily: pd.DataFrame, hours: pd.Series, when: pd.Series,
              price: np.ndarray, near_minutes: int) -> tuple[pd.Series, pd.Series]:
    """The spread standing at each instant: the tick found, or the modelled day times its hour."""
    ticked = measure.at(m, when, near_minutes)
    rel = daily["rel"].reindex(when.dt.normalize()).to_numpy() * hours.reindex(when.dt.hour).to_numpy()
    return ticked.fillna(pd.Series(rel * price, when.index)), ticked.notna()


def paid(trades: pd.DataFrame, m: pd.DataFrame, daily: pd.DataFrame, hours: pd.Series,
         near_minutes: int) -> pd.DataFrame:
    """The spread each trade really faced at its entry and at its exit, measured or modelled.

    Args:
        trades: `inputs.trades()`.
        m: `inputs.minutes()` of the asset's tick feed.
        daily: `verdict.reconstruct()`.
        hours: `measure.hours()`.
        near_minutes: The farthest a tick may be from the trade's instant and still be its own.

    Returns:
        Indexed like `trades`: `entry` and `exit` the spread in price at each fill, `real` the
        one the trade pays (entry for a long, exit for a short), `source` ("tick" | "modelo")
        of that one.
    """
    long = trades["Type"].astype(str).map(DIRECTION).to_numpy() > 0
    entry, entry_tick = _standing(m, daily, hours, pd.to_datetime(trades["Open time"]),
                                  trades["Open price"].to_numpy(), near_minutes)
    exit_, exit_tick = _standing(m, daily, hours, pd.to_datetime(trades["Close time"]),
                                 trades["Close price"].to_numpy(), near_minutes)
    return pd.DataFrame({"entry": entry, "exit": exit_, "real": np.where(long, entry, exit_),
                         "source": np.where(np.where(long, entry_tick, exit_tick), "tick", "modelo")},
                        trades.index)


def adjust(trades: pd.DataFrame, spread: pd.DataFrame, charged: dict, point_value: float) -> pd.Series:
    """P/L with SQX's flat spread given back and the real one taken.

    Args:
        trades: `inputs.trades()`, carrying `sample`.
        spread: `paid()`.
        charged: `inputs.charged()`, the flat spread in price per sample.
        point_value: Account currency per 1.0 of price and 1.0 lot.

    Returns:
        The adjusted P/L per trade, in account currency.
    """
    flat = trades["sample"].map(charged).astype(float)
    return trades["Profit/Loss"] + (flat - spread["real"]) * trades["Size"] * point_value


def slip(trades: pd.DataFrame, spread: pd.DataFrame, adjusted: pd.Series, slippage: dict,
         point_value: float) -> pd.Series:
    """`adjust()`'s P/L with SQX's flat slippage swapped too, for half the real spread at each fill.

    Args:
        trades: `inputs.trades()`, carrying `sample`.
        spread: `paid()`.
        adjusted: `adjust()`'s P/L.
        slippage: `inputs.slippage()`, the flat slippage in price per fill, per sample.
        point_value: Account currency per 1.0 of price and 1.0 lot.

    Returns:
        P/L at the real spread and a slippage that follows it. SQX charges its slippage on the
        entry AND on the exit (measured on gold: +0.025 over the open at entry, −0.025 at exit
        at 2.5 points); the owner's convention is half the spread, so each fill here pays half
        the spread standing at that fill.
    """
    flat = 2 * trades["sample"].map(slippage).astype(float)
    return adjusted + (flat - (spread["entry"] + spread["exit"]) / 2) * trades["Size"] * point_value


def stored(trades: pd.DataFrame, charged: dict, names: pd.Series) -> pd.DataFrame:
    """The trades as kept on disk: SQX's own, and the same ones at the real spread, side by side.

    Args:
        trades: `inputs.trades()` joined with `paid()`, carrying `adjusted` and `slipped`.
        charged: `inputs.charged()`.
        names: identity -> strategy name.

    Returns:
        One row per trade: the harvest's columns untouched (`Profit/Loss` is SQX's), then
        `strategy`, `spread SQX`, `spread real` (the one it pays), `spread entrada`, `spread
        salida` in price, `fuente` ("tick" | "modelo"), `Profit/Loss spread real` and
        `Profit/Loss spread y slippage reales`. The trades are the same in all three.
    """
    return pd.DataFrame({
        "strategy": trades["identity"].map(names).astype("category"),
        **{c: trades[c] for c in trades.columns
           if c not in ("entry", "exit", "real", "source", "adjusted", "slipped")},
        "spread SQX": trades["sample"].map(charged).astype(float),
        "spread real": trades["real"], "spread entrada": trades["entry"], "spread salida": trades["exit"],
        "fuente": trades["source"].astype("category"),
        "Profit/Loss spread real": trades["adjusted"],
        "Profit/Loss spread y slippage reales": trades["slipped"]})
