"""Every cell's own out-of-sample equity on one comparable axis, and its statistics as a population."""

from typing import cast

import numpy as np
import pandas as pd

from core import metrics

POINTS = 101  # 0 to 100 %, one point per percentage point


def oos_curves(trades: pd.DataFrame, strategy: str) -> tuple[list[str], np.ndarray]:
    """One resampled curve per cell, so cells with different trade counts overlay.

    Args:
        trades: `wfm/trades.parquet`, every step's trades tagged by cell and sample.
        strategy: Which strategy's cells to read.

    Returns:
        Cell names, and an array (cells, `POINTS`) of cumulative profit. Cells are resampled
        onto percent-of-trades-done rather than calendar time or trade count, because a cell
        with 40 % out of sample runs three times as many trades as one with 20 %, and lining
        them up by date would mean nothing — the walk-forward runs of a 6-run cell and a
        16-run cell do not share a single one of their real dates.
    """
    mine = cast(
        pd.DataFrame,
        trades[(trades["strategy"] == strategy) & (trades["sample"] == "OOS")],
    )
    grid = np.linspace(0, 100, POINTS)
    names, curves = [], []
    for cell, g in mine.sort_values("Close time").groupby("result", observed=True):
        pl = g["Profit/Loss"].to_numpy(dtype=float)
        if pl.size < 2:
            continue
        cum = np.cumsum(pl)
        names.append(str(cell))
        curves.append(np.interp(grid, np.linspace(0, 100, cum.size), cum))
    return names, np.array(curves)


def per_cell(trades: pd.DataFrame, strategy: str) -> pd.DataFrame:
    """Each cell's out-of-sample result as one row, every number over its whole OOS span.

    Args:
        trades: `wfm/trades.parquet`.
        strategy: Which strategy's cells to read.

    Returns:
        `result`, `net_profit`, `profit_factor`, `sharpe` (`core.metrics.sharpe` of `weekday_pnl`: daily P/L on
        business days, idle days 0, a weekend close on Monday, mean/std ×√252), `max_dd` (closed
        trades, in money, from 0) — `profit_factor` inf without a loss and `trades`.
    """
    mine = cast(
        pd.DataFrame,
        trades[(trades["strategy"] == strategy) & (trades["sample"] == "OOS")],
    )
    rows = []
    for cell, g in mine.sort_values("Close time").groupby("result", observed=True):
        pl = g["Profit/Loss"].to_numpy(dtype=float)
        if pl.size < 2:
            continue
        rows.append(
            {
                "result": str(cell),
                "net_profit": pl.sum(),
                "profit_factor": metrics.profit_factor(pl),
                "sharpe": metrics.sharpe(
                    metrics.weekday_pnl(pl, g["Close time"].to_numpy()),
                    metrics.TRADING_DAYS,
                ),
                "max_dd": metrics.dd_money(metrics.cumulative(pl)),
                "trades": pl.size,
            }
        )
    return pd.DataFrame(rows)


def aggregate(cells: pd.DataFrame) -> pd.DataFrame:
    """The cells as one population: median and spread of each metric, and the share in profit.

    Args:
        cells: `per_cell`.

    Returns:
        One row per metric: `mediana`, `p25`, `p75`, `peor`, `mejor` across cells, then a
        last row with the share of cells that ended in profit.
    """
    names = {
        "net_profit": "beneficio neto (USD)",
        "profit_factor": "PF",
        "sharpe": "Sharpe anual",
        "max_dd": "DD máx. (USD)",
        "trades": "operaciones",
    }
    rows = []
    for col, label in names.items():
        v = cells[col].dropna()
        worst, best = (v.max(), v.min()) if col == "max_dd" else (v.min(), v.max())
        # PF is inf in a cell without a loss: interpolating toward it is inf or inf-inf (NaN)
        how = "lower" if col == "profit_factor" else "linear"
        rows.append(
            {
                "métrica": label,
                "mediana": v.quantile(0.5, interpolation=how),
                "p25": v.quantile(0.25, interpolation=how),
                "p75": v.quantile(0.75, interpolation=how),
                "peor": worst,
                "mejor": best,
            }
        )
    share = (cells["net_profit"] > 0).mean() * 100
    rows.append(
        {
            "métrica": f"% de celdas en beneficio ({len(cells)} celdas)",
            "mediana": share,
            "p25": None,
            "p75": None,
            "peor": None,
            "mejor": None,
        }
    )
    return pd.DataFrame(rows).round(2)


def versus_original(
    trades: pd.DataFrame,
    main: pd.DataFrame,
    steps: pd.DataFrame,
    strategy: str,
    points: int = 200,
) -> dict[str, dict]:
    """Each cell's stitched OOS equity against the original's over those very windows.

    Args:
        trades: `wfm/trades.parquet`.
        main: `wfm/main.parquet`, the original's trades with its fixed parameters.
        steps: `inputs.export.steps` (future steps already dropped): the cell's run windows.
        strategy: Which strategy.
        points: Dates kept on the x axis.

    Returns:
        Cell name -> `x` (ISO dates), `cell` and `original` (cumulative profit, both from 0 at
        the cell's first window), `n_cell` and `n_original`. The original is counted only on
        trades that closed inside a window of that cell's out-of-sample runs, so both curves
        earn over the same days; the gaps between windows count for neither.
    """
    mine = cast(
        pd.DataFrame,
        trades[(trades["strategy"] == strategy) & (trades["sample"] == "OOS")],
    )
    orig = cast(pd.DataFrame, main[main["strategy"] == strategy]).sort_values(
        "Close time"
    )
    out = {}
    for cell, g in mine.sort_values("Close time").groupby("result", observed=True):
        win = cast(
            pd.DataFrame,
            steps[(steps["strategy"] == strategy) & (steps["result"] == cell)],
        ).sort_values("run_from")
        if len(g) < 2 or win.empty:
            continue
        start, end = (win[c].to_numpy("datetime64[ns]") for c in ("run_from", "run_to"))
        t = orig["Close time"].to_numpy("datetime64[ns]")
        k = np.searchsorted(start, t, side="right") - 1
        kept = cast(pd.DataFrame, orig[(k >= 0) & (t < end[np.clip(k, 0, None)])])
        grid = pd.date_range(
            start[0], min(end[-1], g["Close time"].max()), periods=points
        )

        def at(frame: pd.DataFrame, grid: pd.DatetimeIndex = grid) -> list[float]:
            """Cumulative profit of `frame` at each grid date."""
            cum = np.concatenate(
                [[0.0], np.cumsum(frame["Profit/Loss"].to_numpy(dtype=float))]
            )
            return [
                float(cum[i])
                for i in np.searchsorted(
                    frame["Close time"].to_numpy("datetime64[ns]"),
                    grid.to_numpy(),
                    side="right",
                )
            ]

        out[str(cell)] = {
            "x": [d.date().isoformat() for d in grid],
            "cell": at(g),
            "original": at(kept),
            "n_cell": len(g),
            "n_original": len(kept),
        }
    return out
