"""Encargo 66 review 3: a trailing period of size 0 is refused by q_null and permuted.between, not read out of bounds."""

import numpy as np
import pytest

from studies.screening.analysis import permuted, resample


def test_an_empty_period_raises() -> None:
    """The sizes add up to the trades, but the last period holds none."""
    values, sizes = np.arange(4.0), np.array([2, 2, 0])
    with pytest.raises(AssertionError):
        resample.q_null(values, sizes, 3, resample.stream(1, "x"))
    with pytest.raises(ValueError):
        permuted.between(
            values - values.mean(),
            np.cumsum(sizes) - sizes,
            sizes,
            3,
            resample.stream(1, "x"),
        )
