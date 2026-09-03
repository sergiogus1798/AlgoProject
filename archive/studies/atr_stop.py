#!/usr/bin/env python3
"""What multiple of ATR(20) should the stop be?

Reads the CSVs export.py wrote, measures how far each trade travelled against
its entry in ATR units, and re-prices the pool under each candidate stop.
Writes summary.txt, sweep.csv and two figures into --out.
"""

import argparse
import csv
from bisect import bisect_right
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np

from plots import plot_mae, plot_sweep

POINT_VALUE = 100.0                        # $ per 1.0 of price per 1.0 lot
ATR_PERIOD = 20
IS_START = datetime(2008, 1, 1)
IS_END = datetime(2017, 12, 31, 23, 59)
N_GRID = np.round(np.arange(0.5, 3.01, 0.25), 2)
SLIP = 0.25                                # stress-test stop slippage, ATR units


def load_bars(path):
    """Load an OHLC export written by export.py.

    Inputs:
        path: Path to a CSV, header Date,Time,Open,High,Low,Close,Volume,
              dates "YYYY.MM.DD" and times "HH:MM"
    Output:
        (times, high, low, close) — times is list[float] of POSIX seconds,
        the rest np.ndarray of float, all the same length.
    """
    rows = list(csv.reader(open(path)))[1:]
    times = [datetime.strptime(f"{r[0]} {r[1]}", "%Y.%m.%d %H:%M").timestamp()
             for r in rows]
    ohlc = np.array([[float(r[3]), float(r[4]), float(r[5])] for r in rows])
    return times, ohlc[:, 0], ohlc[:, 1], ohlc[:, 2]


def atr(high, low, close, period):
    """Wilder-smoothed Average True Range.

    Inputs:
        high, low, close: np.ndarray of float, price per bar, same length
        period: int, lookback in bars
    Output:
        np.ndarray of float, same length; entries before index `period` are NaN.

    Uses Wilder's recursive smoothing, which is what SQX's ATR block computes.
    """
    tr = np.maximum(high[1:] - low[1:],
                    np.maximum(np.abs(high[1:] - close[:-1]),
                               np.abs(low[1:] - close[:-1])))
    out = np.full(len(close), np.nan)
    out[period] = tr[:period].mean()
    for i in range(period + 1, len(close)):
        out[i] = (out[i - 1] * (period - 1) + tr[i - 1]) / period
    return out


def atr_at_entry(times, atrs, when):
    """ATR of the last bar that had closed before a trade opened.

    Inputs:
        times: list[float], bar open times as POSIX seconds, ascending
        atrs: np.ndarray of float, ATR per bar
        when: datetime, the trade's entry time
    Output:
        float, the ATR a stop would have been sized from.

    Steps back one extra bar because the strategies read indicators at Shift=1,
    so the bar the trade opens on has not closed yet.
    """
    return atrs[bisect_right(times, when.timestamp()) - 2]


def load_trades(path, timeframe, bars):
    """Read one strategy's order export into trade records.

    Inputs:
        path: Path to a ";"-separated SQX orderstocsv export
        timeframe: str, the strategy's timeframe, a key of `bars`
        bars: dict {timeframe: (times, atrs)}
    Output:
        list of dict, one per in-sample filled trade, with keys:
            strategy (str), close_type (str), close_time (datetime),
            atr (float, price), notional (float, $ per 1.0 of price),
            gross (float, price), cost (float, $), mae_atr (float, ATR units)

    Drops unfilled pending orders and anything outside the in-sample window.
    MAE is exported in account currency, so it is divided by the trade's own
    notional to recover a price distance; position size varies per trade.
    """
    trades = []
    for r in csv.DictReader(open(path, encoding="utf-8-sig"), delimiter=";"):
        if not r["Close price"]:
            continue
        opened = datetime.strptime(r["Open time"], "%Y.%m.%d %H:%M:%S")
        if not IS_START <= opened <= IS_END:
            continue
        notional = float(r["Size"]) * POINT_VALUE
        gross = float(r["Close price"]) - float(r["Open price"])
        bar_atr = atr_at_entry(*bars[timeframe], opened)
        trades.append({
            "strategy": path.stem,
            "close_type": r["Close type"],
            "close_time": datetime.strptime(r["Close time"],
                                            "%Y.%m.%d %H:%M:%S"),
            "atr": bar_atr,
            "notional": notional,
            "gross": gross,
            "cost": gross * notional - float(r["Profit/Loss"]),
            "mae_atr": abs(float(r["MAE ($)"])) / notional / bar_atr,
        })
    return trades


def simulate(trades, n, slip=0.0):
    """Per-trade P&L had the stop been at n x ATR(20).

    Inputs:
        trades: list of dict from load_trades
        n: float or None, stop multiple of ATR; None means no stop
        slip: float, extra loss on a stopped trade, in ATR units
    Output:
        np.ndarray of float, net $ per trade, in the order given.

    A trade stops exactly when its MAE reached n x ATR. The realised loss is
    capped at the distance price actually travelled against it.
    """
    return np.array([
        -min(n + slip, t["mae_atr"]) * t["atr"] * t["notional"] - t["cost"]
        if n is not None and t["mae_atr"] >= n
        else t["gross"] * t["notional"] - t["cost"]
        for t in trades])


def max_drawdown(pnl):
    """Largest peak-to-trough fall of an equity curve.

    Inputs:
        pnl: sequence of float, $ per trade in chronological order
    Output:
        float, percent of the running peak (0-100).
    """
    equity = 100_000 + np.cumsum(pnl)
    return float((1 - equity / np.maximum.accumulate(equity)).max() * 100)


