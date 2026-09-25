"""The cloud this study reads: the metric panel, the origin, and the per-day curves."""

from pathlib import Path

import numpy as np
import pandas as pd

TRADES = "# of trades (IS)"


def cloud(work: Path, cfg: dict) -> dict:
    """Contract C3 narrowed to the variants this study is allowed to describe.

    Args:
        work: The batch directory, holding `metrics.parquet` from `sqx.variants.collect`.
        cfg: The `run` block of config.yaml.

    Returns:
        `frame` one row per variant, `params` the parameter column names, `metric` the
        column every reading is taken on, and `origin` the variant id of theta-zero.

        The canaries are dropped: they were placed at the extremes of the grid on purpose
        to catch a broken chain, so leaving them in would make the surface look rougher
        and the origin's rank better than either is. **The origin itself is never dropped**,
        whatever it traded -- the whole study is about where it sits.
    """
    frame = pd.read_parquet(work / "metrics.parquet")
    params = sorted(c for c in frame.columns if c.startswith("param_"))
    keep = (~frame["stratum"].isin(cfg["exclude_strata"])
            & (frame[TRADES] >= cfg["min_trades"])) | frame["origin"]
    kept = frame[keep].reset_index(drop=True)
    return {"frame": kept, "params": params, "metric": cfg["metric"],
            "origin": kept.loc[kept["origin"], "variant_id"].iloc[0],
            "dropped": int(len(frame) - len(kept))}


def values(cloud_data: dict) -> np.ndarray:
    """The metric of every variant of the cloud, as a plain array.

    Args:
        cloud_data: What `cloud` returned.

    Returns:
        One float per row of `frame`, in its order.
    """
    return cloud_data["frame"][cloud_data["metric"]].to_numpy(dtype=float)


def curves(work: Path, ids: pd.Series) -> pd.DataFrame:
    """Every harvested variant's per-day P&L, narrowed to the cloud.

    Args:
        work: The batch directory, holding `equity.parquet` from `sqx.variants.equity`.
        ids: The variant ids the metric panel kept.

    Returns:
        Days down, `variant_id` across. Fewer columns than the panel has rows is normal
        and not a fault: a batch is fabricated larger than what comes back off the
        custodian, and only what came back has a curve.
    """
    daily = pd.read_parquet(work / "equity.parquet")
    return daily[[c for c in daily.columns if c in set(ids)]]


def before_reserved(daily: pd.DataFrame, symbol: str) -> dict:
    """The curves cut short of the segment the protocol reserves.

    Args:
        daily: What `curves` returned.
        symbol: The asset, to read its segments from `assets/_policy.yaml`.

    Returns:
        `curves` ending the day before `oos2` starts, and `cut` days removed.

        `oos2` is a one-way door: `_policy.yaml` reserves it for the walk-forward
        correlation and the walk-forward matrix, and every look spends it. A per-period
        heatmap over the whole history would spend it on a diagnostic, so this study
        stops at the boundary whether or not the batch was retested past it.
    """
    from core import assetdata

    start = str(assetdata.load(symbol)["segments"]["oos2"]["from"])
    limit = pd.Timestamp(start if "-" in start else f"{start}-01-01")
    kept = daily[daily.index < limit]
    return {"curves": kept, "cut": int(len(daily) - len(kept)), "limit": limit}
