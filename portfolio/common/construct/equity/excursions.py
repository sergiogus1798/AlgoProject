"""Per-trade MAE/MFE rebuilt from M1 wicks, and the check that licenses the rebuild (§14.2)."""

import numpy as np
import pandas as pd


def _locate(times: np.ndarray, bar_times: np.ndarray) -> np.ndarray:
    """Index of the bar that contains each time: the last bar open at or before it."""
    return np.searchsorted(bar_times, times, side="right") - 1


def rebuild(trades: pd.DataFrame, bars: pd.DataFrame, point_value: float) -> pd.DataFrame:
    """Each trade's worst and best floating excursion.

    The window is the entry minute up to (not including) the exit minute — the exit fills
    at that bar's open and its realised Profit/Loss is booked there, not floating
    (`knowhow/export/mae-mfe-from-m1.md`). A long's worst price in a minute is its `Low`,
    best is `High`; a short's are swapped.

    Args:
        trades: One strategy's trades (schema T).
        bars: M1 bars with High, Low, indexed by naive bar-open minute.
        point_value: Account currency per 1.0 of price per lot.

    Returns:
        DataFrame indexed like `trades`: `mae` (≤ 0), `mfe` (≥ 0), account currency.
    """
    bar_times = bars.index.to_numpy()
    low = bars["Low"].to_numpy(np.float64)
    high = bars["High"].to_numpy(np.float64)
    open_idx = _locate(trades["Open time"].to_numpy(), bar_times)
    close_idx = _locate(trades["Close time"].to_numpy(), bar_times)
    side = np.where(trades["Type"].astype(object) == "Buy", 1.0, -1.0)
    size = trades["Size"].to_numpy(np.float64)
    open_price = trades["Open price"].to_numpy(np.float64)

    mae = np.empty(len(trades))
    mfe = np.empty(len(trades))
    for i, (a, b, s) in enumerate(zip(open_idx, close_idx, side)):
        worst = low[a:b].min() if s > 0 else high[a:b].max()
        best = high[a:b].max() if s > 0 else low[a:b].min()
        mae[i] = min(0.0, s * (worst - open_price[i])) * size[i] * point_value
        mfe[i] = max(0.0, s * (best - open_price[i])) * size[i] * point_value

    return pd.DataFrame({"mae": mae, "mfe": mfe}, index=trades.index)


def licence(trades: pd.DataFrame, rebuilt: pd.DataFrame, tolerance: float,
            min_share: float) -> dict:
    """Whether the M1 rebuild may stand in for SQX's own `MAE ($)`/`MFE ($)` columns.

    Args:
        trades: One strategy's trades, with `MAE ($)` and `MFE ($)`.
        rebuilt: `rebuild()` output, aligned to `trades`.
        tolerance: Account currency; a trade counts as exact within this.
        min_share: Minimum share of exact trades required to license the rebuild.

    Returns:
        `n`, `mae_exact`, `mfe_exact` (shares in [0, 1]), `mae_median_gap`, `mfe_median_gap`,
        `licensed` (bool, both shares at or above `min_share`).
    """
    mae_gap = rebuilt["mae"].to_numpy() - trades["MAE ($)"].to_numpy()
    mfe_gap = rebuilt["mfe"].to_numpy() - trades["MFE ($)"].to_numpy()
    mae_exact = float((np.abs(mae_gap) <= tolerance).mean())
    mfe_exact = float((np.abs(mfe_gap) <= tolerance).mean())
    return {"n": len(trades), "mae_exact": mae_exact, "mfe_exact": mfe_exact,
            "mae_median_gap": float(np.median(np.abs(mae_gap))),
            "mfe_median_gap": float(np.median(np.abs(mfe_gap))),
            "licensed": mae_exact >= min_share and mfe_exact >= min_share}
