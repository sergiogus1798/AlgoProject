"""Price a trade from bars the way SQX did, and prove it by reconciling against SQX's own P/L."""

import numpy as np
import pandas as pd

from engines.market.calibrate import CONVENTIONS, atr, point_value

# The ATR, the point value and the fill conventions are the null engine's own
# (engines/market/calibrate.py): until 2026-09-25 this file held a second copy of each.


def require_long_only(trades: pd.DataFrame) -> None:
    """Refuse to price a market whose trades are not all long.

    Args:
        trades: One market's trades.

    Raises:
        ValueError: A short trade is present. Every return here is log(exit / entry), which
            has the wrong sign for a short, and nothing downstream would notice. The whole
            XAUUSD corpus is long-only (92,329 trades checked), so this is an assertion about
            the data rather than a case to handle: short support is a modelling decision, not
            a sign flip, because the null's drift exposure changes with it.
    """
    kinds = set(trades["Type"].unique())
    if kinds != {"Buy"}:
        raise ValueError(f"cross-market pricing is long-only; found {sorted(kinds)}")


def unit(bars: pd.DataFrame) -> float:
    """The one constant each market's returns are divided by, so markets compare.

    Args:
        bars: One market's bars.

    Returns:
        Median ATR as a fraction of price: roughly what a typical bar moves. It is a single
        number per market, identical for the real run and every null run, so it cannot move a
        p-value — it only puts gold, the DAX and EURUSD on one axis.
    """
    return float(np.nanmedian(atr(bars) / bars["Close"].to_numpy()))


def realised(bars: pd.DataFrame, held: pd.DataFrame, convention: str) -> np.ndarray:
    """The log return of each real trade, priced from the bars rather than from SQX.

    Args:
        bars: One market's bars.
        held: What envelope.occupancy() returned.
        convention: A key of CONVENTIONS.

    Returns:
        One gross log return per trade, before cost.
    """
    enter, leave = CONVENTIONS[convention]
    a = bars[enter].to_numpy()[held["entry"].to_numpy()]
    b = bars[leave].to_numpy()[held["exit"].to_numpy()]
    return np.log(b / a)


def reconcile(trades: pd.DataFrame, bars: pd.DataFrame, held: pd.DataFrame) -> list[dict]:
    """Which fill convention reproduces SQX's own prices, and how closely.

    Args:
        trades: One market's trades, already restricted to the rows envelope kept.
        bars: That market's bars.
        held: What envelope.occupancy() returned.

    Returns:
        One row per convention with its median and worst absolute price error, best first.
        If the winner's median error is not near zero the null is priced differently from the
        real run, and its p-value measures the gap between two pricers rather than timing.
    """
    rows = []
    for name, (enter, leave) in CONVENTIONS.items():
        a = np.abs(bars[enter].to_numpy()[held["entry"].to_numpy()]
                   - trades["Open price"].to_numpy())
        b = np.abs(bars[leave].to_numpy()[held["exit"].to_numpy()]
                   - trades["Close price"].to_numpy())
        rows.append({"convention": name, "entry_median": float(np.median(a)),
                     "exit_median": float(np.median(b)),
                     "worst": float(max(a.max(), b.max()))})
    return sorted(rows, key=lambda r: r["entry_median"] + r["exit_median"])


def fill_profile(trades: pd.DataFrame, bars: pd.DataFrame, held: pd.DataFrame,
                 convention: str, tolerance: float) -> dict:
    """How the recorded fills sit against the bar opens: a constant spread, or real intrabar fills.

    Args:
        trades: One market's trades, already restricted to the rows envelope kept.
        bars: That market's bars.
        held: What envelope.occupancy() returned.
        convention: The key reconcile() chose.
        tolerance: How far from the constant offset a fill may sit and still count as having
            taken the bar's price, in units of the market's median ATR.

    Returns:
        `offset` — the median signed entry error in ATR units, which is the **spread**: one
        constant every trade pays, absorbed by the per-trade cost `backtest.setting()`
        recovers, and therefore paid by every random run too. `error` — the larger of the two
        sides' median absolute error in ATR, which is what a wrong feed or a wrong timeframe
        inflates. `at_open` — the share of entries whose own error sits within `tolerance` of
        that constant offset, i.e. that really did take their bar's price.

    🔬 The distinction is the whole point, measured 2026-09-21. A constant offset is a spread
    and reproduces perfectly; a scattered one is a price-conditional fill no null can place.
    Reading the **clock** instead — is the entry stamped on a bar boundary — answers neither:
    over 960,705 trades the 4,613 entries stamped mid-bar are priced identically to the
    956,092 stamped on it. See knowhow/export/fill-and-pricing.md.
    """
    enter, leave = CONVENTIONS[convention]
    scale = unit(bars) * float(bars["Open"].median())
    a = (trades["Open price"].to_numpy()
         - bars[enter].to_numpy()[held["entry"].to_numpy()]) / scale
    b = (trades["Close price"].to_numpy()
         - bars[leave].to_numpy()[held["exit"].to_numpy()]) / scale
    offset = float(np.median(a))
    return {"offset": offset, "exit_offset": float(np.median(b)),
            "error": max(abs(offset), abs(float(np.median(b)))),
            "at_open": float(np.mean(np.abs(a - offset) <= tolerance))}


def cost_rate(charged: np.ndarray, size: np.ndarray, open_price: pd.Series) -> float:
    """The cost SQX charged, as a fraction of price, for use inside the return.

    Args:
        charged: Per trade, the gross rebuilt from the bars minus the P/L SQX reported.
        size: Per trade, lots times point value.
        open_price: The trades' fill prices.

    Returns:
        Median round-turn cost divided by median entry price. Recovered from the trades rather
        than read from the asset file, because what matters is reproducing the simulation SQX
        already ran, not what the broker ought to charge. It is measured against the BARS,
        like the returns it is subtracted from: SQX fills the entry a spread-and-slippage
        offset above the bar open, and a cost measured from the fill prices (`core.trades.cost`)
        leaves that offset out -- 2026-09-27 that judged 8 USDJPY-family strategies with PF
        0.79-1.07 as PF 1.31-1.51 (knowhow/research/crossmarket-returns-miss-entry-offset.md).
        Swap is inside this residual for trades held overnight.
    """
    return float(np.median(charged / size) / open_price.median())


def trade_returns(fixed: dict, bars: pd.DataFrame) -> np.ndarray:
    """Net log return per real trade.

    Args:
        fixed: What backtest.setting() returned.
        bars: That market's bars.

    Returns:
        One value per trade, in the same units realised() uses, cost already subtracted. It
        lives here and not with the statistics that read it: subtracting the recovered cost
        from the priced return is a measurement, and a module that computed the numbers it
        then judged could not be cross-examined.
    """
    return realised(bars, fixed["held"], fixed["fill"]["convention"]) - fixed["cost"]
