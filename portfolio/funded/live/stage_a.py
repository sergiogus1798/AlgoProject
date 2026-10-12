"""Stage A: the first real trades of a strategy against its SQX backtest, on rows 1, 2, 3a and 5 of step 26."""
import pandas as pd

from mt5 import compare
from mt5.verify import judge

ROWS = {"1": "matched_min", "2": "trade_gap_max_r", "3a": "daily_corr_min", "5": "dd_rel_gap_max"}
# judge.rows reads every threshold of its dict; the rows not judged here still need a key.
UNUSED = {"exit_same_min": 0.0, "daily_mad_max_pct": 0.0, "worst_day_gap_max_pp": 0.0}


def run(sqx: pd.DataFrame, real: pd.DataFrame, timeframe: str, deposit: float, cfg: dict) -> dict:
    """Judge the first `trades` real trades; row 1 only warns, the others take the strategy out.

    Args:
        sqx: The SQX backtest trades in SQX's export shape, already in the server's zone and in
            the same P&L units as `real`.
        real: The real trades, same shape; the oldest `trades` by open time are read, and the
            SQX side is clipped to their time window.
        timeframe: The strategy's timeframe, M1..D1 (sets the entry tolerance).
        deposit: The account both sides start from.
        cfg: The `stage_a` block of config.yaml, ledger values filled, plus `max_offset_h`.

    Returns:
        {"rows": rows 1, 2, 3a, 5 of the judge, "failed": rows 2/3a/5 that failed, "warning":
        row 1 failed, "out": a row failed with the full `trades` read, "ready": `trades` read,
        "n": real trades read, "hours": the clock shift applied to the SQX side}.
    """
    first = real.sort_values("Open time").head(cfg["trades"])
    tolerance = cfg["tolerance_bars"] * judge.MINUTES[timeframe]
    hours = judge.clock(sqx, first, tolerance, cfg["max_offset_h"])
    moved = judge.shifted(sqx, hours)
    window = moved[(moved["Open time"] >= first["Open time"].min()) & (moved["Close time"] <= first["Close time"].max())]
    pairs = compare.pair(window, first, tolerance)
    th = {**UNUSED, **{k: cfg[k] for k in ROWS.values()}}
    rows = [r for r in judge.rows(window, first, pairs, deposit, th) if r["row"] in ROWS]
    failed = [r["row"] for r in rows if r["state"] == "fail" and r["row"] != "1"]
    ready = len(first) >= cfg["trades"]
    return {"rows": rows, "failed": failed, "warning": any(r["row"] == "1" and r["state"] == "fail" for r in rows),
            "out": ready and bool(failed), "ready": ready, "n": len(first), "hours": hours}
