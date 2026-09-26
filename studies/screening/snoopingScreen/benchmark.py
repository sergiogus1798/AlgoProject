"""What buy and hold earned beside each strategy, sized to the strategy's own risk."""

import numpy as np
import pandas as pd


def equal_risk(panel: pd.DataFrame, moves: pd.Series,
               point_value: float) -> tuple[pd.DataFrame, pd.Series]:
    """Each strategy's daily profit minus buy and hold's at the same daily volatility.

    Args:
        panel: Daily profit per strategy, account currency, as inputs.panel() returned it.
        moves: The asset's price change on the same days, as inputs.moves() returned it.
        point_value: Account currency per 1.0 of price and 1.0 of lot.

    Returns:
        The excess panel, and the lots of the asset each strategy is held against.

        The lots are the strategy's daily standard deviation over buy and hold's per lot,
        both over the same calendar with flat days included, as `studies/closing/exposure`
        sizes its `equal_risk` convention. With both sides equally volatile, a positive
        mean excess is exactly a Sharpe ratio above buy and hold's: the question is the
        edge, not how big a position either side held.
    """
    held = moves.iloc[1:] * point_value
    days = panel.loc[held.index]
    lots = days.std(ddof=1) / held.std(ddof=1)
    excess = days - np.outer(held.values, lots.values)
    return excess, lots