def metrics(trades, pnl, n):
    """Pool performance for one candidate stop multiple.

    Inputs:
        trades: list of dict from load_trades
        pnl: np.ndarray of float, per-trade $ from simulate
        n: float or None, the stop multiple this row describes
    Output:
        dict with keys N, stop_rate, net, pf, per_trade, win_rate, dd, cost,
        gross, drag — percentages as 0-100 floats, money in $.

    Drawdown is the median across strategies of each one's own equity curve,
    which is more informative than one pooled curve over a mixed portfolio.
    """
    win = pnl[pnl > 0].sum()
    loss = -pnl[pnl < 0].sum()
    cost = sum(t["cost"] for t in trades)
    stopped = np.mean([n is not None and t["mae_atr"] >= n for t in trades])

    curves = {}
    for t, p in zip(trades, pnl):
        curves.setdefault(t["strategy"], []).append((t["close_time"], p))
    dd = np.median([max_drawdown([p for _, p in sorted(v)])
                    for v in curves.values()])

    return {"N": n, "stop_rate": 100 * stopped, "net": pnl.sum(),
            "pf": win / loss, "per_trade": pnl.mean(),
            "win_rate": 100 * np.mean(pnl > 0), "dd": dd,
            "cost": cost, "gross": win, "drag": 100 * cost / win}


def show(rows, columns):
    """Render rows as a fixed-width text table.

    Inputs:
        rows: list of dict
        columns: list of (key, header, format spec), e.g. ("pf", "PF", ".3f")
    Output:
        str, the table including its header rule.
    """
    head = "  ".join(h.rjust(10) for _, h, _ in columns)
    out = [head, "-" * len(head)]
    for r in rows:
        out.append("  ".join(
            ("-" if r[k] is None else format(r[k], f)).rjust(10)
            for k, _, f in columns))
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True,
                    help="the --out directory export.py wrote")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)

    timeframes = {r["strategy"]: r["timeframe"]
                  for r in csv.DictReader(open(a.data / "timeframes.csv"))}
    bars = {}
    for tf in sorted(set(timeframes.values())):
        times, high, low, close = load_bars(a.data / "bars" / f"bars_{tf}.csv")
        bars[tf] = (times, atr(high, low, close, ATR_PERIOD))

    trades = []
    for name, tf in timeframes.items():
        trades += load_trades(a.data / "trades" / f"{name}.csv", tf, bars)

    mae = np.array([t["mae_atr"] for t in trades])
    base = metrics(trades, simulate(trades, None), None)
    sweep = [metrics(trades, simulate(trades, n), n) for n in N_GRID]
    sweep_slip = [metrics(trades, simulate(trades, n, SLIP), n) for n in N_GRID]

    mix = Counter(t["close_type"] for t in trades)
    lines = [
        f"{len(timeframes)} strategies, {len(trades):,} in-sample trades "
        f"({IS_START:%Y-%m-%d} to {IS_END:%Y-%m-%d})",
        "",
        "STEP 2 - current exit mix",
        *(f"  {k:<22}{v:>8,}{100 * v / len(trades):>8.1f}%"
          for k, v in mix.most_common()),
        f"  {'Stop loss':<22}{0:>8}{0.0:>8.1f}%   (no stop is configured)",
        "",
        "STEP 3 - MAE / ATR(20) percentiles",
        "  " + "  ".join(f"p{q}={np.percentile(mae, q):.2f}"
                         for q in (10, 25, 50, 75, 90, 99)),
        "",
        "STEP 4 - P&L by candidate stop (perfect fill)",
        show([base] + sweep,
             [("N", "N", ".2f"), ("stop_rate", "stop %", ".1f"),
              ("net", "net $", ",.0f"), ("pf", "PF", ".3f"),
              ("per_trade", "$/trade", ",.1f"), ("win_rate", "win %", ".1f"),
              ("dd", "med DD%", ".1f")]),
        "",
        f"STRESS TEST - stop fills {SLIP} ATR worse",
        show([base] + sweep_slip,
             [("N", "N", ".2f"), ("net", "net $", ",.0f"),
              ("pf", "PF", ".3f"), ("dd", "med DD%", ".1f")]),
        "",
        "STEP 5 - cost drag  (a stop moves an exit, it does not add a round "
        "trip, so total cost is constant in N)",
        show([base] + sweep,
             [("N", "N", ".2f"), ("cost", "cost $", ",.0f"),
              ("gross", "gross $", ",.0f"), ("drag", "drag %", ".1f")]),
    ]

    band = [r for r in sweep if 20 <= r["stop_rate"] <= 40]
    best = max(sweep_slip, key=lambda r: r["net"])
    lines += [
        "",
        "STEP 6 - findings",
        f"  (a) No stop exists today: {100 * mix.most_common(1)[0][1] / len(trades):.0f}%"
        f" of trades exit on '{mix.most_common(1)[0][0]}'.",
        f"  (b) Stop rate is in the 20-40% target for N = "
        f"{min(r['N'] for r in band):.2f} to {max(r['N'] for r in band):.2f}.",
        f"  (c) Under a realistic fill the best N is {best['N']:.2f} "
        f"(${best['net']:,.0f}); tight stops lose most to slippage "
        f"({100 * (1 - sweep_slip[0]['net'] / sweep[0]['net']):.0f}% at N=0.50 "
        f"vs {100 * (1 - sweep_slip[-1]['net'] / sweep[-1]['net']):.0f}% at N=3.00).",
    ]

    report = "\n".join(lines)
    print(report)
    (a.out / "summary.txt").write_text(report)
    with open(a.out / "sweep.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(base))
        w.writeheader()
        w.writerows([base] + sweep)

    plot_mae(mae, sweep, N_GRID, a.out / "fig1_mae.png")
    plot_sweep(sweep, sweep_slip, base, N_GRID, SLIP,
               a.out / "fig2_sweep.png")


if __name__ == "__main__":
    main()
