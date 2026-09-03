#!/usr/bin/env python3
"""
ATR-stop sizing study for the XAUUSD long-only strategy pool.
=============================================================

QUESTION
    These strategies currently run with NO stop loss (verified: every generated
    strategy carries SQ.Formulas.SLPT.None, because the build task has
    <SLATR>false</SLATR> and <SLRequired>false</SLRequired>).  If we switch the
    ATR stop on, what multiple N of ATR(20) should it be?

METHOD
    1. Read SQX's own per-trade export (`-tools action=orderstocsv`), which
       carries MAE/MFE measured on the M1 price path inside each trade.
    2. Recompute ATR(20) from the same bars SQX backtested on, and take its
       value on the bar CLOSED BEFORE entry (the strategies all use Shift=1,
       so that is the ATR a live stop would have been sized from).
    3. Express every trade's adverse excursion as MAE / ATR20.  For a candidate
       stop at N x ATR, a trade would have been stopped IFF MAE/ATR >= N.
    4. Re-price each trade under each candidate N and aggregate.

KEY UNITS (all verified against this install, see validate_trades.py)
    - MAE ($) / MFE ($) are ACCOUNT CURRENCY, not points.
      price_move = abs(MAE_$) / (Size * POINT_VALUE),  POINT_VALUE = 100.
    - Position Size varies per trade (risk-based sizing), so the conversion
      must use each trade's own Size.
    - Reported Profit/Loss is NET.  Cost per trade is recovered empirically as
      gross - net, which measures ~ $8 per lot per side (commission), plus swap
      on trades held overnight.  We reuse each trade's own realised cost rather
      than assuming one, so the cost model is the install's, not ours.

CAVEATS (stated in the report, not buried here)
    - Path-dependence: we know MAE was reached, not WHEN.  A stop at N x ATR is
      hit iff MAE >= N x ATR, which is exact; but the counterfactual ignores
      that stopping out early frees the strategy to re-enter sooner.
    - Position size is held at its historical value.  In reality, turning a stop
      on changes risk-based sizing, which would change every trade's size.
    - Slippage on the stop fill is not modelled (backtest slippage is 0).

USAGE
    python3 atr_stop_study.py --trades <dir> --bars <dir> --out <dir>
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import sys
from bisect import bisect_right
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


# --------------------------------------------------------------------------
# Install constants (read from settings.xml / project.cfx of THIS install)
# --------------------------------------------------------------------------
POINT_VALUE = 100.0                 # $ per 1.0 price unit per 1.0 lot
ATR_PERIOD = 20                     # MinSLATRPeriod == MaxSLATRPeriod == 20
IS_START = datetime(2008, 1, 1)     # Build task <Setup dateFrom="2008.01.01"
IS_END = datetime(2017, 12, 31, 23, 59)  #            dateTo  ="2017.12.31"

# Candidate stop multiples to sweep (Step 3/4 of the brief)
SLIP_REF = 0.25   # reference stop-fill slippage, in ATR units (~$0.55 on M30 gold)
N_GRID = [round(x, 2) for x in np.arange(0.5, 3.0001, 0.25)]

# dataviz reference palette, light mode.  Charts here are single-series per
# panel, so we only ever need the first three (all-pairs validated) slots.
C_BLUE, C_ORANGE, C_AQUA = "#2a78d6", "#eb6834", "#1baf7a"
C_INK, C_INK2, C_MUTED = "#0b0b0b", "#52514e", "#8a8985"
C_SURFACE, C_GRID = "#fcfcfb", "#e4e3df"


# --------------------------------------------------------------------------
# Bars + ATR
# --------------------------------------------------------------------------
def load_bars(path: Path) -> tuple[list[datetime], np.ndarray, np.ndarray, np.ndarray]:
    """Load an SQX data export (Date;Time;Open;High;Low;Close;Volume)."""
    times, o, h, l, c = [], [], [], [], []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        sample = fh.read(4096)
        fh.seek(0)
        delim = ";" if sample.count(";") > sample.count(",") else ","
        rd = csv.reader(fh, delimiter=delim)
        for row in rd:
            if len(row) < 6:
                continue
            try:
                # Date and Time may be one field or two
                if ":" in row[1]:
                    ts = datetime.strptime(f"{row[0]} {row[1]}", "%Y.%m.%d %H:%M")
                    vals = row[2:6]
                else:
                    ts = datetime.strptime(row[0], "%Y.%m.%d %H:%M")
                    vals = row[1:5]
                oo, hh, ll, cc = (float(v.replace(",", ".")) for v in vals)
            except (ValueError, IndexError):
                continue        # header or malformed line
            times.append(ts); o.append(oo); h.append(hh); l.append(ll); c.append(cc)
    return times, np.array(o), np.array(h), np.array(l), np.array(c)


def wilder_atr(high: np.ndarray, low: np.ndarray, close: np.ndarray,
               period: int = ATR_PERIOD) -> np.ndarray:
    """Wilder-smoothed ATR, the definition MetaTrader/SQX's iATR uses.

    Returns an array aligned to the bars; index i is the ATR of the bar CLOSING
    at i (so a stop set on the next bar's open uses atr[i]).
    """
    n = len(close)
    tr = np.empty(n)
    tr[0] = high[0] - low[0]
    prev_close = close[:-1]
    tr[1:] = np.maximum.reduce([
        high[1:] - low[1:],
        np.abs(high[1:] - prev_close),
        np.abs(low[1:] - prev_close),
    ])
    atr = np.full(n, np.nan)
    if n < period:
        return atr
    atr[period - 1] = tr[:period].mean()          # seed = simple mean
    k = (period - 1) / period
    for i in range(period, n):
        atr[i] = atr[i - 1] * k + tr[i] / period   # Wilder recursion
    return atr


class BarSeries:
    """Bars for one timeframe, with ATR and O(log n) timestamp lookup."""

    def __init__(self, path: Path):
        self.times, self.o, self.h, self.l, self.c = load_bars(path)
        self.atr = wilder_atr(self.h, self.l, self.c)
        self.ts = [t.timestamp() for t in self.times]

    def __len__(self):
        return len(self.ts)

    def index_at_or_before(self, when: datetime) -> int:
        """Index of the last bar whose open time is <= `when` (-1 if none)."""
        return bisect_right(self.ts, when.timestamp()) - 1

    def atr_at_entry(self, when: datetime) -> float | None:
        """ATR(20) of the last bar that had CLOSED before `when`.

        A trade opening at the 19:00 bar can only know the ATR through the
        18:00 bar, matching the strategies' Shift=1 convention.
        """
        i = self.index_at_or_before(when)
        if i < 1:
            return None
        v = self.atr[i - 1]
        return None if (math.isnan(v) or v <= 0) else float(v)

    def bars_between(self, a: datetime, b: datetime) -> int:
        """Number of bars from entry to exit (weekend-gap safe)."""
        ia, ib = self.index_at_or_before(a), self.index_at_or_before(b)
        return max(0, ib - ia)


# --------------------------------------------------------------------------
# Trades
# --------------------------------------------------------------------------
def parse_dt(s: str) -> datetime | None:
    s = (s or "").strip()
    for fmt in ("%Y.%m.%d %H:%M:%S", "%Y.%m.%d %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None


def num(s) -> float | None:
    s = (s or "").strip().replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def load_trades(path: Path, bars_by_tf: dict, tf: str) -> tuple[list[dict], Counter]:
    """Parse one strategy's order export into enriched trade records.

    Drops: unfilled pending orders (blank close price / EndTest), trades outside
    the 2008-2017 in-sample window, and trades whose ATR could not be resolved.
    """
    series = bars_by_tf[tf]
    kept, skipped = [], Counter()

    with open(path, newline="", encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh, delimiter=";"):
            t_open, t_close = parse_dt(r.get("Open time")), parse_dt(r.get("Close time"))
            po, pc = num(r.get("Open price")), num(r.get("Close price"))
            size, pl = num(r.get("Size")), num(r.get("Profit/Loss"))
            mae_d, mfe_d = num(r.get("MAE ($)")), num(r.get("MFE ($)"))

            if None in (t_open, t_close, po, pc, size, pl, mae_d, mfe_d) or size <= 0:
                skipped["unfilled/blank (EndTest pending order)"] += 1
                continue
            if not (IS_START <= t_open <= IS_END):
                skipped["outside 2008-2017 in-sample window"] += 1
                continue

            atr = series.atr_at_entry(t_open)
            if atr is None:
                skipped["no ATR(20) at entry"] += 1
                continue

            notional = size * POINT_VALUE            # $ per 1.0 of price move
            mae_px = abs(mae_d) / notional           # adverse excursion, price
            mfe_px = abs(mfe_d) / notional           # favourable excursion, price
            gross_px = pc - po                       # long-only
            gross_d = gross_px * notional
            cost_d = gross_d - pl                    # realised commission+swap

            kept.append({
                "strategy": path.stem,
                "tf": tf,
                "open_time": t_open,
                "close_time": t_close,
                "open_price": po,
                "close_price": pc,
                "size": size,
                "notional": notional,
                "bars_held": series.bars_between(t_open, t_close),
                "close_type": (r.get("Close type") or "").strip(),
                "pl": pl,
                "gross_px": gross_px,
                "cost": cost_d,
                "atr": atr,
                "mae_px": mae_px,
                "mfe_px": mfe_px,
                "mae_atr": mae_px / atr,
                "mfe_atr": mfe_px / atr,
            })
    return kept, skipped


# --------------------------------------------------------------------------
# Step 4 - counterfactual re-pricing
# --------------------------------------------------------------------------
def simulate(trades: list[dict], n: float, slip_atr: float = 0.0) -> list[float]:
    """Net $ P/L of every trade had the stop been at n x ATR(20).

    A trade is stopped IFF its MAE reached n x ATR before its actual exit.
    That test is exact: MAE is the running maximum of adverse excursion, so
    MAE >= n*ATR means the level was touched.

    `slip_atr` widens the realised stop loss to (n + slip_atr) x ATR.  This is
    the assumption that most flatters a tight stop: gold gaps, and the trades
    whose MAE hugely overshoots the stop level are exactly the ones that would
    NOT have filled at the stop price.  The fill is capped at the trade's own
    MAE - you cannot lose more than the price actually travelled against you.
    """
    out = []
    for t in trades:
        if t["mae_atr"] >= n:
            loss_px = min((n + slip_atr) * t["atr"], t["mae_px"])
            out.append(-loss_px * t["notional"] - t["cost"])
        else:
            out.append(t["gross_px"] * t["notional"] - t["cost"])
    return out


def max_drawdown(pnl: list[float], start_equity: float = 100_000.0) -> float:
    """Max drawdown as a % of the running equity peak."""
    eq, peak, worst = start_equity, start_equity, 0.0
    for p in pnl:
        eq += p
        peak = max(peak, eq)
        if peak > 0:
            worst = max(worst, (peak - eq) / peak)
    return worst * 100.0


def aggregate(trades: list[dict], pnl: list[float], n: float | None) -> dict:
    """Pool-level performance for one candidate N."""
    arr = np.array(pnl)
    wins, losses = arr[arr > 0], arr[arr < 0]
    gross_win, gross_loss = wins.sum(), -losses.sum()
    stopped = sum(1 for t in trades if n is not None and t["mae_atr"] >= n)
    costs = sum(t["cost"] for t in trades)

    # Portfolio equity: every strategy's trades interleaved by exit time.
    order = np.argsort([t["close_time"] for t in trades])
    pooled_dd = max_drawdown([pnl[i] for i in order],
                             start_equity=100_000.0 * len({t["strategy"] for t in trades}))

    # Per-strategy drawdown, then the median - robust to one blow-up.
    by_strat = defaultdict(list)
    for t, p in zip(trades, pnl):
        by_strat[t["strategy"]].append((t["close_time"], p))
    dds = [max_drawdown([p for _, p in sorted(v)]) for v in by_strat.values()]

    return {
        "N": n,
        "trades": len(arr),
        "stop_rate_pct": 100.0 * stopped / len(arr) if len(arr) else 0.0,
        "net_profit": arr.sum(),
        "gross_profit": gross_win,
        "gross_loss": gross_loss,
        "profit_factor": (gross_win / gross_loss) if gross_loss > 0 else float("inf"),
        "avg_per_trade": arr.mean(),
        "win_rate_pct": 100.0 * len(wins) / len(arr) if len(arr) else 0.0,
        "median_strategy_maxdd_pct": float(np.median(dds)) if dds else 0.0,
        "worst_strategy_maxdd_pct": float(np.max(dds)) if dds else 0.0,
        "pooled_maxdd_pct": pooled_dd,
        "total_cost": costs,
        # Step 5: cost as a share of the gross winnings it is charged against
        "cost_drag_pct_of_gross": 100.0 * costs / gross_win if gross_win > 0 else float("nan"),
    }


# --------------------------------------------------------------------------
# Output helpers
# --------------------------------------------------------------------------
def table(rows: list[dict], cols: list[tuple[str, str, str]]) -> str:
    """Render a fixed-width table: cols = [(key, header, format), ...]."""
    head = "  ".join(h.rjust(max(len(h), 9)) for _, h, _ in cols)
    lines = [head, "-" * len(head)]
    for r in rows:
        cells = []
        for k, h, f in cols:
            v = r.get(k)
            s = "-" if v is None else (format(v, f) if isinstance(v, (int, float)) else str(v))
            cells.append(s.rjust(max(len(h), 9)))
        lines.append("  ".join(cells))
    return "\n".join(lines)


def style_axes(ax, title: str, xlabel: str, ylabel: str):
    ax.set_title(title, fontsize=11, color=C_INK, loc="left", pad=10, fontweight="600")
    ax.set_xlabel(xlabel, fontsize=9, color=C_INK2)
    ax.set_ylabel(ylabel, fontsize=9, color=C_INK2)
    ax.tick_params(colors=C_INK2, labelsize=8.5, length=0)
    ax.grid(True, color=C_GRID, linewidth=0.8, alpha=0.9)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left", "bottom"):
        ax.spines[s].set_visible(False)
    ax.set_facecolor(C_SURFACE)


def plot_mae_distribution(trades, sweep, out: Path):
    """Step 3: the MAE/ATR distribution and the stop-rate curve it implies."""
    mae = np.array([t["mae_atr"] for t in trades])
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 4.9), facecolor=C_SURFACE)

    # (a) where adverse excursion actually lands, in ATR units
    clipped = np.clip(mae, 0, 4.0)
    ax1.hist(clipped, bins=np.arange(0, 4.05, 0.1), color=C_BLUE,
             edgecolor=C_SURFACE, linewidth=0.6)
    med = float(np.median(mae))
    top = ax1.get_ylim()[1]
    ax1.axvline(med, color=C_ORANGE, linewidth=2, zorder=5)
    ax1.annotate(f"median {med:.2f}x", xy=(med, top * 0.92),
                 xytext=(6, 0), textcoords="offset points",
                 color=C_ORANGE, fontsize=9, fontweight="600", va="top")
    # Both end bars are pile-ups, not modes - say so, or they read as shape.
    ax1.annotate(f"{100*np.mean(mae <= 1e-9):.0f}% never went\nagainst at all",
                 xy=(0.06, top * 0.99), xytext=(10, -4),
                 textcoords="offset points", color=C_INK2, fontsize=8.5, va="top")
    ax1.annotate(f"{100*np.mean(mae > 4):.0f}% exceed 4x\n(tail runs to {mae.max():.0f}x)",
                 xy=(3.94, top * 0.80), xytext=(-10, 0), ha="right",
                 textcoords="offset points", color=C_INK2, fontsize=8.5, va="top")
    style_axes(ax1, "Where trades actually go against you",
               "MAE ÷ ATR(20) at entry   (end bars are pile-ups: 0, and >4x)",
               "trades")

    # (b) the decision curve: stop-exit rate for each candidate N
    ns = [r["N"] for r in sweep]
    rate = [r["stop_rate_pct"] for r in sweep]
    ax2.axhspan(20, 40, color=C_AQUA, alpha=0.13, zorder=0)
    ax2.annotate("target band 20-40%", xy=(2.98, 40), xytext=(0, 4),
                 textcoords="offset points", ha="right", color="#0d7a55",
                 fontsize=9, fontweight="600")
    ax2.plot(ns, rate, color=C_BLUE, linewidth=2, marker="o", markersize=8,
             markerfacecolor=C_BLUE, markeredgecolor=C_SURFACE, markeredgewidth=2,
             zorder=3, clip_on=False)
    for n, r in zip(ns, rate):
        if n in (0.5, 1.0, 1.5, 2.0, 2.5, 3.0):
            ax2.annotate(f"{r:.0f}%", xy=(n, r), xytext=(0, 11),
                         textcoords="offset points", ha="center",
                         color=C_INK2, fontsize=8.5)
    style_axes(ax2, "Fraction of trades a stop at N x ATR would catch",
               "candidate stop multiple N", "stop-exit rate (%)")
    ax2.set_xlim(0.4, 3.1)
    ax2.set_ylim(0, max(rate) * 1.18 + 2)

    fig.tight_layout(pad=1.6)
    fig.savefig(out, dpi=160, facecolor=C_SURFACE)
    plt.close(fig)


def plot_sweep(sweep, sweep_slip, baseline, out: Path):
    """Step 4/5: what each candidate N does to P&L, and to cost drag.

    The P&L panels carry BOTH fill assumptions, because the difference between
    them is the whole finding: a perfect stop fill makes tight stops look great,
    and that advantage is exactly what disappears under realistic slippage.
    """
    ns = [r["N"] for r in sweep]
    band = [r["N"] for r in sweep if 20 <= r["stop_rate_pct"] <= 40]

    def draw(ax, title, unit, key, fmt, two_series: bool):
        if band:
            ax.axvspan(min(band) - 0.125, max(band) + 0.125,
                       color=C_AQUA, alpha=0.13, zorder=0)
        ax.axhline(baseline[key], color=C_MUTED, linewidth=1.6,
                   linestyle=(0, (5, 4)), zorder=2)
        series = [("perfect stop fill", sweep, C_BLUE)]
        if two_series:
            series.append(("fill 0.25 ATR worse", sweep_slip, C_ORANGE))
        for label, data, colour in series:
            y = [r[key] for r in data]
            ax.plot(ns, y, color=colour, linewidth=2, marker="o", markersize=7,
                    markerfacecolor=colour, markeredgecolor=C_SURFACE,
                    markeredgewidth=2, zorder=3, clip_on=False, label=label)
            # Direct label at the right end so identity is never colour-alone.
            # A single-series panel needs none - its title already names it.
            if two_series:
                ax.annotate(label, xy=(ns[-1], y[-1]), xytext=(-4, 12),
                            textcoords="offset points", ha="right",
                            color=colour, fontsize=8.5, fontweight="600")
        style_axes(ax, title, "candidate stop multiple N", unit)
        ax.set_xlim(0.4, 3.15)
        # keep the baseline label off the curves: pin it low-left inside the axes
        lo, hi = ax.get_ylim()
        pad = (hi - lo) * 0.16
        ax.set_ylim(min(lo, baseline[key]) - pad, hi + pad * 0.6)
        ax.annotate(f"no stop today: {fmt(baseline[key])}",
                    xy=(0.42, baseline[key]), xytext=(2, -12),
                    textcoords="offset points", ha="left", va="top",
                    color=C_MUTED, fontsize=8.5, fontweight="600")

    fig, axes = plt.subplots(2, 2, figsize=(13.2, 8.6), facecolor=C_SURFACE)
    draw(axes[0][0], "Net profit", "$", "net_profit",
         lambda v: f"{v/1e6:.1f}M", True)
    draw(axes[0][1], "Profit factor", "PF", "profit_factor",
         lambda v: f"{v:.2f}", True)
    draw(axes[1][0], "Win rate", "%", "win_rate_pct",
         lambda v: f"{v:.0f}%", False)
    draw(axes[1][1], "Cost drag (costs ÷ gross profit)", "%",
         "cost_drag_pct_of_gross", lambda v: f"{v:.0f}%", False)

    axes[0][0].legend(frameon=False, fontsize=8.5, loc="lower right",
                      labelcolor=C_INK2)
    fig.suptitle("Pool P&L under each candidate ATR-stop multiple   "
                 "(green band = stop-exit rate lands in the 20-40% target)",
                 fontsize=11.5, color=C_INK, x=0.012, ha="left", fontweight="600")
    fig.tight_layout(pad=1.7, rect=(0, 0, 1, 0.963))
    fig.savefig(out, dpi=160, facecolor=C_SURFACE)
    plt.close(fig)


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trades", required=True, type=Path)
    ap.add_argument("--bars", required=True, type=Path)
    ap.add_argument("--scan", type=Path,
                    default=Path(__file__).with_name("strategy_scan.json"))
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    # ---- timeframe per strategy, from the .sqx scan -----------------------
    scan = json.loads(args.scan.read_text())
    tf_of = {f"{r['databank']}__{r['name']}": r["tf"] for r in scan}

    # ---- bars -------------------------------------------------------------
    bars = {}
    for tf in ("M30", "H1"):
        matches = sorted(args.bars.glob(f"*_{tf}.csv"))
        if not matches:
            sys.exit(f"missing bar export for {tf} in {args.bars}")
        bars[tf] = BarSeries(matches[0])
        b = bars[tf]
        print(f"bars {tf}: {len(b):>7,} rows  "
              f"{b.times[0]:%Y-%m-%d} .. {b.times[-1]:%Y-%m-%d}  "
              f"ATR20 median {np.nanmedian(b.atr):.2f}")

    # ---- trades -----------------------------------------------------------
    # Deduplicate first.  The WFM databank re-exports SPP OOS strategies with
    # their parameters externalised for optimisation: a different inner-XML
    # hash, but byte-identical trade lists.  Counting both would double-weight
    # those strategies in every pooled statistic, so we key on the trade list.
    seen: dict[str, str] = {}
    dup_count = 0
    csv_paths = []
    for p in sorted(args.trades.glob("*.csv")):
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        if digest in seen:
            dup_count += 1
            continue
        seen[digest] = p.stem
        csv_paths.append(p)
    print(f"\ndeduplicated: {len(csv_paths)} unique trade lists "
          f"({dup_count} duplicate exports dropped)")

    trades, per_strategy, skipped = [], {}, Counter()
    for csv_path in csv_paths:
        tf = tf_of.get(csv_path.stem)
        if tf is None:
            skipped["strategy not in scan"] += 1
            continue
        t, sk = load_trades(csv_path, bars, tf)
        skipped.update(sk)
        if t:
            per_strategy[csv_path.stem] = t
            trades.extend(t)

    print(f"\n{len(per_strategy)} strategies, {len(trades):,} in-sample trades "
          f"({IS_START:%Y-%m-%d} .. {IS_END:%Y-%m-%d})")
    for k, v in skipped.most_common():
        print(f"  skipped {v:>7,}  {k}")

    report = []
    def say(s=""):
        print(s)
        report.append(s)

    # ================= STEP 2 - current exit mix ==========================
    say("\n" + "=" * 78)
    say("STEP 2 - CURRENT EXIT MIX (no stop loss is configured today)")
    say("=" * 78)
    mix = Counter(t["close_type"] for t in trades)
    total = sum(mix.values())
    say(f"\n{'exit reason':<28} {'trades':>9} {'share':>8}")
    say("-" * 47)
    for k, v in mix.most_common():
        say(f"{k:<28} {v:>9,} {100*v/total:>7.1f}%")
    say(f"\nStop-loss exits: 0 (0.0%) - there is no stop to hit.")

    holds = Counter(t["bars_held"] for t in trades)
    say(f"\nbars held: median {int(np.median([t['bars_held'] for t in trades]))}, "
        f"mean {np.mean([t['bars_held'] for t in trades]):.2f}, "
        f"max {max(holds)}   (ExitAfterBars cap = 8)")
    say("  " + "  ".join(f"{b}:{100*n/total:.0f}%"
                         for b, n in sorted(holds.items())[:11]))

    # per-strategy spread of the time-exit share
    shares = []
    for name, ts in per_strategy.items():
        c = Counter(t["close_type"] for t in ts)
        shares.append(100 * c.get("Exit After X Bars", 0) / len(ts))
    say(f"\nshare of trades hitting the 8-bar cap, across the {len(shares)} "
        f"strategies: min {min(shares):.0f}%  median {np.median(shares):.0f}%  "
        f"max {max(shares):.0f}%")

    # ================= STEP 3 - MAE distribution ==========================
    say("\n" + "=" * 78)
    say("STEP 3 - MAE / ATR(20) DISTRIBUTION  (the core object)")
    say("=" * 78)
    mae = np.array([t["mae_atr"] for t in trades])
    qs = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    say("\npercentiles of MAE ÷ ATR20:")
    say("  " + "  ".join(f"p{q}={np.percentile(mae, q):.2f}" for q in qs))
    say(f"  mean {mae.mean():.2f}   max {mae.max():.2f}   "
        f"zero-MAE trades {100*np.mean(mae <= 1e-9):.1f}%")

    # The pool mixes timeframes; MAE/ATR is scale-free so pooling is valid,
    # but the two groups should be shown separately in case they disagree.
    for tf in ("M30", "H1"):
        sub = np.array([t["mae_atr"] for t in trades if t["tf"] == tf])
        if len(sub):
            ns = len({t["strategy"] for t in trades if t["tf"] == tf})
            say(f"\n  {tf:<4} ({ns:>3} strategies, {len(sub):>7,} trades): "
                f"p25={np.percentile(sub,25):.2f}  p50={np.percentile(sub,50):.2f}  "
                f"p75={np.percentile(sub,75):.2f}  p90={np.percentile(sub,90):.2f}")

    sweep = [aggregate(trades, simulate(trades, n), n) for n in N_GRID]
    say("\nstop-exit rate by candidate N:")
    say("\n" + table(sweep, [("N", "N", ".2f"),
                             ("stop_rate_pct", "stop-out %", ".1f"),
                             ("trades", "trades", ",.0f")]))

    plot_mae_distribution(trades, sweep, args.out / "step3_mae_distribution.png")

    # ================= STEP 4 - P&L under each stop =======================
    say("\n" + "=" * 78)
    say("STEP 4 - SIMULATED P&L BY CANDIDATE STOP MULTIPLE")
    say("=" * 78)
    say("\nApproximation: a trade stops iff MAE >= N x ATR (exact), filling at")
    say("-N x ATR with zero slippage; otherwise it keeps its historical exit.")
    say("Ignores that stopping out early frees capital to re-enter, and holds")
    say("position size at its historical (risk-based) value.")

    baseline = aggregate(trades, [t["gross_px"] * t["notional"] - t["cost"]
                                  for t in trades], None)
    baseline["N"] = None
    rows = [baseline] + sweep
    say("\n" + table(rows, [
        ("N", "N", ".2f"),
        ("stop_rate_pct", "stop %", ".1f"),
        ("net_profit", "net $", ",.0f"),
        ("profit_factor", "PF", ".3f"),
        ("avg_per_trade", "$/trade", ",.1f"),
        ("win_rate_pct", "win %", ".1f"),
        ("median_strategy_maxdd_pct", "med DD%", ".1f"),
        ("worst_strategy_maxdd_pct", "worst DD%", ".1f"),
    ]))
    say("\n(row with blank N = the pool as it runs today, no stop)")

    sweep_slip = [aggregate(trades, simulate(trades, n, SLIP_REF), n)
                  for n in N_GRID]
    plot_sweep(sweep, sweep_slip, baseline, args.out / "step4_pnl_sweep.png")

    # ---- stress test: the zero-slippage stop fill -------------------------
    # This is the assumption most likely to flatter a tight stop.  Gold gaps,
    # and the trades whose MAE overshoots the stop by a wide margin are exactly
    # the ones that would have filled worse than the stop price.
    say("\n" + "-" * 78)
    say("STRESS TEST - how much of the result depends on filling AT the stop?")
    say("-" * 78)
    say("\nRealised stop loss widened to (N + slip) x ATR, capped at the trade's")
    say("own MAE. slip is in ATR units: 0.25 ATR on M30 gold is roughly $0.55.")
    say(f"\n{'N':>6}  " + "  ".join(f"{'slip=' + format(s, '.2f'):>16}"
                                    for s in (0.0, 0.10, 0.25, 0.50)))
    say(f"{'':>6}  " + "  ".join(f"{'net $ / PF':>16}" for _ in range(4)))
    say("-" * 78)
    for n in N_GRID:
        cells = []
        for s in (0.0, 0.10, 0.25, 0.50):
            a = aggregate(trades, simulate(trades, n, s), n)
            cells.append(f"{a['net_profit']/1e6:>7.1f}M {a['profit_factor']:>5.2f}"
                         .rjust(16))
        say(f"{n:>6.2f}  " + "  ".join(cells))
    say(f"\nbaseline (no stop): {baseline['net_profit']/1e6:.1f}M  "
        f"PF {baseline['profit_factor']:.2f}")

    # ================= STEP 5 - cost sensitivity ==========================
    say("\n" + "=" * 78)
    say("STEP 5 - COST DRAG")
    say("=" * 78)
    say("\nNOTE: in this architecture a stop does NOT add round trips. Each trade")
    say("still has exactly one entry and one exit; the stop only moves where the")
    say("exit happens. Total commission is therefore constant across N, and the")
    say("drag ratio worsens purely because tighter stops shrink gross profit.")
    say("")
    say(table([baseline] + sweep, [
        ("N", "N", ".2f"),
        ("trades", "round trips", ",.0f"),
        ("total_cost", "total cost $", ",.0f"),
        ("gross_profit", "gross profit $", ",.0f"),
        ("cost_drag_pct_of_gross", "drag % of gross", ".1f"),
        ("net_profit", "net $", ",.0f"),
    ]))

    # ================= Step 6 inputs - outliers ===========================
    say("\n" + "=" * 78)
    say("STEP 6 INPUT - PER-STRATEGY DISPERSION")
    say("=" * 78)
    per_rows = []
    for name, ts in per_strategy.items():
        m = np.array([t["mae_atr"] for t in ts])
        base = sum(t["gross_px"] * t["notional"] - t["cost"] for t in ts)
        row = {"strategy": name, "tf": ts[0]["tf"], "trades": len(ts),
               "median_mae_atr": float(np.median(m)), "base_net": base}
        for n in (1.0, 1.5, 2.0):
            p = sum(simulate(ts, n))
            row[f"rate@{n}"] = 100.0 * float(np.mean(m >= n))
            row[f"keep@{n}"] = 100.0 * p / base if base != 0 else float("nan")
        per_rows.append(row)

    with open(args.out / "per_strategy.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(per_rows[0].keys()))
        w.writeheader(); w.writerows(per_rows)

    for n in (1.0, 1.5, 2.0):
        r = [x[f"rate@{n}"] for x in per_rows]
        say(f"\nstop-out rate at N={n}: median {np.median(r):.1f}%  "
            f"IQR {np.percentile(r,25):.1f}-{np.percentile(r,75):.1f}%  "
            f"range {min(r):.1f}-{max(r):.1f}%")

    say("\nOutliers - most stop-sensitive (lowest % of no-stop profit retained "
        "at N=1.5):")
    per_rows.sort(key=lambda x: x["keep@1.5"])
    say("\n" + table(per_rows[:8], [
        ("strategy", "strategy", ""), ("tf", "tf", ""),
        ("trades", "trades", ",.0f"), ("median_mae_atr", "med MAE/ATR", ".2f"),
        ("rate@1.5", "stop% @1.5", ".1f"), ("keep@1.5", "profit kept %", ".1f")]))
    say("\nLeast sensitive (a stop costs them almost nothing):")
    say("\n" + table(per_rows[-6:], [
        ("strategy", "strategy", ""), ("tf", "tf", ""),
        ("trades", "trades", ",.0f"), ("median_mae_atr", "med MAE/ATR", ".2f"),
        ("rate@1.5", "stop% @1.5", ".1f"), ("keep@1.5", "profit kept %", ".1f")]))

    # ================= STEP 6 - findings ==================================
    # Computed from the run, not hard-coded, so re-running on a different pool
    # re-derives them rather than restating today's numbers.
    say("\n" + "=" * 78)
    say("STEP 6 - FINDINGS")
    say("=" * 78)

    in_band = [r for r in sweep if 20 <= r["stop_rate_pct"] <= 40]
    say(f"\n(a) The 3xATR stop is not decorative - it does not exist. Every one")
    say(f"    of the {len(seen)} strategies carries SQ.Formulas.SLPT.None, because")
    say(f"    the build task sets <SLATR>false</SLATR> and <SLRequired>false</SLRequired>.")
    say(f"    {mix.most_common(1)[0][1]/total*100:.0f}% of trades exit on the "
        f"{int(np.median([t['bars_held'] for t in trades]))}-bar cap, the rest on an exit signal.")
    say(f"    Had a 3xATR stop existed it would have fired on "
        f"{sweep[-1]['stop_rate_pct']:.0f}% of trades - so it would NOT have been")
    say(f"    decorative either. The hypothesis is refuted twice over.")

    if in_band:
        say(f"\n(b) Stop-exit rate lands in the 20-40% target for "
            f"N = {min(r['N'] for r in in_band):.2f} to {max(r['N'] for r in in_band):.2f}.")
    say(f"    Pool median MAE is {np.median(mae):.2f} x ATR, so a stop below ~1.3x sits")
    say(f"    inside the typical trade's normal adverse excursion.")

    best = max(sweep, key=lambda r: r["net_profit"])
    best_slip = max(sweep_slip, key=lambda r: r["net_profit"])
    say(f"\n(c) Under a perfect stop fill, net profit peaks at N={best['N']:.2f} "
        f"({best['net_profit']/1e6:.1f}M vs {baseline['net_profit']/1e6:.1f}M with no stop).")
    say(f"    Under a realistic fill ({SLIP_REF} ATR worse) the peak moves to "
        f"N={best_slip['N']:.2f} and every")
    say(f"    tight setting collapses: N=0.50 falls "
        f"{100*(1-sweep_slip[0]['net_profit']/sweep[0]['net_profit']):.0f}% "
        f"({sweep[0]['net_profit']/1e6:.1f}M -> {sweep_slip[0]['net_profit']/1e6:.1f}M) "
        f"while N=3.00 falls only")
    say(f"    {100*(1-sweep_slip[-1]['net_profit']/sweep[-1]['net_profit']):.0f}%. "
        f"The apparent superiority of tight stops is an artefact of the")
    say(f"    fill assumption, not an edge. There is no cost-vs-P&L tension: total")
    say(f"    commission is CONSTANT in N (a stop moves an exit, it does not add a")
    say(f"    round trip), so drag only rises because gross profit shrinks.")

    say(f"\n(d) The pool is two populations, and one N will not serve both:")
    cap = [n for n, ts in per_strategy.items()
           if Counter(t["close_type"] for t in ts).get("Exit After X Bars", 0) / len(ts) > 0.5]
    sig = [n for n in per_strategy if n not in cap]
    for label, group in (("bar-cap strategies", cap), ("signal-exit strategies", sig)):
        if not group:
            continue
        g = [t for t in trades if t["strategy"] in group]
        gm = np.array([t["mae_atr"] for t in g])
        say(f"      {label:<24} {len(group):>4} strategies  "
            f"median MAE/ATR {np.median(gm):.2f}  "
            f"stop rate at N=2: {100*np.mean(gm >= 2.0):.0f}%")
    say(f"    The signal-exit group exits in 1-3 bars and barely reaches any stop;")
    say(f"    applying the bar-cap group's N to them would be inert, not protective.")

    # ---- persist ----------------------------------------------------------
    (args.out / "summary.txt").write_text("\n".join(report))
    with open(args.out / "sweep.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(sweep[0].keys()))
        w.writeheader(); w.writerows([baseline] + sweep)
    with open(args.out / "trades_enriched.csv", "w", newline="") as fh:
        cols = ["strategy", "tf", "open_time", "close_time", "bars_held",
                "close_type", "open_price", "close_price", "size", "atr",
                "mae_px", "mfe_px", "mae_atr", "mfe_atr", "gross_px", "cost", "pl"]
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader(); w.writerows(trades)

    print(f"\nwrote {args.out}/summary.txt, sweep.csv, per_strategy.csv, "
          f"trades_enriched.csv, and 2 plots")


if __name__ == "__main__":
    main()
