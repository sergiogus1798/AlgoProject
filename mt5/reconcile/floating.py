"""Live trades' MAE and MFE rebuilt from M1 wicks (PLAN §14.2), only where the bars cover the trade."""
import numpy as np
import pandas as pd

from portfolio.common.construct.equity import excursions


def rebuild(trades: pd.DataFrame, bars: pd.DataFrame | None, point_value: float) -> pd.DataFrame:
    """Each trade's worst and best floating, or NaN where no M1 bar can say.

    Args:
        trades: Schema T, times ALREADY in the bars' clock.
        bars: M1 `High` and `Low` indexed by naive bar-open minute; None when the feed has
            no M1 in `AlgoData/bars/`.
        point_value: Account currency per 1.0 of price per lot.

    Returns:
        `mae` (≤ 0) and `mfe` (≥ 0), account currency, indexed like `trades`. NaN for a
        trade still open, one outside the bars' span, and one that opens and closes inside
        the same minute: SQX's window (entry minute to the minute before the exit,
        `knowhow/export/mae-mfe-from-m1.md`) is then empty.
    """
    out = pd.DataFrame({"mae": np.nan, "mfe": np.nan}, index=trades.index)
    if bars is None or trades.empty:
        return out
    t = bars.index.to_numpy()
    opened, closed = pd.to_datetime(trades["Open time"]), pd.to_datetime(trades["Close time"])
    a = np.searchsorted(t, opened.to_numpy(), side="right") - 1
    b = np.searchsorted(t, closed.to_numpy(), side="right") - 1
    seen = (closed.notna() & (opened >= bars.index[0])
            & (closed <= bars.index[-1] + pd.Timedelta(minutes=1)) & (b > a)).to_numpy()
    if seen.any():
        out.loc[seen] = excursions.rebuild(trades[seen], bars, point_value)
    return out
