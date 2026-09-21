"""Which parameters move the result: variance explained, and the duplicate test it cannot see."""

import pandas as pd


def eta_squared(frame: pd.DataFrame, parameters: list[str],
                metrics: list[str]) -> pd.DataFrame:
    """Share of each metric's variance explained by each parameter on its own.

    Args:
        frame: A grid, parameters and metrics side by side.
        parameters: Columns to group by.
        metrics: Columns to explain.

    Returns:
        Parameters as rows, metrics as columns, values in [0, 1]. **A table, never one
        column**: measured 2026-09-20 on `Strategy 17.9.39`, `DICrossShift1` explains
        7.6 % of NetProfit and 78.5 % of trade count. "Freeze everything below 0.01" is
        therefore a choice of metric wearing the clothes of a measurement, and the metric
        has to be named in the report.
    """
    out = {}
    for metric in metrics:
        y = pd.to_numeric(frame[metric], errors="coerce")
        ok = y.notna()
        y, grouped = y[ok], frame[ok]
        total = ((y - y.mean()) ** 2).sum()
        out[metric] = {p: grouped.groupby(p)[metric].apply(
            lambda s: len(s) * (pd.to_numeric(s).mean() - y.mean()) ** 2).sum() / total
            for p in parameters}
    return pd.DataFrame(out).loc[parameters]


def duplicate_test(frame: pd.DataFrame, parameters: list[str],
                   keys: tuple[str, ...] = ("NetProfit", "NumberOfTrades")) -> pd.DataFrame:
    """Which parameters change nothing at all, including through interaction.

    Args:
        frame: A grid, parameters and metrics side by side.
        parameters: Columns to test one at a time.
        keys: What counts as the same backtest.

    Returns:
        One row per parameter: how many groups of tuples differ only in it, how many of
        those produced an identical result, and the `inert` call when every group did.

        This catches what eta-squared cannot. Eta-squared measures a main effect, so a
        parameter that acts purely through interaction scores near zero and looks dead;
        this holds every other parameter fixed and asks whether the number moved at all.
        Measured 2026-09-20: on `Strategy 17.9.39` `CBlock_SqzMmnInt21` gives 217 groups,
        all 217 identical -- and on `Strategy 41.5.25` the same parameter gives 108 groups
        of which **106** are identical. **Inertness is a property of the strategy, not of
        the block**, so it is tested per strategy and never assumed.
    """
    rows = []
    for name in parameters:
        others = [c for c in parameters if c != name]
        groups = frame.groupby(others).filter(lambda x: len(x) > 1).groupby(others)
        identical = sum(1 for _, g in groups if all(g[k].nunique() == 1 for k in keys))
        rows.append({"parameter": name, "groups": groups.ngroups, "identical": identical,
                     "inert": bool(groups.ngroups and identical == groups.ngroups)})
    return pd.DataFrame(rows).set_index("parameter")
