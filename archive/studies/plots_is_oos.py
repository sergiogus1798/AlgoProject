#!/usr/bin/env python3
"""Figures for the IS/OOS correlation study. Called by is_oos_analysis.py."""

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
    ax.set_title(title, fontsize=10.5, color=INK, loc="left", pad=8,
                 fontweight="600")
    ax.set_xlabel(xlabel, fontsize=8.5, color=MUTED)
    ax.set_ylabel(ylabel, fontsize=8.5, color=MUTED)
    ax.tick_params(colors=MUTED, labelsize=8, length=0)
    ax.grid(True, color=RULE, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_facecolor(PAPER)
    for side in ax.spines.values():
        side.set_visible(False)


def plot_persistence(persist, r_crit, path):
    """Figure 1: how strongly each metric carries from IS to OOS.

    Inputs:
        persist: list of dict from persistence(), sorted by |spearman|
        r_crit: float, the significance floor to mark
        path: Path to write the PNG to
    Output:
        None.
    """
    rows = persist[::-1]
    labels = [r["metric"] for r in rows]
    values = [r["spearman"] for r in rows]
    significant = [abs(v) > r_crit for v in values]

    fig, ax = plt.subplots(figsize=(9.5, 9.6), facecolor=PAPER)
    ax.barh(labels, values,
            color=[BLUE if s else RULE for s in significant], height=0.68)
    ax.axvline(0, color=MUTED, linewidth=1)
    for sign in (1, -1):
        ax.axvline(sign * r_crit, color=ORANGE, linewidth=1.4,
                   linestyle=(0, (4, 3)))
    ax.annotate(f"significance floor  |r| = {r_crit:.2f}",
                xy=(r_crit, len(rows) - 0.4), xytext=(5, 0),
                textcoords="offset points", color=ORANGE, fontsize=8.5,
                fontweight="600", va="center")
    for y, (v, s) in enumerate(zip(values, significant)):
        ax.annotate(f"{v:+.2f}", xy=(v, y),
                    xytext=(5 if v >= 0 else -5, 0),
                    textcoords="offset points", va="center",
                    ha="left" if v >= 0 else "right",
                    color=INK if s else MUTED, fontsize=8,
                    fontweight="600" if s else "400")
    style(ax, "Does an in-sample metric keep its value out of sample?",
          "Spearman correlation, same metric IS vs OOS", "")
    ax.set_xlim(min(values) - 0.18, max(values) + 0.18)
    fig.tight_layout(pad=1.4)
    fig.savefig(path, dpi=160, facecolor=PAPER)


def plot_scatter_grid(columns, top, path):
    """Figure 2: IS against OOS for the metrics that persist best.

    Inputs:
        columns: dict {column name: np.ndarray} from load()
        top: list of dict, the metrics to plot (from persistence())
        path: Path to write the PNG to
    Output:
        None.

    The dashed line is y = x: points below it are strategies that got worse
    out of sample, which for most metrics is nearly all of them.
    """
    fig, axes = plt.subplots(2, 3, figsize=(13.4, 8.2), facecolor=PAPER)

    for ax, row in zip(axes.ravel(), top):
        metric = row["metric"]
        x, y = columns[f"{metric} (IS)"], columns[f"{metric} (OOS)"]
        ax.scatter(x, y, s=46, color=BLUE, alpha=0.75, edgecolor=PAPER,
                   linewidth=1.2, zorder=3)

        lo = min(x.min(), y.min())
        hi = max(x.max(), y.max())
        ax.plot([lo, hi], [lo, hi], color=MUTED, linewidth=1.3,
                linestyle=(0, (4, 3)), zorder=2)
        slope, intercept = np.polyfit(x, y, 1)
        grid = np.array([x.min(), x.max()])
        ax.plot(grid, slope * grid + intercept, color=ORANGE, linewidth=2,
                zorder=4)

        style(ax, metric, f"{metric} (IS)", f"{metric} (OOS)")
        ax.annotate(f"r = {row['spearman']:+.2f}   p = {row['p']:.3f}",
                    xy=(0.04, 0.94), xycoords="axes fraction",
                    color=INK, fontsize=9, fontweight="600", va="top")

    fig.suptitle("In-sample against out-of-sample, per strategy   "
                 "(grey dashed = y is x, orange = fitted trend)",
                 fontsize=11.5, color=INK, x=0.012, ha="left",
                 fontweight="600")
    fig.tight_layout(pad=1.6, rect=(0, 0, 1, 0.955))
    fig.savefig(path, dpi=160, facecolor=PAPER)


def plot_predictors(ranked, r_crit, target, path):
    """Figure 3: which in-sample metrics predict one OOS outcome.

    Inputs:
        ranked: list of dict from predictors(), sorted by |spearman|
        r_crit: float, the significance floor to mark
        target: str, the OOS outcome being predicted, for the title
        path: Path to write the PNG to
    Output:
        None.
    """
    rows = ranked[:16][::-1]
    labels = [r["metric"] for r in rows]
    values = [r["spearman"] for r in rows]
    significant = [abs(v) > r_crit for v in values]

    fig, ax = plt.subplots(figsize=(9.5, 7.4), facecolor=PAPER)
    ax.barh(labels, values,
            color=[AQUA if s else RULE for s in significant], height=0.68)
    ax.axvline(0, color=MUTED, linewidth=1)
    for sign in (1, -1):
        ax.axvline(sign * r_crit, color=ORANGE, linewidth=1.4,
                   linestyle=(0, (4, 3)))
    ax.annotate(f"significance floor  |r| = {r_crit:.2f}",
                xy=(r_crit, len(rows) - 0.4), xytext=(5, 0),
                textcoords="offset points", color=ORANGE, fontsize=8.5,
                fontweight="600", va="center")
    for y, (v, s) in enumerate(zip(values, significant)):
        ax.annotate(f"{v:+.2f}", xy=(v, y),
                    xytext=(5 if v >= 0 else -5, 0),
                    textcoords="offset points", va="center",
                    ha="left" if v >= 0 else "right",
                    color=INK if s else MUTED, fontsize=8,
                    fontweight="600" if s else "400")
    style(ax, f"Which in-sample metric predicts {target}?",
          "Spearman correlation against " + target, "")
    ax.set_xlim(min(values) - 0.18, max(values) + 0.18)
    fig.tight_layout(pad=1.4)
    fig.savefig(path, dpi=160, facecolor=PAPER)
