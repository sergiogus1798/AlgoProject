"""The maths: per trade, MAE in ATR and duration in bars; per strategy and segment, how much
of the result lives on trades that went k ATR against."""

import numpy as np
import pandas as pd

from engines.market import excursion


def per_trade(trades: pd.DataFrame, index: pd.DatetimeIndex, atr: np.ndarray,
              point_value: float) -> pd.DataFrame:
    """Every trade with its MAE in ATR, its duration in bars and what one ATR is worth to it.

    Args:
        trades: Harvest trades with `Open time`, `Close time`, `Size`, `MAE ($)`, `MFE ($)`,
            `Profit/Loss`.
        index: Bar open times of the strategy's timeframe.
        atr: `engines.market.atr.sqx` on those bars.
        point_value: Account currency per 1.0 of price and 1.0 of lot.

    Returns:
        `engines.market.excursion.measure`'s columns plus `bars` (the trade's length counted in
        bars of the strategy's timeframe, never hours: a weekend adds none) and `unit` (account
        currency one ATR is worth at this trade's size). A trade opened before the third bar
        has no ATR before it and is dropped.
    """
    kept = pd.DataFrame(trades[trades["Open time"] >= index[2]])
    out = pd.DataFrame(excursion.measure(kept, index, atr, point_value))
    held = (index.searchsorted(kept["Close time"].to_numpy(), side="right")
            - index.searchsorted(kept["Open time"].to_numpy(), side="right"))
    out["bars"] = held
    out["unit"] = kept["Size"].to_numpy() * point_value * out["atr"].to_numpy()
    return out


def one_segment(t: pd.DataFrame, cfg: dict) -> dict[str, float | str]:
    """What one strategy's trades of one segment say about its dependence on deep trades.

    Args:
        t: `per_trade`'s rows for one strategy and one segment.
        cfg: What `inputs.config` returned.

    Returns:
        Flat numbers: `n`, `net`, the duration cut (`dur_mean`, `dur_std`, `dur_cut`, `n_long`:
        trades at or past it, before crossing with the MAE), `peor_mae`, `peor_fecha`,
        `mae_p95_ganadoras`, and for each k and each scope (`prof`: MAE >= k; `anom`: MAE >= k
        and duration at or past the cut) `<scope><k>_n`, `_frac`, `_n_rec` (closed with a net
        gain), `_frac_rec`, `_pnl_rec`, `_cuota_rec` (the recovered's P&L over the net, NaN
        when the net is <= 0) and `_cortado_<slippage>`: the net had every such trade closed
        at -(k + slippage) ATR instead. That last is a bound, not a stop's backtest.
    """
    k_list, slips = cfg["depth"]["k"], cfg["depth"]["slippage"]
    mae, pnl, unit, held = (t[c].to_numpy() for c in ("mae_atr", "Profit/Loss", "unit", "bars"))
    n, net = len(t), float(pnl.sum())
    mean, std = (float(held.mean()), float(held.std(ddof=1))) if n > 1 else (np.nan, np.nan)
    cut = mean + cfg["anomaly"]["sigma"] * std
    long_ = held >= cut
    out: dict[str, float | str] = {"n": n, "net": net, "dur_mean": mean, "dur_std": std, "dur_cut": cut,
           "n_long": int(long_.sum())}
    worst = int(np.argmax(mae)) if n else 0
    out["peor_mae"] = float(mae[worst]) if n else np.nan
    out["peor_fecha"] = str(t["Open time"].iloc[worst].date()) if n else ""
    won = pnl > 0
    out["mae_p95_ganadoras"] = float(np.percentile(mae[won], 95)) if won.any() else np.nan
    for k in k_list:
        for scope, mask in (("prof", mae >= k), ("anom", (mae >= k) & long_)):
            p, hit = f"{scope}{k:g}_", mask
            rec = hit & won
            out[p + "n"], out[p + "n_rec"] = int(hit.sum()), int(rec.sum())
            out[p + "frac"] = float(hit.mean()) if n else np.nan
            out[p + "frac_rec"] = float(rec.sum() / hit.sum()) if hit.any() else np.nan
            pnl_rec = out[p + "pnl_rec"] = float(pnl[rec].sum())
            out[p + "cuota_rec"] = pnl_rec / net if net > 0 else np.nan
            for s in slips:
                out[f"{p}cortado_{s:g}"] = float(np.where(hit, -(k + s) * unit, pnl).sum())
    return out
