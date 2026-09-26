"""What buy and hold earned beside each mother, sized to the mother's own risk."""

import numpy as np
import pandas as pd


def equal_risk(panel: pd.DataFrame, moves: pd.Series,
               point_value: float) -> tuple[pd.DataFrame, pd.Series]:
    """Each mother's daily profit minus buy and hold's at the same daily volatility.

    Args:
        panel: Daily profit per mother, account currency.
        moves: The asset's price change on the same days, the first one NaN.
        point_value: Account currency per 1.0 of price and 1.0 of lot.

    Returns:
        The excess panel, and the lots of the asset each mother is held against.

        Copied from `studies/screening/snoopingScreen/benchmark.py` (a helper two studies
        need is copied, not shared). With both sides equally volatile a positive mean
        excess is exactly a Sharpe ratio above buy and hold's.
    """
    held = moves.iloc[1:] * point_value
    days = panel.loc[held.index]
    lots = days.std(ddof=1) / held.std(ddof=1)
    excess = days - np.outer(held.values, lots.values)
    return excess, lots
