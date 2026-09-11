"""Assign the trades of a data=all export to the Walk-Forward cell and period that produced them."""

import numpy as np
import pandas as pd

MAIN, START = "IST", "IS"


def chunks(trades: pd.DataFrame) -> list[pd.DataFrame]:
    """Cut one strategy's data=all export into its main result and one block per matrix cell.

    Args:
        trades: A whole exported CSV, read by `core.trades.read`, rows in file order.

    Returns:
        The main backtest first, then one frame per cell in the order the cells appear in
        `settings.xml`. Every cell block opens with the backtest of its first optimisation
        window, which is the only place `Sample type` turns back to IS -- the Symbol column
        cannot separate these blocks the way it separates a cross-market retest, because
        every cell trades the same symbol.
    """
    starts = [0] + list(trades.index[(trades["Sample type"] == START)
                                     & (trades["Sample type"].shift() != START)])
    return [trades.iloc[a:b] for a, b in zip(starts, starts[1:] + [len(trades)])]


def label(block: pd.DataFrame, steps: list[dict]) -> pd.DataFrame:
    """Tag every trade of one cell with the walk-forward step it was traded in.

    Args:
        block: One cell's trades, from `chunks`.
        steps: That cell's rows from `core.wfmatrix.periods`, in index order.

    Returns:
        The block with `period` and `sample` added. `period` is -1 for the trades of the
        first optimisation window, which SQX runs before the walk forward starts and
        labels IS; every later trade belongs to the last step that had started.

        The bound has to be the next step's `run_from`, not this one's `run_to`: `run_to`
        is a date at midnight, so testing against it drops every trade taken later that
        same day -- 81 of 58,500 on the strategy this was checked against.
    """
    opened = block["Open time"].astype("int64") // 10**9
    period = np.searchsorted([s["run_from"] for s in steps], opened, side="right") - 1
    return block.assign(period=period,
                        sample=np.where(period < 0, START, "OOS"))


def check(labelled: pd.DataFrame, steps: list[dict]) -> pd.DataFrame:
    """Compare the trades assigned to each step against the count SQX stored for it.

    Args:
        labelled: One cell's output of `label`.
        steps: The same cell's rows from `core.wfmatrix.periods`.

    Returns:
        One row per non-future step with `index`, `assigned` and `stored`. A study that
        splits a 60,000-row CSV on dates has to prove the split, and SQX's own
        `oos_NumberOfTrades` is the only independent witness available.
    """
    got = labelled["period"].value_counts()
    return pd.DataFrame([{"index": s["index"], "assigned": int(got.get(s["index"], 0)),
                          "stored": int(s["oos_NumberOfTrades"])}
                         for s in steps if not s["future"]])
