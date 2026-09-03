#!/usr/bin/env python3
"""The two figures for the ATR-stop study. Called by atr_stop.py."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, MUTED, RULE, PAPER = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"


def style(ax, title, xlabel, ylabel):
    """Apply the shared chart styling to one axis.

    Inputs:
        ax: matplotlib Axes
        title, xlabel, ylabel: str
    Output:
        None.
    """
    ax.set_title(title, fontsize=11, color=INK, loc="left", pad=10,
                 fontweight="600")
    ax.set_xlabel(xlabel, fontsize=9, color=MUTED)
    ax.set_ylabel(ylabel, fontsize=9, color=MUTED)
    ax.tick_params(colors=MUTED, labelsize=8.5, length=0)
    ax.grid(True, color=RULE, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_facecolor(PAPER)
    for side in ax.spines.values():
        side.set_visible(False)


def plot_mae(mae, sweep, n_grid, path):
    """Figure 1: the MAE distribution and the stop rate it implies.

    Inputs:
        mae: np.ndarray of float, MAE per trade in ATR units
        sweep: list of dict from metrics, one per candidate N
        n_grid: np.ndarray of float, the candidate stop multiples
        path: Path to write the PNG to
    Output:
        None.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 4.9), facecolor=PAPER)

    ax1.hist(np.clip(mae, 0, 4), bins=np.arange(0, 4.05, 0.1), color=BLUE,
             edgecolor=PAPER, linewidth=0.6)
    median = np.median(mae)
    ax1.axvline(median, color=ORANGE, linewidth=2)
    top = ax1.get_ylim()[1]
    ax1.annotate(f"median {median:.2f}x", xy=(median, top * 0.92),
                 xytext=(6, 0), textcoords="offset points", color=ORANGE,
                 fontsize=9, fontweight="600", va="top")
    ax1.annotate(f"{100 * np.mean(mae <= 0):.0f}% never went\nagainst at all",
                 xy=(0.06, top), xytext=(10, -4), textcoords="offset points",
                 color=MUTED, fontsize=8.5, va="top")
    ax1.annotate(f"{100 * np.mean(mae > 4):.0f}% exceed 4x\n"
                 f"(tail runs to {mae.max():.0f}x)",
                 xy=(3.94, top * 0.80), xytext=(-10, 0), ha="right",
                 textcoords="offset points", color=MUTED, fontsize=8.5,
                 va="top")
    style(ax1, "Where trades actually go against you",
          "MAE / ATR(20) at entry   (end bars are pile-ups: 0, and >4x)",
          "trades")

    rate = [r["stop_rate"] for r in sweep]
    ax2.axhspan(20, 40, color=AQUA, alpha=0.13)
    ax2.annotate("target band 20-40%", xy=(n_grid[-1], 40), xytext=(0, 4),
                 textcoords="offset points", ha="right", color="#0d7a55",
                 fontsize=9, fontweight="600")
    ax2.plot(n_grid, rate, color=BLUE, linewidth=2, marker="o", markersize=8,
             markeredgecolor=PAPER, markeredgewidth=2, clip_on=False)
    style(ax2, "Fraction of trades a stop at N x ATR would catch",
          "candidate stop multiple N", "stop-exit rate (%)")
    ax2.set_xlim(n_grid[0] - 0.1, n_grid[-1] + 0.1)
    ax2.set_ylim(0, max(rate) * 1.18)

    fig.tight_layout(pad=1.6)
    fig.savefig(path, dpi=160, facecolor=PAPER)


def plot_sweep(sweep, sweep_slip, base, n_grid, slip, path):
    """Figure 2: P&L across candidate stops, under both fill assumptions.

    Inputs:
        sweep, sweep_slip: list of dict from metrics, perfect and slipped fills
        base: dict from metrics, the no-stop baseline
        n_grid: np.ndarray of float, the candidate stop multiples
        slip: float, the stress-test slippage in ATR units, for the label
        path: Path to write the PNG to
    Output:
        None.

    The P&L panels carry both fill assumptions because the gap between them is
    the finding: a perfect fill is what makes a tight stop look good.
    """
    panels = [("net", "Net profit", "$", ",.0f", True),
              ("pf", "Profit factor", "PF", ".2f", True),
              ("win_rate", "Win rate", "%", ".0f", False),
              ("drag", "Cost drag (costs / gross profit)", "%", ".1f", False)]
    fig, axes = plt.subplots(2, 2, figsize=(13.2, 8.6), facecolor=PAPER)

    for ax, (key, title, unit, fmt, two) in zip(axes.ravel(), panels):
        band = [r["N"] for r in sweep if 20 <= r["stop_rate"] <= 40]
        ax.axvspan(min(band) - 0.125, max(band) + 0.125, color=AQUA, alpha=0.13)
        ax.axhline(base[key], color=MUTED, linewidth=1.6, linestyle=(0, (5, 4)))

        series = [("perfect stop fill", sweep, BLUE)]
        if two:
            series.append((f"fill {slip} ATR worse", sweep_slip, ORANGE))
        for label, data, colour in series:
            y = [r[key] for r in data]
            ax.plot(n_grid, y, color=colour, linewidth=2, marker="o",
                    markersize=7, markeredgecolor=PAPER, markeredgewidth=2,
                    clip_on=False, label=label)
            if two:
                ax.annotate(label, xy=(n_grid[-1], y[-1]), xytext=(-4, 12),
                            textcoords="offset points", ha="right",
                            color=colour, fontsize=8.5, fontweight="600")

        style(ax, title, "candidate stop multiple N", unit)
        ax.set_xlim(n_grid[0] - 0.1, n_grid[-1] + 0.15)
        low, high = ax.get_ylim()
        ax.set_ylim(min(low, base[key]) - (high - low) * 0.16, high)
        ax.annotate(f"no stop today: {format(base[key], fmt)}",
                    xy=(n_grid[0] - 0.08, base[key]), xytext=(2, -12),
                    textcoords="offset points", va="top", color=MUTED,
                    fontsize=8.5, fontweight="600")

    axes[0][0].legend(frameon=False, fontsize=8.5, loc="lower right",
                      labelcolor=MUTED)
    fig.suptitle("Pool P&L under each candidate ATR-stop multiple   "
                 "(green band = stop rate in the 20-40% target)",
                 fontsize=11.5, color=INK, x=0.012, ha="left",
                 fontweight="600")
    fig.tight_layout(pad=1.7, rect=(0, 0, 1, 0.963))
    fig.savefig(path, dpi=160, facecolor=PAPER)
