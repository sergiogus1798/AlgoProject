"""Behavioural fingerprint — descriptive only: does the strategy do the same thing everywhere?
Compared against the base asset (gold), never against chance; see verdict/significance.py
for that."""

import numpy as np
import pandas as pd
from scipy import stats

from core import trades as tradeio
from studies.transfer.crossmarket.mechanics import pricing

BINS = 44          # enough shape to read, few enough that each bar is still a wide target


def holding_ks(held_a: pd.DataFrame, held_b: pd.DataFrame) -> dict:
    """Two-sample KS test comparing holding-time distributions.

    Args:
        held_a: One market's held["hold"] source, from envelope.occupancy().
        held_b: Another market's, normally the base asset's.

    Returns:
        Keys statistic and p. A market whose holds have a wildly different shape from the
        base asset's is doing something else, not one edge working twice.
    """
    result = stats.ks_2samp(held_a["hold"], held_b["hold"])
    return {"statistic": float(result.statistic), "p": float(result.pvalue)}


def overlay(a: np.ndarray, b: np.ndarray, label: str, unit: str) -> dict:
    """Two samples binned on one shared axis, ready to be drawn over each other.

    Args:
        a: This market's values.
        b: The base asset's values.
        label: What the quantity is called on screen.
        unit: Its unit, for the axis.

    Returns:
        Shared edges and one count array per series, as **shares** rather than counts, so two
        markets with different trade counts are comparable — the whole point of the overlay is
        the shape, not the height. The axis is clipped at the 99th percentile of the two
        together: a single 400-bar hold otherwise squeezes the other 900 trades into one bar.
    """
    both = np.concatenate([a[np.isfinite(a)], b[np.isfinite(b)]])
    lo, hi = float(np.nanmin(both)), float(np.nanpercentile(both, 99))
    hi = hi if hi > lo else lo + 1.0
    edges = np.linspace(lo, hi, BINS + 1)
    share = [np.histogram(np.clip(x[np.isfinite(x)], lo, hi), bins=edges)[0] for x in (a, b)]
    return {"label": label, "unit": unit, "lo": lo, "hi": hi,
            "market": (share[0] / max(share[0].sum(), 1)).tolist(),
            "base": (share[1] / max(share[1].sum(), 1)).tolist()}


def excursion_profile(aligned: pd.DataFrame, bars: pd.DataFrame, held: pd.DataFrame,
                      point_value: float) -> dict:
    """MAE/MFE normalised by entry-bar ATR, so markets of different volatility compare.

    Args:
        aligned: One market's trades, already restricted to the rows envelope kept.
        bars: That market's bars.
        held: What envelope.occupancy() returned, same rows as aligned.
        point_value: What pricing.point_value() measured for this market.

    Returns:
        Mean and 25th/75th percentile of MAE and MFE in units of entry-bar ATR, plus the
        normalised series themselves for the overlaid histograms.
    """
    excursions = tradeio.excursions(aligned, point_value)
    entry_atr = pricing.atr(bars)[held["entry"].to_numpy()]
    out = {}
    for name in ("mae", "mfe"):
        normalised = excursions[name].to_numpy() / entry_atr
        out[name] = {"mean": float(np.nanmean(normalised)),
                     "p25": float(np.nanpercentile(normalised, 25)),
                     "p75": float(np.nanpercentile(normalised, 75)),
                     "values": normalised}
    return out


def capture_ratio(trades: pd.DataFrame, point_value: float, drop_zero: bool) -> dict:
    """Fraction of the favourable excursion each trade converted into realised move.

    Args:
        trades: One market's trades, already restricted to the rows envelope kept.
        point_value: What pricing.point_value() measured for this market.
        drop_zero: Exclude trades whose MFE is zero rather than letting them divide by it.

    Returns:
        Keys mean, median and dropped. It measures the **exit**, not the entry, which is why
        it lives here and not in exposure.py. A trade that never moved favourably has an
        undefined capture ratio, not an infinite one: 7 of 844 silver trades are such, and
        keeping them makes the mean +/-inf while the median silently ignores the problem.
    """
    mfe = tradeio.excursions(trades, point_value)["mfe"]
    keep = mfe > 0 if drop_zero else np.ones(len(mfe), dtype=bool)
    ratio = ((trades["Close price"] - trades["Open price"])[keep] / mfe[keep]).to_numpy()
    return {"mean": float(ratio.mean()), "median": float(np.median(ratio)),
            "dropped": int((~keep).sum())}


def return_shape(returns: np.ndarray) -> dict:
    """Skew, kurtosis and tail ratio of the real per-trade returns.

    Args:
        returns: What pricing.trade_returns() returned.

    Returns:
        Keys skew, kurtosis and tail_ratio (|p95| / |p5|). A fat left tail on only one market
        is a warning, not a fixable defect of the test.
    """
    return {"skew": float(stats.skew(returns)), "kurtosis": float(stats.kurtosis(returns)),
            "tail_ratio": float(abs(np.percentile(returns, 95)) / abs(np.percentile(returns, 5)))}


def histograms(base: dict, market: dict, base_ex: dict, market_ex: dict) -> list[dict]:
    """The four overlaid distributions: duration, return, and both excursions.

    Args:
        base: backtest.setting()'s return for the base asset, plus its "bars".
        market: The same, for the additional market.
        base_ex, market_ex: What excursion_profile() returned for each.

    Returns:
        One overlay() per quantity, in reading order. Duration first because it is the one
        that says "this is not the same strategy here"; the excursions last because they are
        the ones that need the ATR normalisation explained beside them.
    """
    pairs = [(market["held"]["hold"].to_numpy(), base["held"]["hold"].to_numpy(),
              "Duración de la operación", "velas"),
             (pricing.trade_returns(market, market["bars"]),
              pricing.trade_returns(base, base["bars"]),
              "Retorno neto por operación", "log"),
             (market_ex["mae"]["values"], base_ex["mae"]["values"],
              "MAE — cuánto llegó a perder", "× ATR de entrada"),
             (market_ex["mfe"]["values"], base_ex["mfe"]["values"],
              "MFE — cuánto llegó a ganar", "× ATR de entrada")]
    return [overlay(a, b, label, unit) for a, b, label, unit in pairs]


def fingerprint(strategy: str, base: dict, market: dict, drop_zero: bool) -> dict:
    """Assemble every fingerprint piece for one market against the base asset.

    Args:
        strategy: Strategy name, carried through for the panel's table.
        base: backtest.setting()'s return for the base asset (gold), plus its "bars".
        market: The same, for the additional market.
        drop_zero: exposure.drop_zero_mfe, for the capture ratio.

    Returns:
        Keys strategy, holding_ks, excursion, shape, capture and hists. The excursion series
        themselves are dropped from what is returned — they are megabytes, and the histograms
        already carry their shape.
    """
    held_returns = pricing.trade_returns(market, market["bars"])
    ex = excursion_profile(market["aligned"], market["bars"], market["held"],
                           market["point_value"])
    base_ex = excursion_profile(base["aligned"], base["bars"], base["held"],
                                base["point_value"])
    return {"strategy": strategy, "holding_ks": holding_ks(market["held"], base["held"]),
            "excursion": {k: {n: v for n, v in s.items() if n != "values"}
                          for k, s in ex.items()},
            "shape": return_shape(held_returns),
            "capture": capture_ratio(market["aligned"], market["point_value"], drop_zero),
            "hists": histograms(base, market, base_ex, ex)}
