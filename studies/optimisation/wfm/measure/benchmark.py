"""The original strategy on its untouched window against holding its own asset at the same risk."""

import numpy as np
import pandas as pd

from engines.resample import draws

YEAR = 252


def daily_pnl(trades: pd.DataFrame, close: pd.Series, point_value: float) -> pd.Series:
    """Each trade marked to the asset's daily close, so a held position earns day by day.

    Args:
        trades: One strategy's trades, schema of `main.parquet`.
        close: The asset's D1 close, indexed by day.
        point_value: Money per 1.0 of price and 1.0 of size.

    Returns:
        P/L per day of `close`'s index, 0 on idle days. A trade's open days are marked at
        each close; its exit day books what is left of its `Profit/Loss`, so costs and swap
        land there and the days sum exactly to the trades. Marking only at the close date
        would hide how much of the result is the asset moving under an open position.
    """
    days = close.index
    out = np.zeros(len(days))
    price = close.to_numpy(np.float64)
    cols = ["Type", "Open time", "Open price", "Size", "Close time", "Close price", "Profit/Loss"]
    for t in trades[cols].itertuples(index=False):
        a = days.searchsorted(pd.Timestamp(t[1]).normalize())
        b = days.searchsorted(pd.Timestamp(t[4]).normalize())
        k = (1.0 if t[0] == "Buy" else -1.0) * t[3] * point_value
        marks = k * np.diff(np.concatenate([[t[2]], price[a:b]])) if b > a else np.array([])
        out[a:b] += marks
        out[min(b, len(days) - 1)] += t[6] - marks.sum()
    return pd.Series(out, index=days)


def _sharpe(r: np.ndarray) -> np.ndarray:
    """Annualised Sharpe along the last axis."""
    return r.mean(axis=-1) / r.std(axis=-1, ddof=1) * np.sqrt(YEAR)


def compare(pnl: pd.Series, close: pd.Series, capital: float, cfg: dict) -> dict:
    """Strategy against the asset held at equal volatility, with a paired block bootstrap.

    Args:
        pnl: `daily_pnl` over the window judged — `oos2`, the days nothing was chosen on.
        close: The asset's D1 close over the same days.
        capital: The account the strategy's P/L is a return on.
        cfg: `{"n_resamples", "block_days", "confidence", "seed"}`.

    Returns:
        `sharpe`, `asset_sharpe`, `difference` and its interval; `beta`, the residual's
        Sharpe (what is left once the asset's move is taken out) and its interval;
        `days`; `curves` (cumulative return of both, the asset scaled to the strategy's
        volatility) and `years` (each calendar year's return of both). Days are resampled
        in pairs, so both series keep their own dependence and their joint one.
    """
    s = (pnl / capital).to_numpy()
    g = close.pct_change().fillna(0.0).to_numpy()
    held = g * s.std() / g.std()
    beta = np.cov(s, g)[0, 1] / g.var(ddof=1)
    resid = s - beta * g
    rows = draws.stationary(cfg["n_resamples"], len(s), np.random.default_rng(cfg["seed"]),
                            cfg["block_days"])
    gap = _sharpe(s[rows]) - _sharpe(g[rows])
    left = _sharpe(s[rows] - beta * g[rows])
    tail = (1 - cfg["confidence"]) / 2 * 100
    band = lambda x: [float(np.percentile(x, tail)), float(np.percentile(x, 100 - tail))]
    frame = pd.DataFrame({"estrategia": s, "activo": held}, index=pnl.index)
    return {"sharpe": float(_sharpe(s)), "asset_sharpe": float(_sharpe(g)),
            "difference": float(_sharpe(s) - _sharpe(g)), "difference_band": band(gap),
            "beta": float(beta), "residual_sharpe": float(_sharpe(resid)),
            "residual_band": band(left), "days": len(s),
            "from": pnl.index[0].date().isoformat(), "to": pnl.index[-1].date().isoformat(),
            "curves": frame.cumsum(), "years": frame.groupby(frame.index.year).sum()}


def call(got: dict) -> str:
    """`pass` when the whole interval of the Sharpe gap is above zero, `fail` when all of it
    is below, `watch` when it holds zero: the window cannot tell the two apart."""
    low, high = got["difference_band"]
    return "pass" if low > 0 else "fail" if high < 0 else "watch"
