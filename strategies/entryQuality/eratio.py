"""Item 3: does the entry itself predict favourable movement, or would any entry do?"""

import numpy as np
import pandas as pd

from strategies.entryQuality import excursion


def curve(walk: dict) -> np.ndarray:
    """e(k): mean favourable excursion over mean adverse excursion, horizon by horizon.

    Args:
        walk: What `excursion.normalised` returned.

    Returns:
        One ratio per horizon. Ratio of means, not mean of ratios, and deliberately: the
        second is dominated by the trades whose adverse excursion was near zero, which are
        the ones that say least. Above 1 the entry was followed by more upside than
        downside; at 1 it was not.
    """
    return walk["mfe"].mean(axis=0) / walk["mae"].mean(axis=0)


def eligible(index: pd.DatetimeIndex, entry: np.ndarray, horizon: int) -> np.ndarray:
    """The bars a random entry may be placed on.

    Args:
        index: The bars' open times.
        entry: Bar index of each real entry.
        horizon: The forward walk, so a placement near the end is excluded.

    Returns:
        Bar indices between the first and last real entry, which is the stretch the
        strategy was actually exposed to. Using the whole file would let random entries
        live in years the strategy never traded.
    """
    return np.arange(int(entry.min()), min(int(entry.max()) + 1, index.size - horizon))


def matched(index: pd.DatetimeIndex, pool: np.ndarray, entry: np.ndarray,
            rng: np.random.Generator) -> np.ndarray:
    """Random entry bars with the same time-of-day profile as the real ones.

    Args:
        index: The bars' open times.
        pool: What `eligible` returned.
        entry: Bar index of each real entry.
        rng: Seeded generator.

    Returns:
        As many bar indices as there are real trades, drawn hour by hour so that the
        random set enters at the same hours in the same proportions. Without that the
        benchmark is partly a statement about the session the strategy trades in, which is
        not what the entry signal is being credited with.
    """
    hours = index.hour.to_numpy()
    picks = []
    for hour, count in zip(*np.unique(hours[entry], return_counts=True)):
        same = pool[hours[pool] == hour]
        picks.append(rng.choice(same, size=count, replace=same.size < count))
    return np.concatenate(picks)


def band(frame: pd.DataFrame, found: dict, keep: np.ndarray, scale: np.ndarray,
         cfg: dict) -> dict:
    """The e-ratio curve of random entries matched to the real ones.

    Args:
        frame: The bars.
        found: What `inputs.located` returned.
        keep: The usable mask.
        scale: ATR per bar, the series every random entry is normalised by.
        cfg: The `eratio` block of config.yaml.

    Returns:
        The 5th, 50th and 95th percentile of e(k) over `draws` random sets. The real curve
        sitting inside this band means the entry rule bought nothing that entering at the
        same hours on random days would not have given.

        The long/short split is held fixed by shuffling the real sides, so the band carries
        the strategy's own directional bias and cannot be beaten by simply being long in a
        rising market.
    """
    entry, side = found["entry"][keep], found["side"][keep]
    pool = eligible(frame.index, entry, cfg["horizon"])
    rng = np.random.default_rng(cfg["seed"])
    opens = frame["Open"].to_numpy()
    drawn = []
    for _ in range(cfg["draws"]):
        picks = matched(frame.index, pool, entry, rng)
        walk = excursion.paths(frame, picks, rng.permutation(side), opens[picks],
                               cfg["horizon"])
        drawn.append(curve(excursion.normalised(walk, scale[picks - 1])))
    stacked = np.vstack(drawn)
    return {"low": np.quantile(stacked, 0.05, axis=0),
            "median": np.quantile(stacked, 0.5, axis=0),
            "high": np.quantile(stacked, 0.95, axis=0), "draws": cfg["draws"]}


def table(real: np.ndarray, bands: dict, marks: list[int]) -> pd.DataFrame:
    """The real curve against its band, at a few horizons.

    Args:
        real: What `curve` returned on the real trades.
        bands: What `band` returned.
        marks: Which horizons to print, in bars.

    Returns:
        One row per horizon: the real e(k), the band, and whether it sits above it.
    """
    rows = [{"k": k, "e(k)": real[k - 1], "p5": bands["low"][k - 1],
             "mediana": bands["median"][k - 1], "p95": bands["high"][k - 1],
             "sobre la banda": real[k - 1] > bands["high"][k - 1]} for k in marks]
    return pd.DataFrame(rows).set_index("k")
