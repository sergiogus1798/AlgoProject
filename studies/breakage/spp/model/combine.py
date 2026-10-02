"""IS and OOS1 side by side: the six across-time metrics, the time-free ones, and what "combined" can honestly mean."""

import numpy as np
import pandas as pd

TRADING_DAYS = 252

# Panel 1: histograms across the whole permutation grid. (SQX column, Spanish label, unit).
METRICS = [("NetProfit", "Net Profit", "USD"), ("ProfitFactor", "Profit Factor", ""),
           ("ReturnDDRatio", "Retorno/Drawdown", ""), ("Drawdown", "Max Drawdown", "USD"),
           ("SharpeRatio", "Sharpe", ""), ("SortinoRatio", "Sortino", "")]

# Panel 2: only metrics that do not grow with the sample's length (never Net Profit,
# Drawdown or Ret/DD -- CONTRACT.md "Two samples, one histogram").
TIME_FREE = [("SharpeRatio", "Sharpe", ""), ("SortinoRatio", "Sortino", ""),
             ("ProfitFactor", "Profit Factor", ""), ("EdgeRatioInPips", "R / Edge ratio", "pips")]


def _ratios(net: float, gp: float, gl: float, dd: float) -> dict:
    """Profit Factor and Ret/DD rebuilt from the additive parts of a combined window."""
    return {"NetProfit": net, "Drawdown": dd,
            "ProfitFactor": gp / gl if gl else float("inf"),
            "ReturnDDRatio": net / dd if dd else float("inf")}


def real_combined(is_row: pd.Series, oos_row: pd.Series) -> dict:
    """The four additive panel-1 metrics of the real strategy, as a concatenated backtest would show.

    Args:
        is_row, oos_row: Permutation -1 (the unperturbed original) of each grid.

    Returns:
        NetProfit, ProfitFactor, Drawdown, ReturnDDRatio. NetProfit and the two gross
        figures are exact sums; Drawdown is their sum too, which is an **upper bound**: the
        true combined drawdown could be smaller if the two windows' falls do not overlap
        in time, and cannot be recovered from summary statistics alone. Sharpe and Sortino
        are not here -- SQX's own value is per window, and combining it needs the
        concatenated trades (`real_from_trades`) or is left unmarked.
    """
    net = float(is_row["NetProfit"] + oos_row["NetProfit"])
    gp = float(is_row["GrossProfit"] + oos_row["GrossProfit"])
    gl = float(is_row["GrossLoss"] + oos_row["GrossLoss"])
    dd = float(is_row["Drawdown"] + oos_row["Drawdown"])
    return _ratios(net, gp, gl, dd)


def population(is_grid: pd.DataFrame, oos_grid: pd.DataFrame) -> dict[str, np.ndarray]:
    """An approximate IS+OOS1 population for each of the six panel-1 metrics.

    Args:
        is_grid, oos_grid: `export.without_original()` grids -- every permuted tuple but
            θ0, each an independent random draw of its own window. SPP runs do not pair
            across windows (6 of ~11,600 tuples shared, `README.md`), so there is no row to
            literally concatenate; this pairs row `i` of one with row `i` of the other,
            which is what treating the two grids as independent samples means.

    Returns:
        One array per metric name, length `min(len(is_grid), len(oos_grid))`. NetProfit,
        Drawdown and ProfitFactor are recomputed from their summed components (a real total
        a concatenated backtest could show, Drawdown again an upper bound); Ret/DD is the
        ratio of those two sums, never the two ratios added. Sharpe and Sortino have no
        additive decomposition without the permutation's own trades, which this export does
        not carry, so here they are the POOLED UNION of the IS and OOS values -- a broader
        single-sample statistic, not a joint-window recomputation. Said again in the panel's
        note, since a reader who only sees the numbers cannot tell the two apart.
    """
    n = min(len(is_grid), len(oos_grid))
    a, b = is_grid.iloc[:n], oos_grid.iloc[:n]
    net = a["NetProfit"].to_numpy(float) + b["NetProfit"].to_numpy(float)
    gp = a["GrossProfit"].to_numpy(float) + b["GrossProfit"].to_numpy(float)
    gl = a["GrossLoss"].to_numpy(float) + b["GrossLoss"].to_numpy(float)
    dd = a["Drawdown"].to_numpy(float) + b["Drawdown"].to_numpy(float)
    return {"NetProfit": net, "Drawdown": dd,
            "ProfitFactor": np.divide(gp, gl, out=np.full_like(gp, np.inf), where=gl > 0),
            "ReturnDDRatio": np.divide(net, dd, out=np.full_like(net, np.inf), where=dd > 0),
            "SharpeRatio": np.concatenate([is_grid["SharpeRatio"].to_numpy(float),
                                           oos_grid["SharpeRatio"].to_numpy(float)]),
            "SortinoRatio": np.concatenate([is_grid["SortinoRatio"].to_numpy(float),
                                            oos_grid["SortinoRatio"].to_numpy(float)])}


def real_from_trades(trades: pd.DataFrame) -> dict:
    """Sharpe and Sortino of a concatenated real backtest, from its own daily equity.

    Args:
        trades: IS and OOS trades of one strategy, concatenated (any order; sorted here).

    Returns:
        {"SharpeRatio", "SortinoRatio"}, both `mean / deviation * sqrt(252)` of the daily
        P/L (flat days at zero) -- the same daily-equity basis SQX itself uses for these two
        (`studies/breakage/mcRetest/model/recon.py`), and the app's own "Sharpe total"
        (owner, 2026-09-30). Only called when both windows' trades were exported; the grid
        alone cannot give this because it holds no per-permutation trades.
    """
    by_day = trades.set_index(pd.to_datetime(trades["Close time"]))["Profit/Loss"]
    daily = by_day.groupby(by_day.index.normalize()).sum()
    daily = daily.reindex(pd.date_range(daily.index.min(), daily.index.max(), freq="D"),
                          fill_value=0.0)
    downside = float(np.sqrt((daily.clip(upper=0) ** 2).mean()))
    return {"SharpeRatio": float(daily.mean() / daily.std(ddof=1) * np.sqrt(TRADING_DAYS)),
            "SortinoRatio": (float(daily.mean() / downside * np.sqrt(TRADING_DAYS))
                             if downside else float("inf"))}
