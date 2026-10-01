"""Every cell's own out-of-sample equity on one comparable axis, and its statistics as a population."""

import numpy as np
import pandas as pd

POINTS = 101   # 0 to 100 %, one point per percentage point


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
    mine = trades[(trades["strategy"] == strategy) & (trades["sample"] == "OOS")]
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
        `result`, `net_profit`, `profit_factor`, `sharpe` (daily P/L on business days from
        the first to the last OOS close, idle days 0, mean/std ×√252), `max_dd` (closed
        trades, in money) and `trades`.
    """
    mine = trades[(trades["strategy"] == strategy) & (trades["sample"] == "OOS")]
    rows = []
    for cell, g in mine.sort_values("Close time").groupby("result", observed=True):
        pl = g["Profit/Loss"].to_numpy(dtype=float)
        if pl.size < 2:
            continue
        daily = (g.groupby(g["Close time"].dt.normalize())["Profit/Loss"].sum()
                 .reindex(pd.bdate_range(g["Close time"].min().normalize(),
                                         g["Close time"].max().normalize()), fill_value=0.0))
        cum = np.cumsum(pl)
        loss = -pl[pl < 0].sum()
        rows.append({"result": str(cell), "net_profit": pl.sum(),
                     "profit_factor": pl[pl > 0].sum() / loss if loss else np.nan,
                     "sharpe": daily.mean() / daily.std() * np.sqrt(252),
                     "max_dd": float((np.maximum.accumulate(np.maximum(cum, 0)) - cum).max()),
                     "trades": pl.size})
    return pd.DataFrame(rows)


def aggregate(cells: pd.DataFrame) -> pd.DataFrame:
    """The cells as one population: median and spread of each metric, and the share in profit.

    Args:
        cells: `per_cell`.

    Returns:
        One row per metric: `mediana`, `p25`, `p75`, `peor`, `mejor` across cells, then a
        last row with the share of cells that ended in profit.
    """
    names = {"net_profit": "beneficio neto (USD)", "profit_factor": "PF",
             "sharpe": "Sharpe anual", "max_dd": "DD máx. (USD)", "trades": "operaciones"}
    rows = []
    for col, label in names.items():
        v = cells[col].dropna()
        worst, best = (v.max(), v.min()) if col == "max_dd" else (v.min(), v.max())
        rows.append({"métrica": label, "mediana": v.median(), "p25": v.quantile(0.25),
                     "p75": v.quantile(0.75), "peor": worst, "mejor": best})
    share = (cells["net_profit"] > 0).mean() * 100
    rows.append({"métrica": f"% de celdas en beneficio ({len(cells)} celdas)", "mediana": share,
                 "p25": None, "p75": None, "peor": None, "mejor": None})
    return pd.DataFrame(rows).round(2)
