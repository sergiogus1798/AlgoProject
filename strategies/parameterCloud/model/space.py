"""The geometry of the cloud: the level grid each parameter lives on, and the unit cube."""

import numpy as np
import pandas as pd


def levels(frame: pd.DataFrame, params: list[str]) -> dict[str, np.ndarray]:
    """The distinct values each parameter takes across the cloud, in order.

    Args:
        frame: The metric panel.
        params: The parameter column names.

    Returns:
        One sorted array per parameter. These are the values that were actually
        fabricated, not a span: the design snapped them to what SQX can run.
    """
    return {p: np.sort(frame[p].unique()) for p in params}


def steps(frame: pd.DataFrame, params: list[str]) -> np.ndarray:
    """Every tuple written as level indices instead of values.

    Args:
        frame: The metric panel.
        params: The parameter column names.

    Returns:
        Rows by parameters, integer level index per cell. Distance in this space is the
        one the design was built in -- a level step -- so a neighbourhood measured here
        means the same thing for a bar count of 3 and a period of 67, which a percentage
        of the value does not.
    """
    grid = levels(frame, params)
    return np.column_stack([np.searchsorted(grid[p], frame[p].to_numpy()) for p in params])


def varying(frame: pd.DataFrame, params: list[str]) -> list[str]:
    """The parameters that still take more than one value in this cloud.

    Args:
        frame: The metric panel, already narrowed to what the study describes.
        params: The parameter column names.

    Returns:
        The subset the surrogate and the sensitivity indices may be fitted on.

        A parameter collapses when the study's own filters kill every tuple that moved
        it -- 🔬 `DICrossShift1` on `Strategy 17.9.39`, where everything but shift 1 trades
        under thirty times. That is a finding, not a fault: it says the parameter does not
        choose between good and bad, it chooses between trading and not. The collapsed
        ones are named in the report and left out of the fit, where they would divide by
        zero and, if they did not, would be handed an index of zero they did not earn.
    """
    return [p for p in params if frame[p].nunique() > 1]


def unit(frame: pd.DataFrame, params: list[str]) -> np.ndarray:
    """Every tuple rescaled onto [0, 1] per parameter.

    Args:
        frame: The metric panel.
        params: The parameter column names, from `varying`.

    Returns:
        Rows by parameters. A parameter that took one value only divides by zero here,
        which is why the caller passes `varying(...)` and not the full list.
    """
    raw = frame[params].to_numpy(dtype=float)
    lo, hi = raw.min(axis=0), raw.max(axis=0)
    return (raw - lo) / (hi - lo)
