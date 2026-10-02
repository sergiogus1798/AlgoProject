"""Pair the trades of an MT5 backtest with SQX's for the same strategy and window, and measure the gap."""
import numpy as np
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


def in_points(trades: pd.DataFrame, instrument: dict) -> pd.DataFrame:
    """Each trade's P&L from its price move, at ONE point value for SQX and MT5 alike.

    Args:
        trades: SQX's export shape (Type, Open price, Close price, Size, Profit/Loss).
        instrument: The asset's `tick_size` and `point_value` (USD per 1.0 of price per lot).

    Returns:
        The trades with `Profit/Loss` = points moved × tick × point value × size, and the
        account's own figure kept as `Profit/Loss USD`. Owner, 2026-09-30: compare in points —
        SQX converts a JPY pair at a fixed rate and MT5 at each day's
        (`knowhow/costs/sqx-fixed-point-value-jpy.md`), so the USD figures differ by the rate,
        not by the EA. Commission and swap are not in the price move.
    """
    side = np.where(trades["Type"].astype(str).str.startswith("Buy"), 1.0, -1.0)
    move = (trades["Close price"] - trades["Open price"]) * side
    return trades.assign(**{"Profit/Loss USD": trades["Profit/Loss"],
                            "Profit/Loss": move * instrument["point_value"] * trades["Size"]})


# A zone the IANA database lacks, as SQX and the MT5 servers spell it: New York + 7 h
# (`knowhow/export/feed-clock-timezones.md`).
OFFSET_ZONES = {"EETUS": ("America/New_York", 7)}


def to_zone(trades: pd.DataFrame, source: str, target: str) -> pd.DataFrame:
    """The same trades with both times moved from one clock zone to another, trade by trade.

    A constant hour shift is right most of the year and wrong for the weeks two zones change
    hour on different days (🔬 2026-09-30: the5ers' Asia/Jerusalem feed against the firms'
    EETUS servers — every unpaired entry of four USDJPY runs fell between the US and the
    European change, in March and late October). A time the change skips or repeats is NaT,
    kept: it pairs with nothing and is counted, never guessed.

    Args:
        trades: With `Open time` and `Close time`, naive, in `source`.
        source, target: IANA names, or a key of `OFFSET_ZONES`.

    Returns:
        A copy, naive, in `target`.
    """
    def utc(t: pd.Series, zone: str) -> pd.Series:
        """Naive times in `zone` as UTC."""
        name, hours = OFFSET_ZONES.get(zone, (zone, 0))
        local = (t - pd.Timedelta(hours=hours)).dt.tz_localize(name, ambiguous="NaT",
                                                                 nonexistent="NaT")
        return local.dt.tz_convert("UTC")

    def local(t: pd.Series, zone: str) -> pd.Series:
        """UTC times as naive ones in `zone`."""
        name, hours = OFFSET_ZONES.get(zone, (zone, 0))
        return t.dt.tz_convert(name).dt.tz_localize(None) + pd.Timedelta(hours=hours)

    out = trades.copy()
    for c in ("Open time", "Close time"):
        out[c] = local(utc(pd.to_datetime(out[c]), source), target)
    return out
