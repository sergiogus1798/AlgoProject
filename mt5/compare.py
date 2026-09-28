"""Pair the trades of an MT5 backtest with SQX's for the same strategy and window, and measure the gap."""
import pandas as pd


def pair(sqx: pd.DataFrame, mt5: pd.DataFrame, tolerance_min: float) -> pd.DataFrame:
    """Match each SQX trade to the nearest unmatched MT5 trade of the same side.

    Greedy in SQX's order: an MT5 trade counts once. Both frames are in the same clock
    (the caller shifts one of them first) and inside the same window.

    Args:
        sqx, mt5: Trades in SQX's export shape (Type, Open time, Open price, Close time,
            Close price, Profit/Loss).
        tolerance_min: Largest entry-time gap still called the same trade, in minutes.

    Returns:
        One row per SQX trade, with the matched MT5 row's columns suffixed _mt5 (NaN when none).
    """
    free = mt5.reset_index(drop=True).copy()
    free["taken"] = False
    rows = []
    for values in sqx.itertuples(index=False, name=None):
        row = dict(zip(sqx.columns, values))
        side = free[(free["Type"] == row["Type"]) & ~free["taken"]]
        gap = (side["Open time"] - row["Open time"]).abs()
        near = gap[gap <= pd.Timedelta(minutes=tolerance_min)]
        if len(near):
            i = near.idxmin()
            free.loc[i, "taken"] = True
            row.update({f"{c}_mt5": free.loc[i, c] for c in mt5.columns})
        rows.append(row)
    out = pd.DataFrame(rows, columns=[*sqx.columns, *(f"{c}_mt5" for c in mt5.columns)])
    return out.astype({f"{c}_mt5": mt5[c].dtype for c in mt5.columns})


def gap(pairs: pd.DataFrame, mt5: pd.DataFrame) -> dict:
    """The figures that say how faithfully MT5 reproduces SQX.

    Args:
        pairs: pair()'s output.
        mt5: Every MT5 trade in the window, matched or not.

    Returns:
        Counts, the share matched from each side, the median entry/exit time and price gaps
        of matched trades, and total P/L on each side (all trades, and matched only).
    """
    n_mt5 = len(mt5)
    hit = pairs.dropna(subset=["Open time_mt5"])
    minutes = lambda a, b: float(((hit[a] - hit[b]).abs().dt.total_seconds() / 60).median())
    return {k: None if isinstance(v, float) and v != v else v for k, v in {
        "sqx_trades": len(pairs), "mt5_trades": n_mt5, "matched": len(hit),
        "matched_of_sqx": round(len(hit) / len(pairs), 4) if len(pairs) else None,
        "matched_of_mt5": round(len(hit) / n_mt5, 4) if n_mt5 else None,
        "median_open_gap_min": minutes("Open time_mt5", "Open time"),
        "median_close_gap_min": minutes("Close time_mt5", "Close time"),
        "median_open_price_gap": float((hit["Open price_mt5"] - hit["Open price"]).abs().median()),
        "median_close_price_gap": float((hit["Close price_mt5"] - hit["Close price"]).abs().median()),
        "same_exit_share": round(float((hit["Close time_mt5"] == hit["Close time"]).mean()), 4)
        if len(hit) else None,
        "pl_sqx": round(float(pairs["Profit/Loss"].sum()), 2),
        "pl_mt5": round(float(mt5["Profit/Loss"].sum()), 2),
        "pl_sqx_matched": round(float(hit["Profit/Loss"].sum()), 2),
        "pl_mt5_matched": round(float(hit["Profit/Loss_mt5"].sum()), 2),
        "pl_corr_matched": round(float(hit["Profit/Loss"].corr(hit["Profit/Loss_mt5"])), 4)
        if len(hit) > 2 else None,
    }.items()}  # NaN is not JSON: an empty median becomes None


def window(trades: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    """Trades opened inside [start, end], dates YYYY-MM-DD, end day included."""
    t = trades["Open time"]
    return trades[(t >= pd.Timestamp(start)) & (t < pd.Timestamp(end) + pd.Timedelta(days=1))]
