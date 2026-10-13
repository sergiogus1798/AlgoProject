"""One strategy's week: live trades paired with the SQX backtest's, and every gap as a number — no pass bar."""
import numpy as np
import pandas as pd

from mt5 import compare
from mt5.reconcile import floating, week as weeks
from mt5.verify import judge as clocks

SQX = ["Ticket", "Type", "Open time", "Open price", "Size", "Close time", "Close price",
       "Profit/Loss"]
LIVE = ["Type", "Open time", "Open price", "Size", "Close time", "Close price", "Profit/Loss"]


def _shaped(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """The frame with exactly `columns` (a missing one NaN), times as datetimes and numbers as
    floats, so an empty side pairs like a full one."""
    out = frame.reindex(columns=columns).reset_index(drop=True)
    if "Ticket" in columns and out["Ticket"].isna().all():
        out["Ticket"] = np.arange(1, len(out) + 1)
    for c in columns:
        out[c] = (pd.to_datetime(out[c]) if c.endswith("time") else out[c].astype(object)
                  if c == "Type" else out[c].astype(float))
    return out


def _points(frame: pd.DataFrame, instrument: dict) -> pd.DataFrame:
    """`compare.in_points`, plus `points`: the price move in the asset's ticks, free of size."""
    out = compare.in_points(frame, instrument)
    return out.assign(points=out["Profit/Loss"] / (instrument["point_value"] * out["Size"])
                      / instrument["tick_size"])


def reconcile(sqx: pd.DataFrame, live: pd.DataFrame, week: str, timeframe: str,
              instrument: dict, zones: tuple[str, str], bars: pd.DataFrame | None,
              cfg: dict) -> dict:
    """Pair one strategy's SQX backtest with what its EA really did, and measure the gaps.

    Args:
        sqx: The backtest's trades (schema T, feed clock), the warm-up stretch included.
        live: The EA's trades of the week (`live.trades`, server clock), open ones included.
        week: "YYYY-Www": both sides are cut to trades opened inside it, server clock.
        timeframe: For the entry tolerance, counted in bars.
        instrument: The asset's `tick_size` and `point_value`.
        zones: (SQX feed's zone, the server's).
        bars: The feed's M1 `High`/`Low` in the feed's clock, or None.
        cfg: `pairing.entry_tolerance_bars`, `clock.max_offset_h`.

    Returns:
        {"pairs": one row per paired trade, "sqx_only", "live_only": the trades with no twin,
        "summary": the week's figures}. Points are price moves in ticks (live − SQX); the
        currency figures put SQX's booked P&L at the LIVE trade's size. MAE and MFE are
        rebuilt for BOTH sides on the same M1 bars at the asset's one point value — SQX's
        own `MAE ($)` is priced at its fixed conversion rate and would read the rate as a
        gap (`knowhow/mt5/reconcile-mae-both-sides-rebuilt.md`). Nothing here passes or fails.
    """
    tolerance = cfg["pairing"]["entry_tolerance_bars"] * clocks.MINUTES[timeframe]
    live = weeks.cut(_shaped(live, LIVE), week)
    in_feed = compare.to_zone(live, zones[1], zones[0])
    live = _points(live, instrument).join(floating.rebuild(in_feed, bars,
                                                           instrument["point_value"]))
    live["row"] = np.arange(len(live), dtype=float)
    sqx = _shaped(sqx, SQX)
    zoned = compare.to_zone(sqx, *zones)
    # MAE/MFE only for the trades the week can keep: opened inside it once the clock shift
    # (at most max_offset_h) is applied, plus a day of margin. The rest are cut below anyway.
    start, end = weeks.bounds(week)
    margin = pd.Timedelta(hours=cfg["clock"]["max_offset_h"], days=1)
    near = ((zoned["Open time"] >= start - margin) & (zoned["Open time"] < end + margin)).to_numpy()
    sqx = _points(zoned, instrument).join(
        floating.rebuild(sqx[near], bars, instrument["point_value"]))
    hours = clocks.clock(sqx, live, tolerance, cfg["clock"]["max_offset_h"])
    sqx = weeks.cut(clocks.shifted(sqx, hours), week)
    both = compare.pair(sqx, live, tolerance).astype(sqx.dtypes.to_dict())   # an empty side keeps its types
    hit = both.dropna(subset=["Open time_mt5"])
    scale = hit["Size_mt5"] / hit["Size"]
    side = np.where(hit["Type"].astype(str).str.startswith("Buy"), 1.0, -1.0)
    pairs = pd.DataFrame({
        "ticket_sqx": hit["Ticket"].astype(int), "type": hit["Type"],
        "open_sqx": hit["Open time"], "open_live": hit["Open time_mt5"],
        "entry_gap_min": (hit["Open time_mt5"] - hit["Open time"]).dt.total_seconds() / 60,
        "price_sqx": hit["Open price"], "price_live": hit["Open price_mt5"],
        "entry_gap_pts": (hit["Open price_mt5"] - hit["Open price"]) / instrument["tick_size"],
        # the same gap signed by what it cost: + is a worse fill live than in the backtest
        "entry_slip_pts": (hit["Open price_mt5"] - hit["Open price"]) * side
        / instrument["tick_size"],
        "close_gap_min": (hit["Close time_mt5"] - hit["Close time"]).dt.total_seconds() / 60,
        "pnl_pts_sqx": hit["points"], "pnl_pts_live": hit["points_mt5"],
        "pnl_gap_pts": hit["points_mt5"] - hit["points"],
        "size_live": hit["Size_mt5"],
        "pnl_cur_sqx": hit["Profit/Loss USD"] * scale, "pnl_cur_live": hit["Profit/Loss USD_mt5"],
        "pnl_gap_cur": hit["Profit/Loss USD_mt5"] - hit["Profit/Loss USD"] * scale,
        "mae_sqx": hit["mae"] * scale, "mae_live": hit["mae_mt5"],
        "mae_gap": hit["mae_mt5"] - hit["mae"] * scale,
        "mfe_sqx": hit["mfe"] * scale, "mfe_live": hit["mfe_mt5"],
        "mfe_gap": hit["mfe_mt5"] - hit["mfe"] * scale}).reset_index(drop=True)
    sqx_only = both[both["Open time_mt5"].isna()][["Ticket", "Type", "Open time", "Open price",
                                                   "Close time", "points"]]
    live_only = live[~live["row"].isin(hit["row_mt5"])][["Type", "Open time", "Open price",
                                                         "Close time", "Size", "points",
                                                         "Profit/Loss USD"]]

    def mean(column: str, absolute: bool = False) -> float | None:
        """A column's mean over the pairs that have it, None when none does."""
        values = pairs[column].abs() if absolute else pairs[column]
        return None if values.notna().sum() == 0 else float(values.mean())

    def total(values: pd.Series) -> float:
        """A sum over the trades that have the figure (an open position has none yet)."""
        return float(values.fillna(0.0).sum())

    summary = {
        "sqx_trades": len(sqx), "live_trades": len(live), "paired": len(pairs),
        "sqx_only": len(sqx_only), "live_only": len(live_only),
        "live_open": int(live["Close time"].isna().sum()), "clock_h": hours,
        "entry_gap_min_mean_abs": mean("entry_gap_min", True),
        "entry_gap_pts_mean": mean("entry_gap_pts"),
        "entry_slip_pts_mean": mean("entry_slip_pts"),
        "pnl_pts_sqx": total(sqx["points"]), "pnl_pts_live": total(live["points"]),
        "pnl_gap_pts_paired": total(pairs["pnl_gap_pts"]),
        "pnl_cur_live": total(live["Profit/Loss USD"]),
        "pnl_cur_sqx_paired": total(pairs["pnl_cur_sqx"]),
        "pnl_gap_cur_paired": total(pairs["pnl_gap_cur"]),
        "mae_pairs": int(pairs["mae_gap"].notna().sum()),
        "mae_gap_mean": mean("mae_gap"), "mfe_gap_mean": mean("mfe_gap"),
        "worst_mae_sqx": None if pairs["mae_sqx"].isna().all() else float(pairs["mae_sqx"].min()),
        "worst_mae_live": None if pairs["mae_live"].isna().all()
        else float(pairs["mae_live"].min())}
    return {"pairs": pairs, "sqx_only": sqx_only.reset_index(drop=True),
            "live_only": live_only.reset_index(drop=True), "summary": summary}


def totals(summaries: list[dict]) -> dict:
    """The week's totals over every live strategy: counts and P&L added, gaps not averaged."""
    keys = ["sqx_trades", "live_trades", "paired", "sqx_only", "live_only", "live_open",
            "pnl_pts_sqx", "pnl_pts_live", "pnl_gap_pts_paired", "pnl_cur_live",
            "pnl_cur_sqx_paired", "pnl_gap_cur_paired"]
    return {k: sum(s[k] for s in summaries) for k in keys}
