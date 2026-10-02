"""The context block of a cell: drift, volatility clustering and cost against the bar's ATR."""

import numpy as np
import pandas as pd

from engines.regimes import regime
from studies.research.marketProfile import inputs

ATR_PERIOD = 20
KAUFMAN_DAYS = 20


def efficiency(close: pd.Series, window: int) -> pd.Series:
    """Kaufman's efficiency ratio: the net move over the path walked, 1 for a straight run.

    The same formula as studies/readings/conditionalMap/regime.efficiency, copied because a
    study never imports another and that one lags the series a day for a trade's entry.
    """
    net = (close - close.shift(window)).abs()
    path = close.diff().abs().rolling(window).sum()
    return (net / path).replace([np.inf, -np.inf], np.nan)


def block(bars: pd.DataFrame, asset: dict) -> dict:
    """What says whether a timeframe can be traded at all; it proposes nothing.

    Args:
        bars: The cell's build-segment bars.
        asset: What core.assetdata.load() returned.

    Returns:
        Yearly drift of the log price, the autocorrelation of absolute returns (lag 1 and
        mean of lags 1-20), the mean round-trip cost over the mean ATR of the timeframe, and
        the mean daily Kaufman efficiency.
    """
    r = np.diff(np.log(bars["Close"].to_numpy()))
    years = (bars.index[-1] - bars.index[0]).days / 365.25
    a = np.abs(r) - np.abs(r).mean()
    acf = [a[k:] @ a[:-k] / (a @ a) for k in range(1, 21)]
    atr = regime.atr(bars, {"atr_period": ATR_PERIOD})["vol"].mean()
    paid = inputs.cost(asset, bars["Open"].to_numpy()).mean()
    daily = regime.daily(bars)["Close"]
    return {"drift_per_year": r.sum() / years, "abs_acf_1": acf[0], "abs_acf_1_20": np.mean(acf),
            "cost": paid, "atr": atr, "cost_over_atr": paid / atr,
            "kaufman_daily": efficiency(daily, KAUFMAN_DAYS).mean()}
