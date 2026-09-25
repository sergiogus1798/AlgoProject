"""How far the optimiser's chosen tuple moves from one step to the next."""

import numpy as np
import pandas as pd


def per_step(chosen: pd.DataFrame) -> pd.DataFrame:
    """Movement between consecutive steps, within each cell.

    Args:
        chosen: Output of `inputs.export.chosen`, indexed by (strategy, result, index).

    Returns:
        One row per consecutive pair: how many parameters changed, what share of them
        that is, and the mean absolute move in units of each parameter's own spread.

        Normalising by the parameter's own spread across the export is what makes periods
        and shifts comparable: a period moving by 3 and a shift moving by 3 are not the
        same event.

        Two strategies share one wide frame, so each one's block carries the other's
        parameters as all-NaN columns. They are dropped per strategy, because `NaN != 0`
        is True and leaving them in counts a parameter the strategy does not have as
        changed at every single step.
    """
    spread = chosen.std().replace(0, np.nan)
    rows = []
    for (strategy, result), block in chosen.groupby(level=[0, 1]):
        ordered = block.droplevel([0, 1]).sort_index().dropna(axis=1, how="all")
        step = ordered.diff().iloc[1:]
        for index, values in step.iterrows():
            changed = values != 0
            rows.append({"strategy": strategy, "result": result, "index": int(index),
                         "changed": int(changed.sum()),
                         "share_changed": float(changed.mean()),
                         "move": float((values.abs() / spread).mean())})
    return pd.DataFrame(rows)


def summary(steps: pd.DataFrame, chosen: pd.DataFrame) -> pd.DataFrame:
    """Drift per strategy, in the two units that mean something.

    Args:
        steps: Output of `per_step`.
        chosen: The frame it was computed from, for the parameter count.

    Returns:
        One row per strategy: parameters, median and mean share changed per step, and the
        median normalised move.

        A share near 1 means the optimiser picks a substantially different strategy every
        time it re-optimises. That is the same thing the variant study measures as
        "optimum drift", measured here directly and without fabricating anything --
        and it is the reason a single in-sample optimum is a weak thing to deploy.
    """
    rows = []
    for strategy, block in steps.groupby("strategy"):
        rows.append({"strategy": strategy,
                     "parameters": int(chosen.shape[1]),
                     "pairs": int(len(block)),
                     "share_changed_median": float(block["share_changed"].median()),
                     "share_changed_mean": float(block["share_changed"].mean()),
                     "move_median": float(block["move"].median())})
    return pd.DataFrame(rows)


def stability(chosen: pd.DataFrame) -> pd.DataFrame:
    """Which parameters the optimiser keeps re-deciding, and which it settles on.

    Args:
        chosen: Output of `inputs.export.chosen`.

    Returns:
        One row per (strategy, parameter): distinct values chosen, and the share of the
        steps that took the most common one. A parameter the optimiser lands on every
        time is a candidate for freezing in any design; one it never agrees with itself
        about is where the in-sample surface is flat or noisy.
    """
    rows = []
    for strategy, block in chosen.groupby(level=0):
        owned = block.dropna(axis=1, how="all")
        for name in owned.columns:
            values = owned[name].dropna()
            rows.append({"strategy": strategy, "parameter": name,
                         "distinct": int(values.nunique()),
                         "modal_share": float(values.value_counts(normalize=True).iloc[0])})
    return pd.DataFrame(rows).sort_values(["strategy", "modal_share"], ascending=[True, False])
