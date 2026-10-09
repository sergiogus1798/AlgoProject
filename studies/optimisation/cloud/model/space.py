"""The geometry of the cloud: which parameters still vary, and the unit cube they span."""

import numpy as np
import pandas as pd


def varying(frame: pd.DataFrame, params: list[str]) -> list[str]:
    """The parameters that take more than one value in this cloud: its live ones.

    Args:
        frame: The cloud, controls already out.
        params: The parameter column names.

    Returns:
        The subset the surface is fitted on. The factory holds frozen parameters and shifts
        at the mother's value in every `lhs` row, so what varies here is a live parameter
        whose plateau is wider than one value; a live one the trade floor left with a single
        value drops out too, and the report names it.
    """
    return [p for p in params if frame[p].nunique() > 1]


def unit(frame: pd.DataFrame, params: list[str]) -> np.ndarray:
    """Every tuple rescaled onto [0, 1] per parameter.

    Args:
        frame: The cloud.
        params: From `varying`: a parameter with one value would divide by zero.

    Returns:
        Rows by parameters.
    """
    raw = frame[params].to_numpy(dtype=float)
    lo, hi = raw.min(axis=0), raw.max(axis=0)
    return (raw - lo) / (hi - lo)
