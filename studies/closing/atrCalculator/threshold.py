"""§2.1 — the air the IS winners need: X per percentile, with its bootstrap interval."""

import numpy as np
import pandas as pd

CHUNK = 500          # resamples drawn at once: 500 x 5,000 winners x 8 bytes is 20 MB


def intervals(values: np.ndarray, percentiles: list[int], cfg: dict) -> np.ndarray:
    """Percentile bootstrap of several percentiles over the same resamples.

    Args:
        values: One MAE/ATR per winner; each resample draws that many with replacement.
        percentiles: The percentiles to bootstrap.
        cfg: The `bootstrap` section of the config.

    Returns:
        Shape (len(percentiles), 2): the low and high end of each interval. All four
        percentiles read the same draws, so their intervals are comparable. Vectorised in
        chunks: one np.percentile per resample cost 5 s a strategy (perf, 2026-09-26).
    """
    rng = np.random.default_rng(cfg["seed"])
    got = []
    for start in range(0, cfg["n"], CHUNK):
        draws = values[rng.integers(0, len(values), (min(CHUNK, cfg["n"] - start), len(values)))]
        got.append(np.percentile(draws, percentiles, axis=1))
    tail = (1 - cfg["confidence"]) / 2
    return np.quantile(np.concatenate(got, axis=1), [tail, 1 - tail], axis=1).T


def x_values(mae_winners: np.ndarray, cfg: dict) -> pd.DataFrame:
    """The X of each sub-study and how much another sample of winners would move it.

    Args:
        mae_winners: MAE in ATR of the in-sample winners, one per trade.
        cfg: The study's config.

    Returns:
        One row per percentile: `x` (numpy's linear interpolation between order statistics),
        the interval's `low` and `high`, `width` as a share of `x`, and `unreliable` when that
        width passes `bootstrap.wide`. The winners are resampled whole, one draw per trade.
    """
    ps = cfg["stop"]["percentiles"]
    xs = np.percentile(mae_winners, ps)
    bounds = intervals(mae_winners, ps, cfg["bootstrap"])
    width = (bounds[:, 1] - bounds[:, 0]) / xs
    return pd.DataFrame({"percentile": ps, "x": xs, "low": bounds[:, 0], "high": bounds[:, 1],
                         "width": width, "unreliable": width > cfg["bootstrap"]["wide"]})
