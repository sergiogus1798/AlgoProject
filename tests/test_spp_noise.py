#!/usr/bin/env python3
"""Known-answer test: the SPP noise gate compares the CENTRED maximum (max - mean) with sigma*sqrt(2 ln N)."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.breakage.spp.verdict import noise


def grid(values: np.ndarray) -> pd.DataFrame:
    """One distinct backtest (NetProfit, NumberOfTrades) per tuple, metric `m`."""
    return pd.DataFrame({"NetProfit": np.arange(values.size, dtype=float),
                         "NumberOfTrades": 100, "m": values})


def test_pure_noise_with_a_positive_mean_reads_noise() -> None:
    """10,000 iid N(5, 1): max ~ 8.7 > 4.29 uncentred ('proceed'), excess ~ 3.7 < 4.29 ('noise')."""
    values = np.random.default_rng(0).normal(5.0, 1.0, 10_000)
    got = noise.noise_check(grid(values), "m")
    assert got["verdict"] == "noise", got


def test_a_real_ridge_proceeds() -> None:
    """The same grid plus 200 neighbours at +6 sigma clears the centred bar."""
    rng = np.random.default_rng(0)
    values = np.concatenate([rng.normal(5.0, 1.0, 9_800), rng.normal(11.0, 0.2, 200)])
    assert noise.noise_check(grid(values), "m")["verdict"] == "proceed"


if __name__ == "__main__":
    test_pure_noise_with_a_positive_mean_reads_noise()
    test_a_real_ridge_proceeds()
    print("ok")
