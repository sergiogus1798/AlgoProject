"""Per-cell trades, mean P&L with its bootstrap interval, and hit rate — floored, never filtered."""

import numpy as np

from core.surface import dedupe
from engines.nulls import inputs as nullinputs
from studies.readings.conditionalMap import regime, sessions

# The same floor the OOS gate reads (engines/nulls/config.yaml#verdict.min_trades): read
# here, not copied, so the two can never quietly drift apart (encargo 14 rule 2).
MIN_CELL = nullinputs.config([])["verdict"]["min_trades"]

WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")


def cell_stats(pnl: np.ndarray, cfg: dict) -> dict | None:
    """One cell's count, mean P&L with its interval, and hit rate.

    Args:
        pnl: Profit/Loss per trade in the cell.
        cfg: The `bootstrap` block of config.yaml.

    Returns:
        None below MIN_CELL trades: too few to say anything, and a mapa de dos dimensiones
        only shows the cells that clear it (encargo 14 rule 2). Otherwise `n`, `mean`,
        `ci_lo`, `ci_hi`, `hit_rate`.
    """
    if len(pnl) < MIN_CELL:
        return None
    lo, hi = dedupe.bootstrap_ci(pnl, np.mean, cfg["resamples"], cfg["confidence"], cfg["seed"])
    return {"n": int(len(pnl)), "mean": float(np.mean(pnl)), "ci_lo": float(lo),
            "ci_hi": float(hi), "hit_rate": float(np.mean(pnl > 0))}


def grid(pnl: np.ndarray, vol_idx: np.ndarray, trend_idx: np.ndarray, cfg: dict) -> dict:
    """Every (volatilidad, tendencia) cell that clears the floor.

    Args:
        pnl: Profit/Loss per trade.
        vol_idx: regime.bucket() on volatility; -1 is excluded from every cell.
        trend_idx: regime.bucket() on efficiency; -1 is excluded from every cell.
        cfg: The `bootstrap` block.

    Returns:
        `mean`: the 3x3 matrix for the heat map, None where the cell is empty or below the
        floor. `count`: every cell's trades, floored or not, so the map can say why a cell
        is blank. `cells`: the cleared cells flat, named and with every stat, for the table.
    """
    mean = [[None] * len(regime.BUCKETS) for _ in regime.BUCKETS]
    count = [[0] * len(regime.BUCKETS) for _ in regime.BUCKETS]
    found = []
    for i, vname in enumerate(regime.BUCKETS):
        for j, tname in enumerate(regime.BUCKETS):
            inside = pnl[(vol_idx == i) & (trend_idx == j)]
            count[i][j] = int(len(inside))
            stats = cell_stats(inside, cfg)
            if stats is None:
                continue
            mean[i][j] = round(stats["mean"], 6)
            found.append({"volatilidad": vname, "tendencia": tname, **stats})
    return {"mean": mean, "count": count, "cells": found}


def by_label(pnl: np.ndarray, labels: np.ndarray, order: tuple, cfg: dict) -> list[dict]:
    """Every label that clears the floor, in the given order.

    Args:
        pnl: Profit/Loss per trade.
        labels: One label per trade — a weekday (inputs.located) or a session.
        order: The labels to try, in display order: WEEKDAYS or sessions.ORDER.
        cfg: The `bootstrap` block.

    Returns:
        `shown`: one dict per label that clears the floor, `cell_stats()` plus `label`.
        `hidden`: {label: trades} for every label below it, zero included.
    """
    shown, hidden = [], {}
    for name in order:
        inside = pnl[labels == name]
        stats = cell_stats(inside, cfg)
        if stats is None:
            hidden[name] = int(len(inside))
        else:
            shown.append({"label": name, **stats})
    return {"shown": shown, "hidden": hidden}


def session_by_weekday(pnl: np.ndarray, session: np.ndarray, weekday: np.ndarray,
                       cfg: dict) -> dict:
    """Every (session, weekday) cell that clears the floor — the two cuts read together.

    Args:
        pnl: Profit/Loss per trade.
        session: One sessions.ORDER label per trade.
        weekday: One English day name per trade.
        cfg: The `bootstrap` block.

    Returns:
        `mean`: sessions x weekdays matrix, None where below the floor. `count`: every
        cell's trades. `cells`: the cleared ones, flat, with every stat.
    """
    mean = [[None] * len(WEEKDAYS) for _ in sessions.ORDER]
    count = [[0] * len(WEEKDAYS) for _ in sessions.ORDER]
    found = []
    for i, sname in enumerate(sessions.ORDER):
        for j, dname in enumerate(WEEKDAYS):
            inside = pnl[(session == sname) & (weekday == dname)]
            count[i][j] = int(len(inside))
            stats = cell_stats(inside, cfg)
            if stats is None:
                continue
            mean[i][j] = round(stats["mean"], 6)
            found.append({"sesión": sname, "weekday": dname, **stats})
    return {"mean": mean, "count": count, "cells": found}
